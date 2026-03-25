from machine import Pin, SPI

class MFRC522:
    OK = 0
    NOTAGERR = 1
    ERR = 2
    REQIDL = 0x26
    AUTH = 0x0E
    TRANSCEIVE = 0x0C

    def __init__(self, spi, gpio_cs, gpio_rst):
        self.spi = spi
        self.cs = Pin(gpio_cs, Pin.OUT)
        self.rst = Pin(gpio_rst, Pin.OUT)
        self.cs.value(1)
        self.rst.value(1)
        self.init()

    def _wreg(self, reg, val):
        self.cs.value(0)
        self.spi.write(bytes([(reg << 1) & 0x7E, val]))
        self.cs.value(1)

    def _rreg(self, reg):
        self.cs.value(0)
        self.spi.write(bytes([(reg << 1) & 0x7E | 0x80]))
        val = self.spi.read(1)
        self.cs.value(1)
        return val[0]

    def _sbits(self, reg, mask):
        self._wreg(reg, self._rreg(reg) | mask)

    def _cbits(self, reg, mask):
        self._wreg(reg, self._rreg(reg) & (~mask))

    def _tcard(self, cmd, send):
        recv = []
        bits = irq_en = wait_irq = 0
        stat = self.ERR

        if cmd == self.AUTH:
            irq_en, wait_irq = 0x12, 0x10
        elif cmd == self.TRANSCEIVE:
            irq_en, wait_irq = 0x77, 0x30

        self._wreg(0x02, irq_en | 0x80)
        self._cbits(0x04, 0x80)
        self._sbits(0x0A, 0x80)
        self._wreg(0x01, 0x00)

        for i in range(len(send)):
            self._wreg(0x09, send[i])

        self._wreg(0x01, cmd)
        if cmd == self.TRANSCEIVE:
            self._sbits(0x0D, 0x80)

        i = 2000
        while True:
            n = self._rreg(0x04)
            i -= 1
            if not ((i != 0) and not (n & 0x01) and not (n & wait_irq)):
                break

        self._cbits(0x0D, 0x80)

        if i != 0:
            if (self._rreg(0x06) & 0x1B) == 0x00:
                stat = self.OK
                if n & irq_en & 0x01:
                    stat = self.NOTAGERR
                elif cmd == self.TRANSCEIVE:
                    n = self._rreg(0x0A)
                    lb = self._rreg(0x0C) & 0x07
                    bits = (n - 1) * 8 + lb if lb != 0 else n * 8
                    n = 1 if n == 0 else (16 if n > 16 else n)
                    for _ in range(n):
                        recv.append(self._rreg(0x09))
        return stat, recv, bits

    def init(self):
        self.rst.value(0)
        self.rst.value(1)
        self._wreg(0x01, 0x0F)
        self._wreg(0x2A, 0x8D)
        self._wreg(0x2B, 0x3E)
        self._wreg(0x2D, 30)
        self._wreg(0x2C, 0)
        self._wreg(0x15, 0x40)
        self._wreg(0x11, 0x3D)
        self.antenna_on()

    def antenna_on(self, on=True):
        if on and not (self._rreg(0x14) & 0x03):
            self._sbits(0x14, 0x03)
        else:
            self._cbits(0x14, 0x03)

    def request(self, mode=0x26):
        self._wreg(0x0D, 0x07)
        (stat, recv, bits) = self._tcard(self.TRANSCEIVE, [mode])
        return (self.OK, bits) if (stat == self.OK and bits == 0x10) else (self.ERR, 0)

    def anticoll(self):
        self._wreg(0x0D, 0x00)
        (stat, recv, bits) = self._tcard(self.TRANSCEIVE, [0x93, 0x20])
        if stat == self.OK and len(recv) == 5:
            check = 0
            for i in range(4):
                check ^= recv[i]
            if check != recv[4]:
                stat = self.ERR
        return stat, recv