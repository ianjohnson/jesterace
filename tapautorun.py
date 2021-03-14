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


class TapBlock(object):
  def __init__(self):
    self._data = bytearray()

  @property
  def checksum(self):
    return bytes([functools.reduce(lambda acc, b: acc ^ b, self._data[1:], 0)])

  @property
  def length_bytes(self):
    return bytearray.fromhex('{0:0{1}x}'.format(len(self._data), 4))

  def write_data(self, fd):
    block_length = self.length_bytes
    fd.write(bytes([block_length[1], block_length[0]]))
    fd.write(self._data)


class HeaderTapBlock(TapBlock):
  def __init__(self, name):
    super(HeaderTapBlock, self).__init__()
    self._data += bytes([0x00, 0x20])
    self._data += name.ljust(10).encode('utf-8')
    self._data += bytes([0x00, 0x00])
    self._data += bytes([0xe0, 0x22])
    self._data += bytes([0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20])

  def write_data(self, fd, data_block):
    data_block_length = bytearray.fromhex('{0:0{1}x}'.format(data_block.content_length, 4))
    self._data[12] = data_block_length[1]
    self._data[13] = data_block_length[0]
    self._data += self.checksum
    super(HeaderTapBlock, self).write_data(fd)
    

class DataTapBlock(TapBlock):
  def __init__(self, command):
    super(DataTapBlock, self).__init__()
    self._data += bytes([0xff, 0x00])
    self._data += command.encode('utf-8')
    self._data += self.checksum

  @property
  def content_length(self):
    return len(self._data) - 2
    

def autorun(tap_name, tap_dir, force, command):
  if not os.path.exists(tap_dir):
    print("Directory [%s] does not exist" % tap_dir, file = sys.stderr)
    sys.exit(1)

  tap_filename = os.path.join(tap_dir, "%s.tap" % tap_name)
  if os.path.exists(tap_filename) and not force:
    print("TAP file [%s] exists" % tap_filename, file = sys.stderr)
    sys.exit(1)

  if len(command) > 31:
    print("Command, of length %d, [%s] is too long, 31 characters maximum" % (len(command), command))
    sys.exit(1)

  hdr_block = HeaderTapBlock(tap_name)
  data_block = DataTapBlock(command)

  with open(tap_filename, 'wb') as tap_fd:
    hdr_block.write_data(tap_fd, data_block)
    data_block.write_data(tap_fd)


if __name__ == '__main__':
  import argparse

  __VERSION = "1.0.0"

  default_tap_name = "exec"
  default_tap_dir = os.path.curdir

  parser = argparse.ArgumentParser(prog = "tapautorun.py",
                                   description = "Create autorun TAP file (v%s)." % __VERSION)
  parser.add_argument('-t', '--tapname',
                      type = str,
                      dest = 'tap_name',
                      default = default_tap_name,
                      help = 'Name of the generated TAP file (default: %s)' % default_tap_name)
  parser.add_argument('-d', '--directory',
                      type = str,
                      dest = 'tap_dir',
                      default = default_tap_dir,
                      help = 'Name of the generated TAP file (default: %s)' % default_tap_dir)
  parser.add_argument('-f', '--force',
                      dest = 'force',
                      action = 'store_true',
                      help = 'Overwrite generated TAP file if it exists')
  parser.add_argument('command',
                      nargs = '+',
                      type = str,
                      help = 'Command to autorun')
  args = parser.parse_args()

  autorun(args.tap_name, args.tap_dir, args.force, ' '.join(args.command))
          
