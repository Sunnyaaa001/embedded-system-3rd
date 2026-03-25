from machine import ADC,Pin,PWM,I2C,SPI
from ds1302 import DS1302
from lcd_api import LcdApi
from i2c_lcd import I2cLcd
import time
import network
import ntptime
from mfrc522 import MFRC522
import urequests

# define variables related to LCD I2C
I2C_ADDR = 0x27
ROW_NUMBER = 2
COLUMN_NUMBER = 16
i2c:I2C
lcd:I2cLcd
#init RTC
rtc:DS1302
last_time = 0

wifi_list = []
waln = None
buzzer = None

TIME_HOST = "0.nl.pool.ntp.org"
UTC_OFFSET = 1 * 3600

spi = None
MISO = 12
MOSI = 11
SCK = 10
SDA = 13
RST = 15

red = None
green = None
blue = None

card_scanner = None

SERVER_HOST = "http://192.168.1.222:8080"

def setup():
    global i2c,lcd,rtc,spi,card_scanner,buzzer,red,green,blue
    wifi_scan()
    wifi_connect()
    i2c = I2C(0,sda=Pin(0),scl=Pin(1),freq=40000)
    lcd = I2cLcd(i2c, I2C_ADDR, ROW_NUMBER, COLUMN_NUMBER)
    lcd.clear()
    #set buzzer
    buzzer = PWM(Pin(16))
    #init mfrc522
    spi = SPI(1,baudrate=2500000,polarity=0,phase=0,sck=Pin(SCK),mosi=Pin(MOSI),miso=Pin(MISO))
    card_scanner = MFRC522(spi,SDA,RST)
    #init RGB LED
    red = PWM(Pin(21))
    green = PWM(Pin(20))
    blue = PWM(Pin(19))
    red.freq(1000)
    green.freq(1000)
    blue.freq(1000)
    #init rtc
    rtc = DS1302(clk=Pin(2),dio=Pin(3),cs=Pin(4))
    rtc.start()
    # ct =  rtc.date_time()
    print("--- I am here")
    ntptime.host = TIME_HOST
    ntptime.settime()
    local_time = init_time()
    print(local_time)
    now = (local_time[0],local_time[1],local_time[2],local_time[6] + 1,local_time[3],local_time[4],local_time[5])
    print(now)
    rtc.date_time(now)
        

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
               time.sleep(2)
               break       
           

def init_time():
    local_time = time.localtime(time.time() + UTC_OFFSET)
    return local_time

def get_current_time():
    now =  rtc.date_time()
    if now is not None:
        current_time = "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(
             now[0], now[1], now[2],now[4], now[5], now[6])
        print(current_time)
        return current_time

def show_data_on_lcd(data:dict):
    print(data)
    lcd.move_to(0,0)
    lcd.putstr(data["username"])
    lcd.move_to(0,1)
    timestr = str(data["current_time"]).split(" ")[1]
    lcd.putstr(f"Time: {timestr}")
      

def uid_read() -> str:
    uid_str = ""
    if card_scanner is not None:
        (stat,tag_type) = card_scanner.request(card_scanner.REQIDL)
        if stat == card_scanner.OK:
            (stat,uid) = card_scanner.anticoll()
            if stat == card_scanner.OK:
                uid_hex = "0x" + "".join(["%02X" % x for x in uid])
                uid_str = uid_hex
    return uid_str            

def setcolor(r:int,g:int,b:int):
    if red is not None and green is not None and blue is not None:
        red.duty_u16(r * 257)
        green.duty_u16(g * 257)
        blue.duty_u16(b * 257)
            
def send_data(path:str, method:str,params:dict = None)->dict:
    path = SERVER_HOST + path
    result = {}
    if method == "post":
       response =  urequests.post(url = path, json = params, timeout = 5)
    elif method == "get":
       print(path)
       response = urequests.get(url=path,timeout = 5)
    result = response.json()
    response.close()
    return result

def play_sound(start_freq, end_freq, duration_ms,volume = 30):
    if buzzer is not None:
        duty = int((volume / 100) * 32768)
        steps = 20
        step_time = duration_ms//steps
        step_freq = (end_freq - start_freq) // steps
        for i in range(steps):
          current_freq = start_freq + (step_freq * i)
          if current_freq > 0:
             buzzer.freq(current_freq)
             buzzer.duty_u16(duty)
          time.sleep_ms(step_time)
        buzzer.duty_u16(0)

def alert_check_in():
    setcolor(0,255,0)
    play_sound(800,2000,2000,volume=30)
    setcolor(0,0,0)

def alert_check_out():
    setcolor(255,165,0)
    play_sound(2000,800,2000,volume=30)
    setcolor(0,0,0)

def alert_unknown():
    setcolor(255,0,0)
    play_sound(1000,1000,1000,volume=30)
    setcolor(0,0,0)

def loop():
    global last_time
    while True:
        uid = uid_read()
        if uid == "":
            current_timestamp = time.time()
            if current_timestamp - last_time >= 1:
               last_time = current_timestamp
               current_time = str(get_current_time())
               lcd.move_to(0,0)
               lcd.putstr(current_time.split(" ")[0])
               lcd.move_to(0,1)
               lcd.putstr(current_time.split(" ")[1])
        else:
            print(uid)
            #get current time
            now = get_current_time()
            # check this uid whether exist in Database
            path = f"/user/check?uid={uid}"
            userResult = send_data(path,"get")
            user_exist = bool(userResult["data"])
            if not user_exist:
                ## make buzzer have unknown sound
                alert_unknown()
                continue
            # get user information
            user_info_path = f"/user/info?uid={uid}"
            userInfo = send_data(user_info_path,"get")
            username = userInfo["data"]["username"] 
            ##check attendance record
            is_check_path = f"/check/attendance?uid={uid}"
            isCheckResult = send_data(is_check_path,"get")
            check_flag = bool(isCheckResult["data"])
            if check_flag:
                # add check-in data 
                check_in_param = {
                    "uid":uid,
                    "type":"0",
                    "current_time":now
                }
                check_in_path = f"/insert/attendance"  
                send_data(check_in_path,"post",check_in_param)
                checkinshow = {
                    "username":username,
                    "current_time":now
                }
                show_data_on_lcd(checkinshow)
                # check-in sound
                alert_check_in()
            else:
                # add check-in data 
                check_out_param = {
                    "uid":uid,
                    "type":"1",
                    "current_time":now
                }
                check_in_path = f"/insert/attendance"  
                send_data(check_in_path,"post",check_out_param)
                checkoutshow = {
                    "username":username,
                    "current_time":now
                }
                lcd.clear()
                show_data_on_lcd(checkoutshow)
                # check-in sound
                print("hello I'm check out")
                alert_check_out()
            time.sleep(2)
            lcd.clear()

def main():
    setup()
    loop()

main()