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
        # We receive an extra 5 bytes before the data. The first two
        # bytes are '+=', then there's a checksum, then the length of
        # the data to receive.
        header = ser.read(5)
        assert header[0:2] == b'+='
        expected_chksum = header[2]
        expected_length = (header[3] << 8) | header[4]
        assert expected_length == length
        data = ser.read(length)
        if len(data) == length:
            log('successful read')
            # Send ACK (just +, but need to escape)
            ser.write(b'\x1b+\n')
            chksum = header[1] + header[3] + header[4]
            for b in data:
                chksum += b
            chksum = chksum & 0xff
            #log('expected_chksum={}, chksum={}'.format(expected_chksum, chksum))
            assert expected_chksum == chksum
            return data
        else:
            log('error: only received {} bytes'.format(len(data)))

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
    # From the schematic, I think this can be read at 0x4080000. This
    # is mostly mirrored at 0x4000000, but there the first 16 bytes
    # are masked by the RTC?

    main(0x4080000, 512 * 1024, './nvram.bin')

    # RTC / watchdog
    # https://www.futurlec.com/Datasheet/Dallas/DS1286.pdf

    # From the schematic, it looks like the first 16 bytes of this can
    # be accessed at 0x4000000. The last two of these are user
    # regsiters, and could potentially be used by the scope, though it
    # seems unlikely?

    #main(0x4000000, 16, './rtc.bin')

    # Boot ROM

    # The schematic mentions an Intel 27010 EPROM, which is a 128k x 8
    # device?
    # https://www.elnec.com/en/device/Intel/27010/

    # However, the schematic shows enough lines to address 256k * 8,
    # which we might have. The address mapping is done with a custom
    # IC, so this can't be read from the schematic.

    #main(0x0000000, 256 * 1024, './boot_rom.bin')

    # The flash ROM in the device appears to be 12 x N28F020
    # https://www.elnec.com/en/device/Intel/N28F020+%5BPLCC32%5D/
    # Each of these is 256k x 8
    # (Though the schematic mentions 28F010.)

    # Aside, unlike the other memories mention here, these put 32 bits
    # onto the data bus, and as a result don't get to see the first
    # two address lines, A0 & A1.

    # It seems to me that there is 3 MBytes of flash ROM on the CPU
    # board, accessible at 0x1000000.

    # main(0x1000000, 3 * 1024 * 1024, './flash_rom.bin')
