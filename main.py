import network
import socket
import time

from machine import I2C, Pin, Timer
import ads1x15
from time import sleep_ms, ticks_ms, ticks_us
from array import array

addr = 0x48
gain = 5
_BUFFERSIZE = const(512)

data = array("h", (0 for _ in range(_BUFFERSIZE)))
timestamp = array("L", (0 for _ in range(_BUFFERSIZE)))
i2c = I2C(0, scl=Pin(5), sda=Pin(4), freq=400000)
# for the Pycom branch, use:
# i2c = I2C()
ads = ads1x15.ADS1115(i2c, addr, gain)

ads.set_conv(7, 0, 1) # start the first conversion

led = Pin(15, Pin.OUT)

ssid = 'WIFI_USER'
password = 'WIFI_PWD'

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(ssid, password)

# 192.168.1.47 and 192.168.1.1 are sample IP and gateway
wlan.ifconfig(('192.168.1.48', '255.255.255.0', '192.168.1.1', '8.8.8.8'))

max_wait = 10
while max_wait > 0:
    print(wlan.status())
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

addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]

s = socket.socket()
s.bind(addr)
s.listen(1)

print('listening on', addr)

# Listen for connections
while True:
    try:
        cl, addr = s.accept()
        print('client connected from', addr)
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
