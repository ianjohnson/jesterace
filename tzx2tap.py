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
import re
import os
import sys


block_id_registry = dict()


def tzx_block(klass):
  global block_id_registry
  block_id = (klass.BLOCK_ID).to_bytes(1, byteorder = 'little')
  block_id_registry[block_id] = klass
  return klass


class TZXFileNotValidError(Exception):
  pass


class TXZBlockUnsupportedException(Exception):
  def __init__(self, block_id):
    self.__block_id = block_id

  def __str__(self):
    return "Unsupported block ID [%X]" % self.__block_id


class TZXDataBlockIncorrectCountException(Exception):
  pass

  
class TZXBlock(object):
  def __init__(self, fd, attributes):
    for attr_name, no_bytes in attributes:
      if callable(no_bytes):
        no_bytes = no_bytes()
      value = fd.read(no_bytes)
      setattr(self, attr_name, value)


@tzx_block
class TZXHeader(TZXBlock):
  BLOCK_ID = 0x5a

  def __init__(self, fd):
    super(TZXHeader, self).__init__(fd, [('signature', 7),
                                         ('end_of_text_marker', 1),
                                         ('tzx_major_version', 1),
                                         ('tzx_minor_version', 1)])

  @property
  def signature(self):
    return self.__signature

  @signature.setter
  def signature(self, sig):
    self.__signature = sig.decode('utf-8')

  @property
  def end_of_text_marker(self):
    return self.__eot_marker

  @end_of_text_marker.setter
  def end_of_text_marker(self, eotm):
    self.__eot_marker = int.from_bytes(eotm, byteorder = 'little')

  @property
  def tzx_major_version(self):
    return self.__tzx_major_version

  @tzx_major_version.setter
  def tzx_major_version(self, major_ver):
    self.__tzx_major_version = int.from_bytes(major_ver, byteorder = 'little')

  @property
  def tzx_minor_version(self):
    return self.__tzx_minor_version

  @tzx_minor_version.setter
  def tzx_minor_version(self, minor_ver):
    self.__tzx_minor_version = int.from_bytes(minor_ver, byteorder = 'little')

  @property
  def is_valid(self):
    return self.signature == 'ZXTape!' and self.end_of_text_marker == 0x1a

  def __str__(self):
    return "%s v%d.%d" % (self.signature, self.tzx_major_version, self.tzx_minor_version)


@tzx_block
class TZXStandardSpeedDataBlock(TZXBlock):
  BLOCK_ID = 0x10

  def __init__(self, fd):
    super(TZXStandardSpeedDataBlock, self).__init__(fd, [('pause', 2),
                                                         ('block_length', 2),
                                                         ('block_data', lambda: self.block_length)])

  @property
  def pause(self):
    return self.__pause

  @pause.setter
  def pause(self, p):
    self.__pause = int.from_bytes(p, byteorder = 'little')

  @property
  def block_length(self):
    return self.__block_length

  @block_length.setter
  def block_length(self, bl):
    self.__block_length_bytes = bl
    self.__block_length = int.from_bytes(bl, byteorder = 'little')

  @property
  def block_length_bytes(self):
    return self.__block_length_bytes

  @property
  def block_data(self):
    return self.__block_data

  @block_data.setter
  def block_data(self, bd):
    self.__block_data = bd


@tzx_block
class TZXTextDescription(TZXBlock):
  BLOCK_ID = 0x30

  def __init__(self, fd):
    super(TZXTextDescription, self).__init__(fd, [('length', 1),
                                                  ('description', lambda: self.length)])

  @property
  def length(self):
    return self.__length

  @length.setter
  def length(self, l):
    self.__length = int.from_bytes(l, byteorder = 'little')

  @property
  def description(self):
    return self.__description

  @description.setter
  def description(self, desc):
    self.__description = desc.decode('utf-8')


@tzx_block
class TZXMessageBlock(TZXBlock):
  BLOCK_ID = 0x32

  def __init__(self, fd):
    super(TZXMessageBlock, self).__init__(fd, [('time', 1),
                                               ('length', 1),
                                               ('message', lambda: self.length)])

  @property
  def time(self):
    return self.__time

  @time.setter
  def time(self, t):
    self.__time = int.from_bytes(t, byteorder = 'little')

  @property
  def length(self):
    return self.__length

  @length.setter
  def length(self, l):
    self.__length = int.from_bytes(l, byteorder = 'little')

  @property
  def message(self):
    return self.__message

  @message.setter
  def message(self, msg):
    self.__message = msg.decode('utf-8')


