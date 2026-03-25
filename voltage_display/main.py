from machine import Pin,ADC
import utime

pin_adc = 26
ON = 1
OFF = 0
adc = None
last_time = 0
voltage = 0.00

R1 = 10000
R2 = 1000

RATIO = (R1 + R2) / R2

seg_pins = [0,1,2,3,4,5,6,7] # a-g,dot
segs = []
digit_pins = [8,9,10,11]
digits = []

display_show = {'0':0b11111100,'1':0b01100000,'2':0b11011010,'3':0b11110010,'4':0b01100110,'5':0b10110110,
                '6':0b10111110,'7':0b11100000,'8':0b11111110,'9':0b11110110}

def setup():
    global adc,segs,digits
    adcadc = ADC(Pin(pin_adc))
    for seg_pin in seg_pins:
        pin = Pin(seg_pin,Pin.OUT)
        pin.value(OFF)
        segs.append(pin)
    for digit in digit_pins:
        pin = Pin(digit,Pin.OUT)
        pin.value(OFF)
        digits.append(pin)
    utime.sleep(2)    

def loop():
    while True:
       #read current outside voltage value
       current_voltage = float(read_voltage_value())
       # show current voltage value in 4 digital 7 segment display
       show_on_display(current_voltage)



def read_voltage_value() -> float:
    global last_time,voltage
    if adc is not None:
        current_time = utime.ticks_ms()
        if utime.ticks_diff(current_time,last_time) >= 1000:
            value = adc.read_u16()
            voltage = round(value * 3.3 / 65535 * RATIO ,2)
            last_time = current_time
    return voltage

def show_on_display(value:float):
    # numbe converts to string
    value_str = "{:05.2f}".format(value)
    number_list = []
    dot = False
    for symbol in value_str:
        if symbol != '.':
            number_list.append(symbol)
        else:
            dot = True
    for index,number in enumerate(number_list):
        code = display_show[number]
        if index == 1 and dot:
            code |= 0b00000001
        show_one_digit_on_display(index=index,code=code)    

def show_one_digit_on_display(index:int, code:int):

    for i in range(8):
        if code & (0b10000000 >> i):
            segs[i].value(ON)
        else:
            segs[i].value(OFF)    
    digits[index].value(ON)
    utime.sleep_ms(5)
    digits[index].value(OFF)    


def main():
    setup()
    loop()

main()
