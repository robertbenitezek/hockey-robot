from pymodbus.client.sync import ModbusSerialClient
import serial

client = ModbusSerialClient(
    method='rtu',
    port='/dev/rs485',  # COM port for Windows or /dev/ttyUSBX for Linux
    baudrate=115200,        # Communication speed
    parity='N',           # N=None, E=Even, O=Odd
    stopbits=2,           # Number of stop bits
    bytesize=8,           # Number of data bits
    timeout=1             # Seconds to wait for a response
)

try:
	print("Connecting to servo drive...")
	client.connect()
	print("connected to servo drive")
	
	# Switch to speed control mode
	client.write_register(address=0, value=1, unit=1)

	#set speed source to rs485
	client.write_register(address=1280, value=5, unit=1)

	r1=client.read_holding_registers(address=0, count=1, unit=1)
	r2=client.read_holding_registers(address=1280, count=1, unit=1)

	print(f"P00.00: {r1.registers[0]}")
	print(f"P05.00: {r2.registers[0]}")

finally:
	print("disconnecting from servo drive...")
	client.close()
	print("disconnected from servo driver")
