from pymodbus.client.sync import ModbusSerialClient
import time

PORT     = '/dev/rs485'
SLAVE_ID = 1

client = ModbusSerialClient(
    method='rtu',
    port=PORT,
    baudrate=115200,
    parity='N',
    stopbits=2,
    bytesize=8,
    timeout=1
)

def to_u16(value):
    return value & 0xFFFF if value < 0 else value

try:
    print("Connecting...")
    client.connect()
    print("Connected.\n")

    # Speed source = digit value (P05.03)
    client.write_register(address=1280, value=0, unit=SLAVE_ID)

    # Force DI enable + assert S-ON
    client.write_register(address=2826, value=1, unit=SLAVE_ID)
    client.write_register(address=2827, value=1, unit=SLAVE_ID)
    time.sleep(0.5)

    # +100 RPM for 5s
    print("Running +100 RPM...")
    client.write_register(address=1283, value=to_u16(100), unit=SLAVE_ID)
    time.sleep(5)

    # -100 RPM for 5s
    print("Running -100 RPM...")
    client.write_register(address=1283, value=to_u16(-100), unit=SLAVE_ID)
    time.sleep(5)

    # Ramp to zero
    print("Stopping...")
    client.write_register(address=1283, value=0, unit=SLAVE_ID)
    time.sleep(1)

    # De-assert S-ON
    client.write_register(address=2827, value=0, unit=SLAVE_ID)
    print("Servo disabled.")

except Exception as e:
    print(f"Error: {e}")

finally:
    client.close()
    print("Disconnected.")