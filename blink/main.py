from machine import Pin,PWM
import utime

led = None
button = None
reset_led = None
max_brightness = 65536
current_brightness = 0
ON = 1
OFF = 0
led_pin = 15
reset_led_pin = 13
last_time = 0
frequency = 1000

def setup():
    global led,button,reset_led
    led = PWM(Pin(led_pin,Pin.OUT),freq=frequency,duty_u16=0)
    reset_led = Pin(reset_led_pin,Pin.OUT)
    reset_led.value(OFF)
    print("initialize led")
    reset_led.value(ON)
    utime.sleep(1)
    print("initialize reset button")
    reset_led.value(OFF)
    utime.sleep(1)

def loop():
    global last_time,current_brightness
    while True:
        if led is not None:
           current_time = utime.time()
           interval = int(max_brightness / 2000)
           if current_time - last_time >= 2:
               if current_brightness < max_brightness:
                   led.duty_u16(current_brightness)
                   current_brightness+=interval
                   current_brightness = max(0,min(current_brightness,max_brightness))
               if current_time - last_time >= 3:
                   last_time = current_time
           else:
               if current_brightness >= 0:
                   led.duty_u16(current_brightness)
                   current_brightness -= interval
                   current_brightness = max(0,min(current_brightness,max_brightness))              

def main():
    setup()
    loop()

main()

