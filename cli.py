# Tek TDS Backup Tool
# Copyright (C) 2021  Paul Horsfall

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

#!/usr/bin/env python3

import argparse
import serial

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
    return bytes(out)

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
    return escape(bytes(out))

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
            # Send ACK
            ser.write(escape(b'+') + b'\n')
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

def main(device, offset, length, filename):
    assert offset >= 0
    assert length >= 0
    assert length % CHUNK_SIZE == 0
    num_chunks = length // CHUNK_SIZE

    ser = serial.Serial(device, 115200, timeout=1)
    gpib_init(ser)
    ser.timeout = 10

    with open(filename, 'wb') as f:
        for i in range(num_chunks):
            addr = offset + CHUNK_SIZE * i
            data = gpib_read(ser, addr, CHUNK_SIZE)
            f.write(data)

    ser.close()

# Allow hex literals to be given as command line arguments.
def int_literal(x):
    return int(x, 0)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('device', help='The serial port on which the AR488 is available.')
    parser.add_argument('offset', type=int_literal, help='The address from which to start reading data.')
    parser.add_argument('length', type=int_literal, help='The number of bytes to read.')
    parser.add_argument('filename', help='The name of the output file.')
    args = parser.parse_args()
    main(args.device, args.offset, args.length, args.filename)
