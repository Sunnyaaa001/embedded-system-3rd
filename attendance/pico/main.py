from machine import Pin,PWM,I2C,SPI
from ds1302 import DS1302
from lcd_api import LcdApi
from i2c_lcd import I2cLcd
import time
import network
import ntptime
from mfrc522 import MFRC522
from microdot import Microdot,Request,send_file
import uasyncio
import ujson
import os

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

scanner_locker = True

app = Microdot()

@app.after_request
async def add_cors(request, response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = '*'
    response.headers['Access-Control-Allow-Headers'] = '*'
    return response

def setup():
    global i2c,lcd,rtc,spi,card_scanner,buzzer,red,green,blue
    init_db()
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
    rtc.stop()
    # ct =  rtc.date_time()
    print("--- I am here")
    ntptime.host = TIME_HOST
    ntptime.settime()
    local_time = init_time()
    print(local_time)
    now = (local_time[0],local_time[1],local_time[2],local_time[6] + 1,local_time[3],local_time[4],local_time[5])
    print(now)
    rtc.date_time(now)
    rtc.start()

        

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



def init_db():
    if "db" not in os.listdir():
        os.mkdir("db")
        print("Directory 'db' created.")

    db_files = ["user_info.json", "attendance.json"]
    current_files = os.listdir("db")
    for file_name in db_files:
        path = "db/" + file_name
        if file_name not in current_files:
            with open(path, 'w') as f:
                ujson.dump({}, f)
            print(f"File {path} initialized with {{}}")
        else:
            print(f"File {path} already exists.")    



def save_user(data:dict):
    db_file = "db/user_info.json"
    with open(db_file,"r") as f:
        data_list = ujson.load(f)
        if not isinstance(data_list,list):
             data_list = []
    records = len(data_list) + 1
    data["id"] = records         
    data_list.append(data)

    with open(db_file,"w") as f:
        ujson.dump(data_list,f)

def insert_attendance(data:dict):
    print(data)
    db_file = "db/attendance.json"
    with open(db_file,"r") as f:
        data_list = ujson.load(f)
        if not isinstance(data_list,list):
             data_list = []
    now = rtc.date_time()
    today = "{:04d}-{:02d}-{:02d}".format(now[0],now[1],now[2])
    record = next((item for item in data_list if item["user_id"] == data["user_id"] 
                   and item["type"] == data["type"] and str(item["current_time"]).startswith(today)),None)
    if record:
        record["current_time"] = data["current_time"]
    else:
        id = len(data_list) + 1
        data["id"] = id
        data_list.append(data)
    print(f"attendance data {data_list}")    
    with open(db_file,"w") as f:
        ujson.dump(data_list,f)    

def user_exist(uid:str) -> bool:
    db_file = "db/user_info.json"
    with open(db_file,"r") as f:
        data_list = ujson.load(f)
        if not isinstance(data_list,list):
             data_list = []
    if len(data_list) == 0:
        return False
    user = next((u for u in data_list if u["uid"] == uid),None) 
    if user:
        return True
    else:
        return False

def user_info(uid:str)->dict:
    db_file = "db/user_info.json"
    with open(db_file,"r") as f:
        data_list = ujson.load(f)
        if not isinstance(data_list,list):
             data_list = []

    user = next((u for u in data_list if u["uid"] == uid),{})
    return user

def check_attendance(user_id:str) -> bool:
     db_file = "db/attendance.json"
     with open(db_file,"r") as f:
        data_list = ujson.load(f)
        if not isinstance(data_list,list):
             data_list = []
     print(data_list)        
     now = rtc.date_time()
     today = "{:04d}-{:02d}-{:02d}".format(now[0],now[1],now[2])
     records = [item for item in data_list if item["user_id"] == user_id 
           and str(item["current_time"]).startswith(today)]
     print(f"r-----{records}")
     if len(records) == 0:
         return True
     else:
         return False
     



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
    setcolor(255,255,100)
    play_sound(2000,800,2000,volume=30)
    setcolor(0,0,0)

def alert_unknown():
    setcolor(255,0,0)
    play_sound(1000,1000,1000,volume=30)
    setcolor(0,0,0)

async def loop():
    global last_time, scanner_locker
    while True:
        if scanner_locker:
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
                now = get_current_time()
                is_user = user_exist(uid)
                if not is_user:
                    lcd.clear()
                    lcd.move_to(0,0)
                    lcd.putstr("Uknown Card")
                    alert_unknown()
                    lcd.clear()
                    await uasyncio.sleep(0.1)
                    continue
                userInfo = user_info(uid)
                username = userInfo["first_name"]
                check_flag = check_attendance(userInfo["id"])
                if check_flag:
                    check_in_param = {
                        "user_id":userInfo["id"],
                        "type":"0",
                        "current_time":now
                    } 
                    insert_attendance(check_in_param)
                    checkinshow = {
                        "username": "Hello " + username,
                        "current_time":now
                    }
                    lcd.clear()
                    show_data_on_lcd(checkinshow)
                    alert_check_in()
                    lcd.clear()
                else:
                    check_out_param = {
                        "user_id":userInfo["id"],
                        "type":"1",
                        "current_time":now
                    } 
                    insert_attendance(check_out_param)
                    checkoutshow = {
                        "username":"Good Bye "+username,
                        "current_time":now
                    }
                    lcd.clear()
                    show_data_on_lcd(checkoutshow)
                    print("hello I'm check out")
                    alert_check_out()
                await uasyncio.sleep(2)
                lcd.clear()
        
        await uasyncio.sleep(0.1)

@app.get("/uid/info")
async def get_uid(request):
    global scanner_locker
    scanner_locker = False
    headers = {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*"
    }
    while True:
        uid = uid_read()
        if uid != "":
            lcd.clear()
            lcd.move_to(0,0)
            lcd.putstr("Scan Sucessfully!")
            alert_check_in()
            lcd.clear()
            scanner_locker = True
            return ujson.dumps({"code":200,"data":uid}),200,headers
        else:
            lcd.move_to(0,0)
            lcd.putstr("Waiting user scan card..")
        await uasyncio.sleep(0.1)

@app.route("/insert/user", methods=["POST", "OPTIONS"])
async def insert_user_info(request):
    h = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "POST, GET, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type",
        "Content-Type": "application/json"
    }
    if request.method == "OPTIONS":
        return "", 204, h

    try:
        import gc
        gc.collect()
        
        data = request.json
        if not data:
            import ujson
            data = ujson.loads(request.body) 

        print("Data received:", data)
        save_user(data)
        
        return {"code": 200, "msg": "ok"}, 200, h     
    except Exception as e:
        print("Error in POST:", e)

        return {"code": 500, "error": str(e)}, 500, h

@app.route("/attendance/show",methods=["GET","OPTIONS"])
async def attendance_show(request:Request):
    headers = {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Authorization" 
    }

    if request.method == "OPTIONS":
        return "", 204, headers
    db_file = "db/user_info.json"
    with open(db_file,"r") as f:
        users = ujson.load(f)
        if not isinstance(users,list):
             users = []

    db_file = "db/attendance.json"
    with open(db_file,"r") as f:
        attendance_list = ujson.load(f)
        if not isinstance(attendance_list,list):
             attendance_list = []

    for user in users:
        now = rtc.date_time()
        today = "{:04d}-{:02d}-{:02d}".format(now[0],now[1],now[2])
        attendance = [at for at in attendance_list if at["user_id"] == user["id"] and str(at["current_time"]).startswith(today)]
        user["attendance"] =attendance

    return ujson.dumps({"code":200,"data":users}),200,headers                     


@app.route('/')
async def index(request):
    return send_file('static/index.html')

@app.route('/<path:path>')
async def static(request, path):
    return send_file(path)


if __name__ == "__main__":
    setup()
    uasyncio.create_task(loop())
    app.run(port=8081,debug=True)