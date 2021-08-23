import time
import serial

"""
Notes:

I've commented out `#define USE_INTERRUPTS` in the AV488 project
(`AR488_Config.h`) when running on my Arduino Diecimila. This seems to
improve reliability to the point where things are useable, but I'm not
100% sure about the necessity of this.

"""

VERBOSE = True

def log(str):
    if VERBOSE:
        print(str)

# Escape binary data as described in the AR488 manual.

CTRL_CHARS = [13, 10, 27, 43]

def escape(chars):
    out = []
    for c in chars:
        if c in CTRL_CHARS:
            out.append(27)
        out.append(c)
    return out

def read_cmd(addr, length):
    out = [
        # header
        b'm'[0], # command 'm'
        0, # check sum
        0, 8, # body length of this command
        # body
        0, 0, 0, 0, # address
        0, 0, 0, 0, # length
    ]
    out[4] = (addr >> 24) & 0xff
    out[5] = (addr >> 16) & 0xff
    out[6] = (addr >> 8) & 0xff
    out[7] = addr & 0xff
    out[8] = (length >> 24) & 0xff
    out[9] = (length >> 16) & 0xff
    out[10] = (length >> 8) & 0xff
    out[11] = length & 0xff
    checksum = 0
    for i in range(12):
        if not i == 1:
            checksum += out[i]
    out[1] = checksum & 0xff
    return bytes(escape(out))

def pp(bs):
    return ' '.join('{:02x}'.format(b) for b in bs)

def gpib_init(ser):
    # For some reason it takes a while before things start working.
    # Here I just keep retrying `++ver` until there are signs of life
    # from the Arduino.
    while True:
        ser.write(b'++ver\n')
        line = ser.readline()
        if len(line) > 0:
            log(line)
            break
    ser.write(b'++ifc\n')
    ser.write(b'++addr 29\n')
    ser.write(b'++eoi 1\n') # assert eoi when sending command
    ser.write(b'++eos 3\n') # drop trailing newlines from sent commands
    ser.write(b'++read_tmo_ms 3000\n')


def gpib_read(ser, addr, length):
    cmd = read_cmd(addr, length)
    # log(cmd)
    while True:
        log('attempting read addr={}, length={}'.format(addr, length))
        ser.write(cmd + b'\n')
        ser.write(b'++read eoi\n')
        data = ser.read(length + 5)
        if len(data) == length + 5:
            log('successful read extra={}'.format(pp(data[0:5])))
            # Send ACK (just +, but need to escape)
            ser.write(b'\x1b+\n')
            chksum = data[1] + data[3] + data[4]
            for b in data[5:]:
                chksum += b
            chksum = chksum & 0xff
            log('check sum(?) = {:02X}'.format(chksum))
            return data[5:]
        else:
            log('error: only received {} bytes'.format(len(data)))
            if len(data) <= 5:
                log(data)

CHUNK_SIZE = 1024

def main(offset, length, filename):

    assert length % CHUNK_SIZE == 0
    num_chunks = length // CHUNK_SIZE

    ser = serial.Serial('/dev/tty.usbserial-A70061Un', 115200, timeout=1)
    gpib_init(ser)
    ser.timeout = 10

    with open(filename, 'wb') as f:
        for i in range(num_chunks):
            addr = offset + CHUNK_SIZE * i
            data = gpib_read(ser, addr, CHUNK_SIZE)
            f.write(data)

    ser.close()

if __name__ == '__main__':
    # The Dallas DS1650Y is a 512k x 8 device.
    # https://www.elnec.com/en/device/Dallas/DS1650Y/
    #
    # But the schematic says "RAM_128kX8" for component U1108, perhaps
    #not all of this is used?

    main(0x4000000, 512 * 1024, './nvram.bin')

    # The Intel 27010 EPROM is a 128k x 8 device?
    # https://www.elnec.com/en/device/Intel/27010/

    #main(0x0000000, 256 * 1024, './kernel_rom.bin')

    # The flash ROM appears to be 12 x N28F010
    # https://www.elnec.com/en/device/Intel/N28F010+%5BPLCC32%5D/
    # Each of these is 128k x 8
