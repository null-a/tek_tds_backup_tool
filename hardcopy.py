#!/usr/bin/env python3

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

import argparse
import serial

def main(device, address, filename):
    assert 0 <= address <= 30
    # Open output file for exclusive creation -- i.e. fail if already
    # exists.
    f = open(filename, 'xb')
    ser = serial.Serial(device, 115200, timeout=1)

    while True:
        ser.write(b'++ver\n')
        line = ser.readline()
        if len(line) > 0:
            break

    ser.write(bytes('++addr {:d}\n'.format(address), 'ascii'))
    ser.write(b'++eoi 1\n') # assert eoi when sending command
    ser.write(b'++read_tmo_ms 10000\n')

    ser.write(b'hardcopy:format bmp\n')
    ser.write(b'hardcopy:port gpib\n')
    ser.write(b'hardcopy start\n')
    ser.write(b'++read eoi\n')

    ser.timeout = 10
    bs = ser.read(38462)
    f.write(bs)

    ser.close()
    f.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('device', help='The serial port on which the AR488 is available.')
    parser.add_argument('address', help='The GPIB address of the scope.', type=int)
    parser.add_argument('filename', help='The output file.')
    args = parser.parse_args()
    main(args.device, args.address, args.filename)
