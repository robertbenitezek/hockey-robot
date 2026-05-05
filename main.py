from pymodbus.client import ModbusSerialClient
import serial

client = ModbusSerialClient(
    port='/dev/rs485',  # COM port for Windows or /dev/ttyUSBX for Linux
    baudrate=115200,        # Communication speed
    parity='N',           # N=None, E=Even, O=Odd
    stopbits=1,           # Number of stop bits
    bytesize=8,           # Number of data bits
    timeout=1             # Seconds to wait for a response
)

#parameters from datasheet are tbd
