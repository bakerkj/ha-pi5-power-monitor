# Copyright (c) 2026 Kenneth Baker <bakerkj@umich.edu>
# All rights reserved.

"""Poll vcgencmd pmic_read_adc and expose per-rail readings."""

from __future__ import annotations

import asyncio
import contextlib
import logging
import re
from dataclasses import dataclass, field
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    RAILS_V_AND_A,
    RAILS_V_ONLY,
    VCGENCMD_BINARY,
    VCGENCMD_SUBCOMMAND,
)

_LOGGER = logging.getLogger(__name__)

# Matches one line like ``3V3_SYS_A current(1)=0.12589500A``. The channel
# index between parentheses is a PMIC-internal mux slot and is discarded.
_LINE_RE = re.compile(
    r"^\s*(?P<rail>[A-Z0-9_]+)_(?P<kind>[AV])\s+"
    r"(?:current|volt)\(\d+\)=(?P<value>-?\d+(?:\.\d+)?)[AV]\s*$"
)


@dataclass(frozen=True, slots=True)
class RailReading:
    voltage: float | None
    current: float | None
    power: float | None


@dataclass(frozen=True, slots=True)
class PmicData:
    rails: dict[str, RailReading] = field(default_factory=dict)
    total_power: float | None = None


def _parse(output: str) -> PmicData:
    volts: dict[str, float] = {}
    amps: dict[str, float] = {}
    for raw in output.splitlines():
        m = _LINE_RE.match(raw)
        if not m:
            continue
        rail = m.group("rail")
        value = float(m.group("value"))
        if m.group("kind") == "V":
            volts[rail] = value
        else:
            amps[rail] = value

    rails: dict[str, RailReading] = {}
    total = 0.0
    contributing = 0
    for rail in RAILS_V_AND_A:
        v = volts.get(rail)
        a = amps.get(rail)
        p: float | None
        if v is not None and a is not None:
            p = v * a
            total += p
            contributing += 1
        else:
            p = None
        rails[rail] = RailReading(voltage=v, current=a, power=p)
    for rail in RAILS_V_ONLY:
        v = volts.get(rail)
        rails[rail] = RailReading(voltage=v, current=None, power=None)

    # Distinguishes "every rail is quiescent at 0 W" (unlikely in practice but
    # mathematically possible) from "the parser recognized nothing", which
    # would otherwise show a plausible 0 W in energy dashboards.
    return PmicData(rails=rails, total_power=total if contributing else None)


class Pi5PowerMonitorCoordinator(DataUpdateCoordinator[PmicData]):
    def __init__(self, hass: HomeAssistant, scan_interval: int) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(
                seconds=max(5, scan_interval or DEFAULT_SCAN_INTERVAL)
            ),
        )

    async def _async_update_data(self) -> PmicData:
        try:
            proc = await asyncio.create_subprocess_exec(
                VCGENCMD_BINARY,
                VCGENCMD_SUBCOMMAND,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
        except OSError as err:
            raise UpdateFailed(f"spawning {VCGENCMD_BINARY} failed: {err}") from err

        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=5)
        except TimeoutError as err:
            # wait_for cancels communicate() but leaves the subprocess alive;
            # without this reap, every timeout stacks another vcgencmd process.
            proc.kill()
            with contextlib.suppress(Exception):
                await proc.wait()
            raise UpdateFailed("vcgencmd timed out") from err

        if proc.returncode != 0:
            raise UpdateFailed(
                f"vcgencmd exited {proc.returncode}: {stderr.decode(errors='replace').strip()}"
            )
        return _parse(stdout.decode(errors="replace"))