@tzx_block
class TZXHardwareTypeBlock(TZXBlock):
  BLOCK_ID = 0x33

  def __init__(self, fd):
    super(TZXHardwareTypeBlock, self).__init__(fd, [('number', 1),
                                                    ('hwinfo', lambda: self.number * 3)])

  @property
  def number(self):
    return self.__number

  @number.setter
  def number(self, n):
    self.__number = int.from_bytes(n, byteorder = 'little')

  @property
  def hwinfo(self):
    return self.__hwinfo

  @hwinfo.setter
  def hwinfo(self, hi):
    self.__hwinfo = hi


@tzx_block
class TZXCustomInfoBlock(TZXBlock):
  BLOCK_ID = 0x35

  def __init__(self, fd):
    super(TZXCustomInfoBlock, self).__init__(fd, [('identification', 10),
                                                  ('length', 4),
                                                  ('info', lambda: self.length)])

  @property
  def identification(self):
    return self.__identification

  @identification.setter
  def identification(self, i):
    self.__identification = i.decode('utf-8')

  @property
  def length(self):
    return self.__length

  @length.setter
  def length(self, l):
    self.__length = int.from_bytes(l, byteorder = 'little')

  @property
  def info(self):
    return self.__info

  @info.setter
  def info(self, i):
    self.__info = i


def tzx_parse(tzx_fd):
  hdr = TZXHeader(tzx_fd)
  if not hdr.is_valid:
    raise TZXFileNotValidError()

  blocks = [hdr]
  block_id = tzx_fd.read(1)
  while block_id:
    if block_id not in block_id_registry:
      raise TXZBlockUnsupportedException(int.from_bytes(block_id, byteorder = 'little'))
    klass = block_id_registry[block_id]
    block = klass(tzx_fd)
    blocks.append(block)
    block_id = tzx_fd.read(1)

  return blocks


def tzx_convert(tzx_file, tap_dir):
  with open(tzx_file, 'rb') as tzx_fd:
    tzx_blocks = tzx_parse(tzx_fd)
    tzx_data_blocks = list(filter(lambda blk: isinstance(blk, TZXStandardSpeedDataBlock),
                                  tzx_blocks))
    if len(tzx_data_blocks) % 2:
      raise TZXDataBlockIncorrectCountException("%d standard speed data blocks" % len(tzx_data_blocks))
    tzx_data_block_pairs = [(tzx_data_blocks[i], tzx_data_blocks[i+1]) \
                            for i in range(0, len(tzx_data_blocks) - 1, 2)]
    tap_names = dict()
    for tzx_hdr, tzx_data in tzx_data_block_pairs:
      tap_name = tzx_hdr.block_data[2:12].decode('utf-8').strip().upper()[:8]
      if tap_name in tap_names:
        tap_idx = tap_names[tap_name]
        tap_idx += 1
        tap_names[tap_name] = tap_idx
        tap_idx_s = "_%d" % tap_idx
        tap_name = tap_name[0:8 - len(tap_idx_s)] + tap_idx_s
      else:
        tap_names[tap_name] = 1
      tap_filename = re.sub(r'[\\/:\*"<>|?]', "_", tap_name + '.TAP')
      tap_pathname = os.path.join(tap_dir, tap_filename)
      with open(tap_pathname, 'wb') as tap_fd:
        tap_fd.write(tzx_hdr.block_length_bytes)
        tap_fd.write(tzx_hdr.block_data)
        tap_fd.write(tzx_data.block_length_bytes)
        tap_fd.write(tzx_data.block_data)


def tzx_to_tap(tzx_files, root_dir, force):
  for tzx_file in tzx_files:
    tap_dirname, _ = os.path.splitext(os.path.basename(tzx_file))
    tap_dirname = tap_dirname[:8].upper()
    tap_dir = os.path.realpath(os.path.join(root_dir, tap_dirname))
    if os.path.exists(tap_dir):
      if not force:
        print("%s: TAP directory [%s] exists" % (os.path.realpath(tzx_file), tap_dir),
              file = sys.stderr)
        return False
    else:
      os.mkdir(tap_dir)

    tzx_convert(tzx_file, tap_dir)
    

if __name__ == '__main__':
  import argparse

  __VERSION = "1.0.0"

  default_root_dir = os.path.realpath(".")

  parser = argparse.ArgumentParser(prog = "tzx2tap.py",
                                   description = "Converts a TZX files to TAP files for use with the Jester Ace (v%s)." % __VERSION)
  parser.add_argument('-f', '--force',
                      dest = 'force',
                      action = 'store_true',
                      help = 'Force conversion if TAP directory exists')
  parser.add_argument('-d', '--rootdir',
                      type = str,
                      dest = 'root_dir',
                      default = default_root_dir,
                      help = 'Directory to which the TAP directory structure will be written (default: %s)' % default_root_dir)
  parser.add_argument('tzx_file',
                      type = str,
                      nargs = '+',
                      default = '',
                      help = 'TZX file to convert')
  args = parser.parse_args()

  rc = tzx_to_tap(args.tzx_file, args.root_dir, args.force)
  sys.exit(not rc)
