import usb_hid
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keycode import Keycode
import time
import analogio
import board

keybd:Keyboard = None
LDR:analogio.AnalogIn = None

vry:analogio.AnalogIn = None
mode = 0 


THRESHOLD = 42300
CENTER_VALUE = 50400

def mode_choose()->int:
    print("1. automation")
    print("2. joystick")
    return int(input("choose the mode: "))

def get_ldr_value():
    total = 0
    for _ in range(10):
        total += LDR.value
    return total // 10

def setup():
    global keybd,LDR,mode,vry
    keybd = Keyboard(usb_hid.devices)
    mode = mode_choose()
    if mode == 1:
      LDR = analogio.AnalogIn(board.GP26)
    elif mode == 2:
      vry = analogio.AnalogIn(board.GP27)  

def loop():
    while True:
        if mode == 1:
            auto()
        elif mode == 2:
            joystick()


def auto():
    global last_time
    if keybd is not None and LDR is not None:
        current_value =  get_ldr_value()
        if current_value < THRESHOLD:
            keybd.press(Keycode.SPACE)
        else:
            keybd.release_all()
                

def joystick():
    value =  vry.value
    if (CENTER_VALUE - 500) <= value <= (CENTER_VALUE + 500):
        keybd.release_all()
        pass
    elif value <= 20000:
        keybd.press(Keycode.SPACE)
    elif value >=60000:
        keybd.press(Keycode.DOWN_ARROW)
    


def main():
    setup()
    loop()

main()