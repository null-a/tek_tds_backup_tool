# Tektronix TDS Backup Tool

## Introduction

This is a program which can read the memory of some old Tektronix TDS
series oscilloscopes. Data is read over the oscilloscope's GPIB bus
using an Arduino
running [AR488](https://github.com/Twilight-Logic/AR488). Here's the
setup:

```
[Computer] <--USB Serial--> [Arduino AR488] <--GPIB--> [Oscilloscope]
```

## Status

I wrote this to backup the data on my TDS 540A. Now that I have done
so, I don't expect to work on it any further. However, it took me a
little while to get this working, so I'm sharing the code and these
notes in case anyone else attempting something similar finds them
useful.

## How It Works

Data is read by repeatedly issuing a memory read command over GPIB. I
learned of this existence of this command, and how to use it,
from
[`tektool`](https://github.com/ragges/tektools/tree/master/tektool).
The main differences between this program and `tektool` are:

* This program uses an Arduino running AR488 for interfacing, which is
  not supported by `tektool` AFAICT.
* This program can only read data. `tektool` has additional features,
  such as the ability to write data.

## Supported Devices

Since this program uses the same approach as `tektool`, I expect it to
work with the same devices. This means it probably works with the TDS
5xx/6xx/7xx series, for example. However, I have only tested it with
my TDS 540A.

## AR488 Setup

The Arduino should be running the AR488 firmware and connected to the
GPIB bus of the oscilloscope.

IMPORTANT: I suspect that (in my particular case) I only had this
working reliably (on an Arduino Diecimila) after I disabled the use of
interrupts by the AR488. This can be done by commenting out the
`#define USE_INTERRUPTS` line in `AR488_Config.h`.

If you don't have a Centronics 24 pin connector to allow connection to
the external GPIB port of the oscilloscope, you might
consider
[connecting the Arduino directly](https://www.dropbox.com/s/j50jz1x2fvnk9x9/idc_header.jpg?raw=1) the
GPIB IDC connector on CPU board.

## Enabling Memory Access

The oscilloscope typically needs to be booted in a special mode to
gain access to the memory read command. On many models, this is done
as follows:

* Turn off the oscilloscope.
* Move the memory protect switch, located within the case, to the
  unprotected position.
* Power on the oscilloscope.

It is normal for the screen to be blank, and all front panel LEDs lit,
when booting in this mode.

## Usage

The [main program](./cli.py) is able to read an arbitrary section of
memory and write its contents to an output file.

```
usage: cli.py [-h] device offset length filename

positional arguments:
  device      The serial port on which the AR488 is available.
  offset      The address from which to start reading data.
  length      The number of bytes to read.
  filename    The name of the output file.
```

Different models of oscilloscope have interesting data at differing
locations. A [script](./tds540a.sh) is provided that retrieves NVRAM
and ROM from a TDS 540A as an example. However, please don't rely on
the correctness of this; be sure to satisfy yourself that you have all
the data you need if using this to program to perform a backup.
The [EEVblog](https://www.eevblog.com/forum/)
and [Tektronix](https://forum.tek.com/index.php) forums are good
places to look for information about the memory addresses used by
specific models.

## Dependencies

* Python 3
* `pyserial`
