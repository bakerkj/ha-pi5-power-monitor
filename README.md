# ha-pi5-power-monitor

Home Assistant custom integration that exposes the Raspberry Pi 5's power
management IC (DA9091) per-rail readings as HA sensors.

## What it reports

- Per-rail voltage, current, and derived power for each of the 12
  current-carrying PMIC rails (`VDD_CORE`, `3V3_SYS`, `1V8_SYS`, `1V1_SYS`,
  `0V8_SW`, `0V8_AON`, `3V3_DAC`, `3V3_ADC`, `3V7_WL_SW`, `DDR_VDD2`,
  `DDR_VDDQ`, `HDMI`)
- Voltage-only readings for `EXT5V` and `BATT`
- **Chip-side power** — the sum of V × I across every rail, i.e. what the Pi 5
  SoC package draws through the PMIC. This is a direct measurement.
- **Input power (estimated)** — chip-side divided by a configurable PMIC
  efficiency (default 0.80). This estimates the 5V-rail draw at the Pi's input,
  modulo the caveats below.

Only the aggregate sensors and `VDD_CORE` are enabled by default; everything
else is `enabled_default=false` to keep the entity list manageable. Enable
individual rails from the device page as needed.

## Requirements

- Raspberry Pi 5 running Home Assistant OS. The firmware mailbox device
  (`/dev/vcio`) and the `vcgencmd` binary are already present inside the HA
  container on HAOS — no extra add-on, device mounts, or shell plumbing
  required.
- Home Assistant 2026.9 or newer.

## Install

Add this repository to HACS as a custom integration repository, install
**Raspberry Pi 5 Power Monitor**, restart Home Assistant, then add the
integration from Settings → Devices & Services. The flow is zero-input: there is
one Pi, one PMIC, one entry.

## Options

- **Poll interval** (seconds, 5-600, default 30). Each poll shells out to
  `vcgencmd pmic_read_adc` once and refreshes every sensor from that single
  call.
- **PMIC efficiency** (0.50 - 1.00, default 0.80). Only affects the "Input power
  (estimated)" sensor.

## About the estimated input power

The DA9091 datasheet is NDA-only, there is no vendor-published efficiency curve,
and the chip's per-rail buck efficiency varies with load. The default of 0.80 is
a reasonable midpoint for Pi 5 light-to-moderate loads based on comparable
multi-rail buck PMICs; adjust per deployment if you can calibrate against a real
wall-side measurement.

**The estimate accounts ONLY for PMIC conversion loss.** It does NOT account
for:

- USB peripherals (RTL-SDR dongles, SSDs, etc.) — draw straight from the Pi's 5V
  rail outside the PMIC path
- The 5V rail to the GPIO header, status LEDs, fan, PCIe/NVMe link idle current
- PoE+ HAT inefficiency on PoE-powered Pis
- Any non-PMIC consumer

On a bare USB-C-powered Pi 5 with no peripherals the estimate is close to true
wall-side draw. On a Pi 5 with a PoE+ HAT and attached peripherals, real
wall-side draw can be 2-3× the estimate; measure your wall-side watts externally
if that matters.

## License

MIT — see [LICENSE](LICENSE).
