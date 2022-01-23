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


class BlockUnexpectedTypeException(Exception):
  def __init__(self, klass, offset, bid):
    super(BlockUnexpectedTypeException, self).__init__()
    self.__class = klass
    self.__offset = offset
    self.__bid = bid

  def __str__(self):
    return "Unexpected block at offset [%d], expected %s block, got [0x%.2x]" % \
      (self.__offset, self.__class, self.__bid)


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
    pos = tap_file.tell()
    super(Header, self).__init__(tap_file)
    self.__is_v2_tap = True if self.block_length == 27 else False
    if self.__is_v2_tap and self._data[2] != 0x00:
      raise BlockUnexpectedTypeException("header", pos, self._data[2])

  @property
  def is_v2_tap_file(self):
    return self.__is_v2_tap

  def filename(self):
    if self.is_v2_tap_file:
      return self._data[4:14].decode("utf-8").strip()
    return self._data[3:13].decode("utf-8").strip()


class Data(Block):
  def __init__(self, tap_file, is_v2_tap):
    pos = tap_file.tell()
    super(Data, self).__init__(tap_file)
    if is_v2_tap and self._data[2] != 0xff:
      raise BlockUnexpectedTypeException("header", pos, self._data[2])


def tap_split(tap_file, tap_dir):
  with open(tap_file, "rb") as tap_file_fd:
    print(tap_file)
    tap_names = dict()
    while(True):
      try:
        header = Header(tap_file_fd)
      except BlockDataExhausted:
        break
      try:
        data = Data(tap_file_fd, header.is_v2_tap_file)
      except BlockDataExhausted as ex:
        print("%s file is corrupt" % header.filename(), file = sys.stderr)
        raise ex
      print("\tFound program [%s] (%d:%d)" % (header.filename(), header.block_length(), data.block_length()), end = '')
      valid_split_filename = header.filename()[:8]
      if valid_split_filename in tap_names:
        tap_idx = tap_names[valid_split_filename]
        tap_idx += 1
        tap_names[valid_split_filename] = tap_idx
        tap_idx_s = "_%d" % tap_idx
        unique_split_filename = valid_split_filename[0:-len(tap_idx_s)] + tap_idx_s
      else:
        tap_names[valid_split_filename] = 1
        unique_split_filename = valid_split_filename
      split_filename = (unique_split_filename + '.tap').upper()
      print(", writing split file to [%s]..." % split_filename)
      with open(os.path.join(tap_dir, split_filename), "wb") as split_tap:
        header.write_data(split_tap)
        data.write_data(split_tap)


def taps_split(tap_files, root_dir, force):
  for tap_file in tap_files:
    tap_dirname, _ = os.path.splitext(os.path.basename(tap_file))
    tap_dirname = tap_dirname[:8].upper()
    tap_dir = os.path.realpath(os.path.join(root_dir, tap_dirname))
    if not force and os.path.exists(tap_dir):
      print("%s: TAP directory [%s] exists" % (os.path.realpath(tap_file), tap_dir),
            file = sys.stderr)
      return False
    else:
      os.mkdir(tap_dir)

    try:
      tap_split(tap_file, tap_dir)
    except Exception as ex:
      os.rmdir(tap_dir)
      raise ex


if __name__ == '__main__':
  import argparse

  __VERSION = "1.1.0"
  default_root_dir = os.path.realpath(".")
  default_max_filename_len = 8

  parser = argparse.ArgumentParser(prog = "tapsplit.py",
                                   description = "Creates separate TAP files from a multi-program TAP file (v%s)." % __VERSION)
  parser.add_argument('-f', '--force',
                      dest = 'force',
                      action = 'store_true',
                      help = 'Force conversion if TAP directory exists')
  parser.add_argument('-d', '--rootdir',
                      type = str,
                      dest = 'root_dir',
                      default = default_root_dir,
                      help = 'Directory to which the TAP directory structure will be written (default: %s)' % default_root_dir)
  parser.add_argument('tap_file',
                      type = str,
                      nargs = '+',
                      default = '',
                      help = 'TAP file to split')
  args = parser.parse_args()

  taps_split(args.tap_file, args.root_dir, args.force)
