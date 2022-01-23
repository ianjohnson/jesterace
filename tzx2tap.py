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
import re
import os
import sys


block_id_registry = dict()


def tzx_block(klass):
  global block_id_registry
  block_id = (klass.BLOCK_ID).to_bytes(1, byteorder = 'little')
  block_id_registry[block_id] = klass
  return klass


class TZXFileException(Exception):
  def __init__(self, tzx_file):
    super(TZXFileException, self).__init__()
    self.tzx_file = os.path.realpath(tzx_file)


class TZXFileNotValidException(TZXFileException):
  def __str__(self):
    return "[%s] is not a valid TZX file" % self.tzx_file


class TXZBlockUnsupportedException(TZXFileException):
  def __init__(self, tzx_file, unsupported_block_id):
    super(TXZBlockUnsupportedException, self).__init__(tzx_file)
    self.unsupported_block_id = unsupported_block_id

  def __str__(self):
    return "[%s] contains an unsupported TZX block [ID = %.2X]" % \
      (self.tzx_file, self.unsupported_block_id)


class TZXDataBlockIncorrectCountException(TZXFileException):
  def __init__(self, tzx_file, no_blocks):
    super(TZXDataBlockIncorrectCountException, self).__init__(tzx_file)
    self.no_blocks = no_blocks

  def __str__(self):
    return "[%s] contains an unexpected number of standard speed data blocks [count = %d]" % \
      (self.tzx_file, self.no_blocks)

  
class TZXBlock(object):
  def __init__(self, fd, attributes):
    for attr_name, no_bytes_or_callable in attributes:
      if callable(no_bytes_or_callable):
        try:
          no_bytes_or_obj = no_bytes_or_callable(fd)
        except TypeError:
          no_bytes_or_obj = no_bytes_or_callable()
      else:
        no_bytes_or_obj = no_bytes_or_callable
      value = fd.read(no_bytes_or_obj) if isinstance(no_bytes_or_obj, int) else no_bytes_or_obj
      setattr(self, attr_name, value)


class TZXHeader(TZXBlock):
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
  BLOCK_ID = 0x31

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
class TZXArchiveInfoBlock(TZXBlock):
  BLOCK_ID = 0x32

  class ArchiveText(TZXBlock):
    def __init__(self, fd):
      super(TZXArchiveInfoBlock.ArchiveText, self).__init__(fd, [('identity', 1),
                                                                 ('length', 1),
                                                                 ('text', lambda: self.length)])

    @property
    def identity(self):
      return self.__identity

    @identity.setter
    def identity(self, i):
      self.__identity = int.from_bytes(i, byteorder = 'little')

    @property
    def length(self):
      return self.__length

    @length.setter
    def length(self, l):
      self.__length = int.from_bytes(l, byteorder = 'little')

    @property
    def text(self):
      return self.__text

    @text.setter
    def text(self, t):
      self.__text = t.decode('utf-8')

  def __init__(self, fd):
    super(TZXArchiveInfoBlock, self).__init__(fd, [('length', 2),
                                                   ('number_of_strings', 1),
                                                   ('text', lambda fd: list(map(lambda _: TZXArchiveInfoBlock.ArchiveText(fd), \
                                                                                range(0, self.number_of_strings))))])

  @property
  def length(self):
    return self.__length

  @length.setter
  def length(self, l):
    self.__length = int.from_bytes(l, byteorder = 'little')

  @property
  def number_of_strings(self):
    return self.__number_of_strings

  @number_of_strings.setter
  def number_of_strings(self, ns):
    self.__number_of_strings = int.from_bytes(ns, byteorder = 'little')

  @property
  def text(self):
    return self.__text

  @text.setter
  def text(self, t):
    self.__text = t


@tzx_block
class TZXHardwareTypeBlock(TZXBlock):
  BLOCK_ID = 0x33

  class HardwareInfo(TZXBlock):
    def __init__(self, fd):
      super(TZXHardwareTypeBlock.HardwareInfo, self).__init__(fd, [('type', 1),
                                                                   ('identifier', 1),
                                                                   ('information', 1)])

    @property
    def type(self):
      return self.__type

    @type.setter
    def type(self, t):
      self.__type = int.from_bytes(t, byteorder = 'little')

    @property
    def identifier(self):
      return self.__identifier

    @identifier.setter
    def identifier(self, i):
      self.__identifier = int.from_bytes(i, byteorder = 'little')

    @property
    def information(self):
      return self.__information

    @information.setter
    def information(self, i):
      self.__information = int.from_bytes(i, byteorder = 'little')

  def __init__(self, fd):
    super(TZXHardwareTypeBlock, self).__init__(fd, [('number_of_types', 1),
                                                    ('hardware_info', lambda fd: list(map(lambda _: TZXHardwareTypeBlock.HardwareInfo(fd), \
                                                                                          range(0, self.number_of_types))))])

  @property
  def number_of_types(self):
    return self.__number

  @number_of_types.setter
  def number_of_types(self, n):
    self.__number = int.from_bytes(n, byteorder = 'little')

  @property
  def hardware_info(self):
    return self.__hwinfo

  @hardware_info.setter
  def hardware_info(self, hi):
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


@tzx_block
class TZXGlueBlock(TZXBlock):
  BLOCK_ID = 0x5a

  def __init__(self, fd):
    super(TZXGlueBlock, self).__init__(fd, [('signature', 6),
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
    return self.signature == 'XTape!' and self.end_of_text_marker == 0x1a

  def __str__(self):
    return "%s v%d.%d" % (self.signature, self.tzx_major_version, self.tzx_minor_version)


def tzx_parse(tzx_fd):
  hdr = TZXHeader(tzx_fd)
  blocks = [hdr]
  block_id = tzx_fd.read(1)
  while block_id:
    if block_id in block_id_registry:
      klass = block_id_registry[block_id]
      block = klass(tzx_fd)
      blocks.append(block)
      block_id = tzx_fd.read(1)
    else:
      blocks.append(int.from_bytes(block_id, byteorder = 'little'))
      block_id = None

  return blocks


def tzx_convert(tzx_file, tap_dir):
  with open(tzx_file, 'rb') as tzx_fd:
    tzx_blocks = tzx_parse(tzx_fd)
    if not len(tzx_blocks) or not isinstance(tzx_blocks[0], TZXHeader) or not tzx_blocks[0].is_valid:
      raise TZXFileNotValidException(tzx_file)
    tzx_unsupported_blocks = list(filter(lambda blk: isinstance(blk, int), tzx_blocks))
    if len(tzx_unsupported_blocks):
      raise TXZBlockUnsupportedException(tzx_file, tzx_unsupported_blocks[0])
    tzx_data_blocks = list(filter(lambda blk: isinstance(blk, TZXStandardSpeedDataBlock),
                                  tzx_blocks))
    if len(tzx_data_blocks) % 2:
      raise TZXDataBlockIncorrectCountException(tzx_file, len(tzx_data_blocks))
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
      tap_filename = re.sub(r'[\\/:\*"<>|?\.]', "_", tap_name) + '.TAP'
      tap_pathname = os.path.join(tap_dir, tap_filename)
      print(os.path.basename(tzx_file), file = sys.stderr)
      print("  +--> Found header block of length %d bytes" % tzx_hdr.block_length, file = sys.stderr)
      print("  +--> Found data block of length %d bytes" % tzx_data.block_length, file = sys.stderr)
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

    try:
      tzx_convert(tzx_file, tap_dir)
    except TZXFileException as ex:
      os.rmdir(tap_dir)
      raise ex
    

if __name__ == '__main__':
  import argparse

  __VERSION = "2.0.0"

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
