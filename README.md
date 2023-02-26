# Vibration Sensor
## Explaining the Code
A driver is needed to establish a connection between the analog to digital convert (ADC) and the Raspberry Pico. We will  be using the [Driver for the ADS1015/ADS1115 Analogue-Digital Converter](https://github.com/robert-hh/ads1x15), and incorporating the given [sample code](https://github.com/robert-hh/ads1x15#sample-code):
```python
from machine import I2C, Pin, Timer
import ads1x15 # importing the driver library
from array import array

# Sample code:
addr = 0x48 # 72 in hexadecimal
gain = 5
_BUFFERSIZE = const(512)

data = array("h", (0 for _ in range(_BUFFERSIZE)))
timestamp = array("L", (0 for _ in range(_BUFFERSIZE)))
i2c = I2C(0, scl=Pin(5), sda=Pin(4), freq=400000)
# for the Pycom branch, use:
# i2c = I2C()
ads = ads1x15.ADS1115(i2c, addr, gain)
ads.set_conv(7, 0, 1) # start the first conversion
```

Next, we use the [WLAN class](https://docs.micropython.org/en/latest/library/network.WLAN.html) from the `network` library to establish the Pico's connection to the wifi network so that we can get the vibration value through the http server:

```python
import network
import time
from time import sleep_ms, ticks_ms, ticks_us

ssid = 'WIFI_USER'
password = 'WIFI_PWD'

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(ssid, password)

# 192.168.1.48 and 192.168.1.1 are sample IP and gateway
wlan.ifconfig(('192.168.1.48', '255.255.255.0', '192.168.1.1', '8.8.8.8'))

# Waiting for a connection for a  maximum of 10 seconds.
max_wait = 10
while max_wait > 0:
	# wlan.status() returns constants, which store integer values
    if wlan.status() < 0 or wlan.status() >= 3:
        break
    max_wait -= 1
    print('waiting for connection...')
    time.sleep(1)

if wlan.status() != 3:
    raise RuntimeError('network connection failed')
else:
    print('connected')
    status = wlan.ifconfig()
    print( 'ip = ' + status[0] )
```

Next, we will create a [socket](https://docs.python.org/3/library/socket.html) in order to send the value to `192.168.1.48`:

```python
import socket

addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]

s = socket.socket()
s.bind(addr)
s.listen(1)
```

Next, the Pico will listen for connections, which are any HTTP requests with its IP address, http://192.168.1.48/. Once [http://192.168.1.48/](http://192.168.1.48/) is accessed, it will notify that a connection is made. The HTTP request provides a JSON giving the vibration value collected through ads1x15 in the key `"value"`.

```python
print('listening on', addr)

# Listen for connections
while True:
    try:
        cl, addr = s.accept()
        print('client connected from', addr) # Notifies connection
        request = cl.recv(1024)
        request = str(request)
        try:
            request = request.split()[1]
        except IndexError:
            pass
        
        value = ads.read_rev()
        
        str_value = '{"value": "' + str(value) + '"}'
        
        cl.send('HTTP/1.0 200 OK\r\nContent-type: text/json\r\nContent-Length: ' + str(len(str_value)+2) + '\r\n\r\n')
        cl.send(str_value + '\r\n')
        print('Done value', value)
        cl.close()

    except OSError as e:
        cl.close()
        print('connection closed')
```
## Additional Material
Hardware setup information can be found on Instructable here.
