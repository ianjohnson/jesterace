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
    tap_file.seek(pos)
    self._data = tap_file.read(self.__block_length + 2)
    if not self._data or len(self._data) != self.__block_length + 2:
      raise BlockDataExhausted

  def block_length(self):
    return self.__block_length

  def write_data(self, fd):
    fd.write(self._data)


class Header(Block):
  def __init__(self, tap_file):
    super(Header, self).__init__(tap_file)

  def filename(self):
    return self._data[4:14].decode("utf-8").strip()


class Data(Block):
  def __init__(self, tap_file):
    super(Data, self).__init__(tap_file)


def tap_split(tap_file, max_filename_len):
  while(True):
    try:
      header = Header(tap_file)
    except BlockDataExhausted:
      break
    try:
      data = Data(tap_file)
    except BlockDataExhausted as ex:
      print("%s file is corrupt" % header.filename(), file = sys.stderr)
      raise ex
    print("Found %s (%d:%d)" % (header.filename(), header.block_length(), data.block_length()))
    split_filename = (header.filename()[:max_filename_len] + '.tap').upper()
    print("\tSplit file to %s..." % split_filename)
    with open(split_filename, "wb") as split_tap:
      header.write_data(split_tap)
      data.write_data(split_tap)


if __name__ == '__main__':
  import argparse

  __VERSION = "1.0.2"
  default_max_filename_len = 8

  parser = argparse.ArgumentParser(prog = "tapsplit.py",
                                   description = "Creates separate TAP files from a multi-program TAP file (v%s)." % __VERSION)
  parser.add_argument('-m', '--maxnamelen',
                      type = int,
                      dest = 'max_filename_len',
                      default = default_max_filename_len,
                      help = 'Maximum length of TAP file name split out (default: %d)' % default_max_filename_len)
  parser.add_argument('tap_file',
                      type = str,
                      default = '',
                      help = 'TAP file to split')
  args = parser.parse_args()

  if not os.path.exists(args.tap_file):
    print("TAP file [%s] does not exist" % args.tap_file, file = sys.stderr)
    sys.exit(1)

  with open(args.tap_file, "rb") as tap_file:
    tap_split(tap_file, args.max_filename_len)
