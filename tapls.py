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
  def is_v2_header_block(self):
    return True if self.__block_length == 27 and self.__data[0] == 0 else False

  def valid_checksum(self, is_v2_tap_file):
    slice = self.__data[1:-1] if is_v2_tap_file else self.__data[:-1]
    checksum = functools.reduce(lambda acc, b: acc ^ b, slice, 0)
    return (True, checksum) if checksum == self.__data[-1] else (False, checksum, self.__data[-1])

  def data(self, *slice_idxs):
    idx_len = len(slice_idxs)
    if idx_len == 0:
      return self.__data[0:-1]
    elif idx_len == 1:
      return self.__data[slice_idxs[0]]
    return self.__data[slice_idxs[0]:slice_idxs[1]]


def tap_list(tap_filenames, is_v2_verification):
  def tap_crc_error(block, is_v2):
    vcsd = block.valid_checksum(is_v2)
    if not vcsd[0]:
      return ", CRC ERROR (checksum [%.2x], expected [%.2x])" % (vcsd[1], vcsd[2])
    return ""
  for tap_filename in map(lambda fn: os.path.relpath(fn), tap_filenames):
    with open(tap_filename, 'rb') as tap_fd:
      try:
        print(tap_filename)
        while True:
          hdr_block = Block(tap_fd)
          data_block = Block(tap_fd)
          is_v2_file = True if is_v2_verification else hdr_block.is_v2_header_block
          filename = hdr_block.data(2, 12).decode('utf-8') if hdr_block.is_v2_header_block else hdr_block.data(1,11).decode('utf-8')
          print("\t%s" % filename)
          print("\t\tHeader Block: %d bytes%s" % (hdr_block.block_length, tap_crc_error(hdr_block, is_v2_file)))
          print("\t\t  Data Block: %d bytes%s" % (data_block.block_length, tap_crc_error(data_block, is_v2_file)))
      except BlockDataExhausted:
        pass


if __name__ == '__main__':
  import argparse

  __VERSION = "1.1.0"

  parser = argparse.ArgumentParser(prog = "tapls.py",
                                   description = "List the contents of a TAP file (v%s)." % __VERSION)
  parser.add_argument('--v2',
                      dest = 'is_v2_verification',
                      action = 'store_true',
                      help = 'Enable Jester Ace v2 TAP file verification')
  parser.add_argument('tap_file',
                      nargs = '+',
                      type = str,
                      help = 'TAP filename')
  args = parser.parse_args()

  tap_list(args.tap_file, args.is_v2_verification)
