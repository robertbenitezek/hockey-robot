"""
DSY-RS Series Servo - Modbus RTU control script
Spins at +100 RPM for 5s, then -100 RPM for 5s, then disables and disconnects.

Modbus address formula: group * 256 + parameter_number
  P00.00 = 0*256+0   = 0     (control mode: 1=speed)
  P05.00 = 5*256+0   = 1280  (speed command source: 0=digit value / comms register)
  P05.03 = 5*256+3   = 1283  (speed setpoint, signed RPM)
  P11.10 = 11*256+10 = 2826  (forced DI enable: 1=force DI, 2=force DO, 3=both)
  P11.11 = 11*256+11 = 2827  (forced DI value: bit0=FunIN.1=S-ON)
"""

import time
from pymodbus.client import ModbusSerialClient

# ── Config ────────────────────────────────────────────────────────────────────
PORT      = '/dev/rs485'   # Linux: /dev/ttyUSB0 etc. | Windows: 'COM3' etc.
SLAVE_ID  = 1              # Must match P10.00 on the drive (default = 1)
BAUD      = 115200         # Must match P10.02 on the drive (default 6 = 115200)
# P10.03 default = 0 → no parity, 2 stop bits — reflected below
PARITY    = 'N'
STOPBITS  = 2
BYTESIZE  = 8
TIMEOUT   = 1              # seconds

# ── Register addresses ────────────────────────────────────────────────────────
REG_CONTROL_MODE    = 0     # P00.00 — 1 = speed mode (needs power cycle after change)
REG_SPEED_SRC       = 1280  # P05.00 — 0 = digit value (P05.03 is the setpoint)
REG_SPEED_SETPOINT  = 1283  # P05.03 — signed RPM (-9000 to +9000)
REG_FORCE_DI_ENABLE = 2826  # P11.10 — 1 = force DI inputs via software
REG_FORCE_DI_VALUE  = 2827  # P11.11 — bit 0 = FunIN.1 = S-ON (servo enable)

# ── Helpers ───────────────────────────────────────────────────────────────────

def to_u16(value: int) -> int:
    """Convert a signed int to unsigned 16-bit two's complement for Modbus."""
    if value < 0:
        return value & 0xFFFF
    return value


def write(client, address: int, value: int, label: str = "") -> bool:
    """Write a single register; print result; return True on success."""
    result = client.write_register(address=address, value=value, slave=SLAVE_ID)
    if result.isError():
        print(f"  ERROR writing {label or address}: {result}")
        return False
    print(f"  Wrote {label or f'reg[{address}]'} = {value} (0x{value:04X})")
    return True


def read(client, address: int, label: str = "") -> int | None:
    """Read a single register and return its value, or None on error."""
    result = client.read_holding_registers(address=address, count=1, slave=SLAVE_ID)
    if result.isError():
        print(f"  ERROR reading {label or address}: {result}")
        return None
    val = result.registers[0]
    print(f"  Read  {label or f'reg[{address}]'} = {val} (0x{val:04X})")
    return val


# ── Main ──────────────────────────────────────────────────────────────────────

client = ModbusSerialClient(
    port=PORT,
    baudrate=BAUD,
    parity=PARITY,
    stopbits=STOPBITS,
    bytesize=BYTESIZE,
    timeout=TIMEOUT,
)

try:
    # ── Connect ───────────────────────────────────────────────────────────────
    print("Connecting to servo drive...")
    if not client.connect():
        raise RuntimeError(f"Could not open {PORT}")
    print("Connected.\n")

    # ── Verify control mode ───────────────────────────────────────────────────
    # P00.00 must already be 1 (speed mode). Changing it requires a power cycle,
    # so we read it first and warn rather than blindly writing.
    print("── Checking control mode ──")
    mode = read(client, REG_CONTROL_MODE, "P00.00 control mode")
    if mode != 1:
        print(f"  WARNING: P00.00 = {mode}, expected 1 (speed mode).")
        print("  Writing 1 now — you must power-cycle the drive before this takes effect.")
        write(client, REG_CONTROL_MODE, 1, "P00.00 control mode")
        raise RuntimeError("Power-cycle the drive to activate speed mode, then re-run.")
    print("  Control mode confirmed: speed mode (1) ✓\n")

    # ── Set speed command source to comms register (P05.03) ───────────────────
    print("── Setting speed command source ──")
    write(client, REG_SPEED_SRC, 0, "P05.00 speed cmd source")
    print()

    # ── Enable servo via forced DI (software S-ON) ────────────────────────────
    print("── Enabling servo (software S-ON) ──")
    write(client, REG_FORCE_DI_ENABLE, 1, "P11.10 force DI enable")
    write(client, REG_FORCE_DI_VALUE,  1, "P11.11 force DI value (S-ON=bit0)")
    time.sleep(0.5)   # give the drive a moment to enable
    print()

    # ── Run +100 RPM for 5 seconds ────────────────────────────────────────────
    print("── Running at +100 RPM ──")
    write(client, REG_SPEED_SETPOINT, to_u16(100), "P05.03 speed setpoint (+100 RPM)")
    time.sleep(5)
    print()

    # ── Run -100 RPM for 5 seconds ────────────────────────────────────────────
    print("── Running at -100 RPM ──")
    write(client, REG_SPEED_SETPOINT, to_u16(-100), "P05.03 speed setpoint (-100 RPM)")
    time.sleep(5)
    print()

    # ── Ramp to zero before disabling ─────────────────────────────────────────
    print("── Ramping to 0 RPM ──")
    write(client, REG_SPEED_SETPOINT, 0, "P05.03 speed setpoint (0 RPM)")
    time.sleep(1)
    print()

    # ── Disable servo (de-assert S-ON) ───────────────────────────────────────
    print("── Disabling servo (de-assert S-ON) ──")
    write(client, REG_FORCE_DI_VALUE, 0, "P11.11 force DI value (S-ON=0)")
    print("  Servo disabled.")

except Exception as e:
    print(f"\nException: {e}")

finally:
    print("\nDisconnecting...")
    client.close()
    print("Done.")