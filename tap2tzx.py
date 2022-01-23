#! /usr/bin/env python3
########################################################################
# MIT License
#
# Copyright (C) 2021-2022 Ian Johnson
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
########################################################################
import functools
import os
import sys


class BlockDataExhausted(Exception):
  pass

class BlockDataCorruption(Exception):
  pass


class TapBlock(object):
  def __init__(self, tap_file):
    block_length_bytes = tap_file.read(2)
    self.__block_length = int.from_bytes(block_length_bytes, "little")
    self.__data = tap_file.read(self.__block_length)
    if not self.__data or len(self.__data) != self.__block_length:
      raise BlockDataExhausted

  @property
  def length(self):
    return self.__block_length

  @property
  def is_v2_header_block(self):
    return True if self.__block_length == 27 and self.__data[0] == 0 else False

  def valid_checksum(self, is_v2_tap_file):
    slice = self.__data[1:-1] if is_v2_tap_file else self.__data[:-1]
    checksum = functools.reduce(lambda acc, b: acc ^ b, slice, 0)
    return (True, checksum) if checksum == self.__data[-1] else (False, checksum, self.__data[-1])

  def write_data(self, fd):
    fd.write(self.__data)


def tzx_header_write(tzx_file):
  hdr = bytearray("ZXTape!", "utf-8") + bytearray.fromhex("1a0114")
  tzx_file.write(hdr)


def tap_to_tzx(tap_filenames, tzx_filename, block_delay):
  with open(tzx_filename, 'wb') as tzx_file:
    # Write TZX header
    tzx_header_write(tzx_file)
    # Foreach TAP file...
    for tap_filename in [item for sublist in tap_filenames for item in sublist]:
      with open(tap_filename, 'rb') as tap_file:
        print(os.path.basename(tap_filename), file = sys.stderr)
        # Foreach block in the TAP...
        while(True):
          # Header block
          try:
            hdr_block = TapBlock(tap_file)
          except BlockDataExhausted:
            break
          print("  +--> Found header block of length %d bytes" % hdr_block.length,
                file = sys.stderr,
                end = "")
          is_v2_tap_file = hdr_block.is_v2_header_block
          valid_chksum = hdr_block.valid_checksum(is_v2_tap_file)
          if not valid_chksum[0]:
            print(", CRC ERROR (checksum [%.2x], expected [%.2x])" % (valid_chksum[1], valid_chksum[2]),
                  file = sys.stderr,
                  end = "")
          print(file = sys.stderr)

          # Data block expected
          try:
            data_block = TapBlock(tap_file)
          except BlockDataExhausted as ex:
            print("Missing data block in %s" % tap_filename)
            raise ex
          print("  +--> Found data block of length %d bytes" % data_block.length,
                file = sys.stderr,
                end = "")
          valid_chksum = data_block.valid_checksum(is_v2_tap_file)
          if not valid_chksum[0]:
            print(", CRC ERROR (checksum [%.2x], expected [%.2x])" % (valid_chksum[1], valid_chksum[2]),
                  file = sys.stderr,
                  end = "")
          print(file = sys.stderr)

          # Ensure block ID bytes are present in header and data blocks
          hdr_length = hdr_block.length if is_v2_tap_file else hdr_block.length + 1
          ssdb_hdr = bytearray.fromhex("10") + int(block_delay).to_bytes(2, 'little') + int(hdr_length).to_bytes(2, 'little')
          if not is_v2_tap_file:
            ssdb_hdr += bytearray.fromhex("00")

          data_length = data_block.length if is_v2_tap_file else data_block.length + 1
          ssdb_data = bytearray.fromhex("10") + int(block_delay).to_bytes(2, 'little') + int(data_length).to_bytes(2, 'little')
          if not is_v2_tap_file:
            ssdb_data += bytearray.fromhex("ff")

          # Write TZX blocks
          tzx_file.write(ssdb_hdr)
          hdr_block.write_data(tzx_file)
          tzx_file.write(ssdb_data)
          data_block.write_data(tzx_file)
          


if __name__ == '__main__':
  import argparse

  __VERSION = "2.0.0"
  default_delay_ms = 100

  parser = argparse.ArgumentParser(prog = "tap2tzx.py",
                                   description = "Converts TAP files to TZX files (v%s)." % __VERSION)
  parser.add_argument('-d', '--delay',
                      type = int,
                      dest = 'delay',
                      default = default_delay_ms,
                      help = "Delay, in ms, between TZX data blocks (default: %dms)" % default_delay_ms)
  parser.add_argument('-o', '--output',
                      type = str,
                      required = True,
                      dest = 'tzx_output',
                      help = "Output TZX file")
  parser.add_argument('tap_file',
                      type = str,
                      action = 'append',
                      nargs = '+',
                      help = "TAP file to add to the TZX file")
  args = parser.parse_args()

  tap_to_tzx(args.tap_file, args.tzx_output, args.delay)
