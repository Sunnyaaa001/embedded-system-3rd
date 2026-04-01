import network
import time
from microdot import Microdot,Request
from microdot.websocket import with_websocket,WebSocket
from machine import Pin,PWM
import uasyncio
import ubinascii
import ujson

wifi_list = []
waln = None
app = Microdot()
red:PWM = None
green:PWM = None
blue:PWM = None
red_int = 0
blue_int = 0
red_int = 0

color_reset_button = None

def setup():
    global temp,red,green,blue,color_reset_button
    wifi_scan()
    wifi_connect()
    red = PWM(Pin(21))
    green = PWM(Pin(20))
    blue = PWM(Pin(19))
    red.freq(1000)
    green.freq(1000)
    blue.freq(1000)
    color_reset_button = Pin(13,Pin.PULL_UP)


def loop():
    global red_int,green_int,blue_int
    while True:
        if color_reset_button is not None:
            value = color_reset_button.value()
            if value == 0:
                selectColor(0,0,0)
                red_int = 0
                green_int = 0
                blue_int = 0


def wifi_scan():
    global wifi_list,waln
    waln = network.WLAN(network.STA_IF)
    waln.active(True)
    print("scanning wifi....")
    raw = waln.scan()
    for i, wifi in enumerate(raw):
        wifi_name = bytes(wifi[0])
        wifi_mac = ubinascii.hexlify(wifi[1], ':').decode()
        print(f"{i+1}. {wifi_name.decode('utf-8')}      MAC:[{wifi_mac.upper()}]", end= "\n")
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

def selectColor(r:int,g:int,b:int):
    if red is not None and green is not None and blue is not None:
        red.duty_u16(r * 257)
        green.duty_u16(g * 257)
        blue.duty_u16(b * 257)

@app.route("/ws_pico")
@with_websocket
async def websocket(request,ws:WebSocket):
    print(">>> WebSocket Handler Started!")
    try:
        while True:
            rgb_color = {
                "red":red_int,
                "green":green_int,
                "blue":blue_int
            }
            await ws.send(ujson.dumps(rgb_color))
            await uasyncio.sleep(1)
    except Exception as e:
        print(e)

@app.get("/led/control")
async def led_control(request:Request):
    global red_int,blue_int,green_int
    red_str = str(request.args.get("red", "0"))
    red_int = int(red_str)
    green_str = str(request.args.get("green","0"))
    green_int = int(green_str)
    blue_str = str(request.args.get("blue","0"))
    blue_int = int(blue_str)
    return {"code":200}
   

if __name__ == "__main__":
    setup()
    uasyncio.create_task(loop())
    app.run(port=8080,debug=True)

