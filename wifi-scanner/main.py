import network
import time
from microdot import Microdot,Response
from microdot.websocket import with_websocket,WebSocket
from machine import ADC
import uasyncio

wifi_list = []
waln = None
app = Microdot()
temp : ADC = None


def wifi_scan():
    global wifi_list,waln
    waln = network.WLAN(network.STA_IF)
    waln.active(True)
    print("scanning wifi....")
    raw = waln.scan()
    for i, wifi in enumerate(raw):
        wifi_name = bytes(wifi[0])
        print(f"{i+1}. {wifi_name.decode('utf-8')}")
        wifi_list.append(wifi_name.decode('utf-8'))

def wifi_connect():
    option = int(input("choose a Wifi: "))
    ssid = wifi_list[option - 1]
    password = input("password: ")
    if waln is not None:
       retry_time = 10
       waln.connect(ssid,password)
       while retry_time > 0:
           if not waln.isconnected():
               time.sleep(1)
               retry_time -= 1
               print(".",end="")
           else:
               print(f"Connected!! IP:{waln.ifconfig()[0]}")
               break

def get_temperature()->float:
    raw = temp.read_u16() * 3.3 / 65535
    result = 27 - (raw - 0.706) / 0.001721
    return round(result,2)


@app.route("/ws_pico")
@with_websocket
async def websocket(request,ws:WebSocket):
    print(">>> WebSocket Handler Started!")
    try:
        while True:
            current_pico_temp = get_temperature()
            print(f"current temp: {current_pico_temp}")
            await ws.send(str(current_pico_temp))
            await uasyncio.sleep(1)
    except Exception as e:
        print(e)
      
       
def setup():
    global temp
    wifi_scan()
    wifi_connect()
    temp = ADC(4)

if __name__ == "__main__":
    setup()
    app.run(port=8080,debug=True)

