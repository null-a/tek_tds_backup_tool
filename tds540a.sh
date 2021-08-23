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

#!/bin/bash
set -e
if [ $# -eq 0 ]; then
 echo "Usage" $0 "<serial_device>"
 exit 1
fi

# Tektronix TDS 540A
# ==================

# NVRAM
# -----

# The Dallas DS1650Y is a 512k x 8 device.
# https://www.elnec.com/en/device/Dallas/DS1650Y/
#
# From the schematic, I think this can be read at 0x4080000. This is
# mostly mirrored at 0x4000000, but there the first 16 bytes are
# masked by the RTC?

./cli.py $1 0x4080000 $((512 * 1024)) nvram.bin

# RTC
# ---

# https://www.futurlec.com/Datasheet/Dallas/DS1286.pdf

# From the schematic, it looks like the first 16 bytes of this can
# be accessed at 0x4000000. The last two of these are user
# regsiters, and could potentially be used by the scope, though it
# seems unlikely?

# (Read more data than required since the script only handles
# multiples of 1K.)

#./cli.py $1 0x4000000 $((1 * 1024)) rtc.bin

# Boot ROM
# --------

# The schematic mentions an Intel 27010 EPROM, which is a 128k x 8
# device?
# https://www.elnec.com/en/device/Intel/27010/

# However, the schematic shows enough lines to address 256k * 8,
# which we might have. The address mapping is done with a custom
# IC, so this can't be read from the schematic.

./cli.py $1 0x0 $((256 * 1024)) boot_rom.bin

# Flash ROM
# ---------

# The flash ROM in the device appears to be 12 x N28F020
# https://www.elnec.com/en/device/Intel/N28F020+%5BPLCC32%5D/
# Each of these is 256k x 8
# (Though the schematic mentions 28F010.)

# Aside, unlike the other memories mention here, these put 32 bits
# onto the data bus, and as a result don't get to see the first
# two address lines, A0 & A1.

# It seems to me that there is 3 MBytes of flash ROM on the CPU
# board, accessible at 0x1000000.

./cli.py $1 0x1000000 $((3 * 1024 * 1024)) flash_rom.bin
