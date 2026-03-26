from machine import Pin,I2C,ADC
from ds1302 import DS1302
from lcd_api import LcdApi
from i2c_lcd import I2cLcd
import utime

# define variables related to LCD I2C
I2C_ADDR = 0x27
ROW_NUMBER = 2
COLUMN_NUMBER = 16
i2c:I2C
lcd:I2cLcd
#init RTC
rtc:DS1302
#init LM35
lm35:ADC

interval = 1 # second
last_time = 0
last_temp_time = 0

def show_data_on_lcd(date:str,time:str,temp:str):
    lcd.move_to(0,0)
    lcd.putstr(f"D:{date}")
    lcd.move_to(0,1)
    lcd.putstr(f"T:{time}")
    lcd.move_to(12,1)
    lcd.putstr(temp)

def read_temperature()->str:
    samples = []
    for _ in range(30):
        samples.append(lm35.read_u16())
        utime.sleep_ms(1)
    samples.sort()
    smooth_adc = sum(samples[5:-5]) / 20
    voltage = (smooth_adc * 3.3) / 65535
    temp_c = voltage * 100
    return "{:04.1f}".format(temp_c)


def setup():
    # init lcd
    global i2c,lcd,rtc,lm35
    i2c = I2C(0,sda=Pin(0),scl=Pin(1),freq=40000)
    lcd = I2cLcd(i2c, I2C_ADDR, ROW_NUMBER, COLUMN_NUMBER)
    lcd.clear()
    utime.sleep(1)
    #init rtc
    rtc = DS1302(clk=Pin(2),dio=Pin(3),cs=Pin(4))
    rtc.start()
    #get current time
    current_time = rtc.date_time()
    if current_time is None or current_time[0] != 2026:
        rtc.date_time([2026, 3, 9, 5, 11, 2, 0])
    #init LM35 temperature
    lm35 = ADC(27) 

def loop():
    global last_time,last_temp_time
    while True:
       now = utime.time()
       if now - last_time >= 0.5:
           last_time = now
           #get current time from RTC
           current_time_list =  rtc.date_time()
           if current_time_list is not None:
               Yc, Mo, Dc, Wc, Hc, Mi, Sc = current_time_list[:7]
               current_time = "{:02d}:{:02d}:{:02d}".format(Hc,Mi,Sc)
               current_date = "{:04d}-{:02d}-{:02d}".format(Yc,Mo,Dc)
               # get temperature
               temp =  read_temperature()
               show_data_on_lcd(date=current_date,time=current_time,temp=temp)



def main():
    setup()
    loop()

main()