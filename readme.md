# Tektronics TDS Backup Tool

## Introduction

This is a program which can read the memory of a Tektronix TDS series
oscilloscope. Data is read over the oscilloscope's GPIB bus using an
Arduino running AR488.

```
[Computer] <--USB Serial--> [Arduino AR488] <--GPIB--> [Oscilloscope]
```

## AV488 Setup

The Arduino should to be running the AR488 firmware and connected to
the GPIB bus of the oscilloscope.

If you don't have a Centronics 24 pin connector to allow connection to
the external GPIB port of the oscilloscope, you might consider
connecting the Arduino directly to the GPIB IDC connector on CPU
board.

IMPORTANT: I suspect that (in my particular case) I only had this
working reliably (on an Arduino Diecimila) after I disabled the use of
interrupts by the AR488. This can be done by commenting out the
`#define USE_INTERRUPTS` line in `AR488_Config.h`.

## Usage

The main program is able to read an arbitrary section of memory and
write its contents to an output file.

```
usage: cli.py [-h] device offset length filename

positional arguments:
  device      The serial port on which the AR488 is available.
  offset      The address from which to start reading data.
  length      The number of bytes to read.
  filename    The name of the output file.
```

Different models of oscilloscope have interesting data at differing
locations. An example script is provided that (to the best of my
knowledge) retrieves NVRAM and ROM from a TDS 540A. See `tds540a.sh`.

## Dependencies

* Python 3
* `pyserial`

## How It Works

Data is read by repeatedly issuing memory read commands over GPIB. I
learned of this existence of this command, and how to use it, from
`tektool`. The main differences between this program and `tektool`
are:

* This program uses an Arduino running AR488 for interfacing, which is
  not supported by `tektool` AFAICT.
* This program can only read data. `tektool` can write data, and
  perhaps has other features.
