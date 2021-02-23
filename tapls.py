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


class BlockDataExhausted(Exception):
  pass


class Block(object):
  def __init__(self, tap_file):
    pos = tap_file.tell()
    block_length_bytes = tap_file.read(2)
    self.__block_length = int.from_bytes(block_length_bytes, "little")
    self.__data = tap_file.read(self.__block_length)
    if not self.__data or len(self.__data) != self.__block_length:
      raise BlockDataExhausted

  @property
  def block_length(self):
    return self.__block_length

  @property
  def is_header(self):
    return True if self.__data[0] == 0 else False

  @property
  def valid_checksum(self):
    checksum = functools.reduce(lambda acc, b: acc ^ b, self.__data[1:-1], 0)
    return True if checksum == self.__data[-1] else False

  def data(self, *slice_idxs):
    idx_len = len(slice_idxs)
    if idx_len == 0:
      return self.__data[0:-1]
    elif idx_len == 1:
      return self.__data[slice_idxs[0]]
    return self.__data[slice_idxs[0]:slice_idxs[1]]


def tap_list(tap_filenames):
  tap_crc_error = lambda block: ", CRC ERROR" if not block.valid_checksum else ""
  for tap_filename in map(lambda fn: os.path.relpath(fn), tap_filenames):
    with open(tap_filename, 'rb') as tap_fd:
      try:
        print(tap_filename)
        while True:
          hdr_block = Block(tap_fd)
          if hdr_block.is_header:
            data_block = Block(tap_fd)
            filename = hdr_block.data(2, 12).decode('utf-8')
            print("\t%s" % filename)
            print("\t\tHeader Block: %d bytes%s" % (hdr_block.block_length, tap_crc_error(hdr_block)))
            print("\t\t  Data Block: %d bytes%s" % (data_block.block_length, tap_crc_error(data_block)))
      except BlockDataExhausted:
        pass


if __name__ == '__main__':
  import argparse

  __VERSION = "1.0.0"

  parser = argparse.ArgumentParser(prog = "tapls.py",
                                   description = "List the contents of a TAP file (v%s)." % __VERSION)
  parser.add_argument('tap_file',
                      nargs = '+',
                      type = str,
                      help = 'TAP file to split')
  args = parser.parse_args()

  tap_list(args.tap_file)
