import network
import uasyncio as asyncio
from machine import Pin, ADC
from usocket import socket
import ujson

# Set up Wi-Fi connection
wifi_ssid = "your_wifi_ssid"
wifi_password = "your_wifi_password"

sta_if = network.WLAN(network.STA_IF)
sta_if.active(True)
sta_if.connect(wifi_ssid, wifi_password)

while not sta_if.isconnected():
    pass

# Create an ADC object for the LM35 sensor (use the correct pin)
temperature_sensor = ADC(Pin(34))  # Use the correct pin for your setup

# Define a function to read temperature from the LM35 sensor
def read_temperature():
    # Read the analog value (0-4095) from the LM35
    raw_value = temperature_sensor.read()
    # Convert the raw value to temperature in degrees Celsius
    temperature = (raw_value / 4095) * 330  # LM35 has a sensitivity of 10 mV/°C
    return temperature

# Define an HTTP request handler function
def handle_request(reader, writer):
    response = {
        "temperature": read_temperature(),
    }
    
    writer.write("HTTP/1.1 200 OK\r\n")
    writer.write("Content-Type: application/json\r\n")
    writer.write("\r\n")
    writer.write(ujson.dumps(response))
    await writer.drain()
    writer.close()

# Create an asyncio event loop
loop = asyncio.get_event_loop()

# Define a function to periodically read and respond with temperature data
async def read_and_respond():
    while True:
        response = {
            "temperature": read_temperature(),
        }
        
        writer, _ = await asyncio.open_connection("0.0.0.0", 8080)
        
        writer.write("HTTP/1.1 200 OK\r\n")
        writer.write("Content-Type: application/json\r\n")
        writer.write("\r\n")
        writer.write(ujson.dumps(response))
        await writer.drain()
        writer.close()
        
        await asyncio.sleep(30)  # Wait for 30 seconds

# Create an HTTP server
server = loop.create_server(lambda r, w: asyncio.start_server(handle_request(r, w), r, w), "0.0.0.0", 8080)

# Start the server
loop.create_task(server)

# Schedule the periodic read and respond task
loop.create_task(read_and_respond())

# Run the event loop
try:
    loop.run_forever()
except KeyboardInterrupt:
    pass
finally:
    loop.close()
