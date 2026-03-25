import utime
def mario():
    while True:
        try:
            height = int(input("Please enter the height: "))
            if height < 2 or height > 8:
                print("the height should between 2 and 8.")
                continue
            for i in range(1,height+1):
               leftLine = bytearray(b" " * i)
               rightLine = bytearray(b" " * i)
               left = 0
               right = i - 1
               while left <= (i -1) and right >= 0:
                   leftLine[left] = ord("#")
                   rightLine[right] = ord("#")
                   left+=1
                   right-=1
                   print("\r"+" "*(height - i)+leftLine.decode()+ "  " + rightLine.decode(),end="")
                   utime.sleep_ms(500)
               print()    
        except ValueError:
            print("please fill the integer.")

mario()