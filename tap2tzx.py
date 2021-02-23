#! /usr/bin/env python3
########################################################################
# MIT License
#
# Copyright (c) 2021 Ian Johnson
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
  def __init__(self, tap_file, correct_checksum = False):
    block_length_bytes = tap_file.read(2)
    self.__block_length = int.from_bytes(block_length_bytes, "little")
    self._data = tap_file.read(self.__block_length)
    if not self._data or len(self._data) != self.__block_length:
      raise BlockDataExhausted
    self._checksum = functools.reduce(lambda acc, b: acc ^ b, self._data[2:-1], self._data[1])
    if self._checksum != self._data[-1]:
      if correct_checksum:
        self._data = self._data[:-1] + bytes([self._checksum])
      else:
        raise BlockDataCorruption("Block checksum 0x%x, expected 0x%x" % (self._data[-1], self._checksum))

  def length(self):
    return self.__block_length

  def write_data(self, fd):
    fd.write(self._data)


def tzx_header_write(tzx_file):
  hdr = bytearray("ZXTape!", "utf-8") + bytearray.fromhex("1a0114")
  tzx_file.write(hdr)


def tap_to_tzx(tap_filenames, tzx_filename, block_delay, correct_checksum):
  with open(tzx_filename, 'wb') as tzx_file:
    # Write TZX header
    tzx_header_write(tzx_file)
    # Foreach TAP file...
    for tap_filename in [item for sublist in tap_filenames for item in sublist]:
      with open(tap_filename, 'rb') as tap_file:
        print(os.path.basename(tap_filename), file = sys.stderr)
        # Foreach block in the TAP...
        while(True):
          try:
            block = TapBlock(tap_file, correct_checksum)
          except BlockDataExhausted:
            break
          print("  +--> Found block of length %d bytes" % block.length(), file = sys.stderr)
          ssdb_hdr = bytearray.fromhex("10") + int(block_delay).to_bytes(2, 'little') + int(block.length()).to_bytes(2, 'little')
          tzx_file.write(ssdb_hdr)
          block.write_data(tzx_file)
          


if __name__ == '__main__':
  import argparse

  __VERSION = "1.0.1"
  default_delay_ms = 100

  parser = argparse.ArgumentParser(prog = "tap2tzx.py",
                                   description = "Converts TAP files to TZX files (v%s)." % __VERSION)
  parser.add_argument('-c', '--checksum',
                      action = 'store_true',
                      dest = 'correct_checksum',
                      help = "Correct a block's checksum if incorrect")
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

  tap_to_tzx(args.tap_file, args.tzx_output, args.delay, args.correct_checksum)
