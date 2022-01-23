#!/usr/bin/env python3
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
import argparse
import os
import sys


word_names = dict()


def get_word_name(file_name):
  global word_nanes
  word_name = os.path.splitext(os.path.basename(file_name))[0].upper()
  if word_name not in word_names:
    word_names[word_name] = 1
  else:
    word_names[word_name] += 1
    word_name = "%s%d" % (word_name, word_names[word_name])
  return word_name


def get_file_bytes(fn):
  with open(fn, 'rb') as f:
    return f.read()


def convert(file_names, code_word_name, is_decimal, is_executable, is_definer_output):
  bytes_word_name_pairs = map(lambda fn: (get_file_bytes(fn), get_word_name(fn)), file_names)
  if is_definer_output and not is_executable:
    print('DEFINER %s\nDOES>\n\tCALL\n;\n' % code_word_name)
  if not is_decimal:
    print('16 BASE C!\n')

  for bytes, word_name in bytes_word_name_pairs:
    if is_executable:
      print("CREATE %s " % word_name, end = '')
    else:
      print("%s %s " % (code_word_name, word_name), end = '')
    format = ('%d' if is_decimal else '%02X') + ' C,'
    code = ' '.join(map(lambda b: format  % b, bytes))
    print(code, end = '')
    if is_executable:
      print(" %s DUP 2- !" % word_name, end = '\n\n')
    else:
      print(end = '\n\n')

  if not is_decimal:
    print('DECIMAL\n')


if __name__ == '__main__':
  __VERSION = '1.0.0'

  code_word_default = 'CODE'
  
  parser = argparse.ArgumentParser(prog = "bin2foth.py",
                                   description = "Create Forth words from machine code binary files (v%s)." % __VERSION)
  parser.add_argument('-c', '--codeword',
                      type = str,
                      dest = 'code_word_name',
                      default = code_word_default,
                      help = 'The name of the DEFINER word used to execute the machine code (default: %s)' % code_word_default)
  parser.add_argument('-d', '--decimal',
                      action = 'store_true',
                      dest = 'is_decimal',
                      help = 'Output machine code in decimal, default is hexadecimal')
  parser.add_argument('-x', '--executable',
                      action = 'store_true',
                      dest = 'is_executable',
                      help = 'Create a word that is executable, ignores --codeword argument')
  parser.add_argument('-o', '--outputdefiner',
                      action = 'store_true',
                      dest = 'is_definer_output',
                      help = 'Output the DEFINER code word')
  parser.add_argument('bin_file',
                      nargs = '+',
                      type = str,
                      help = 'Z80 binary file')
  args = parser.parse_args()

  convert(args.bin_file, args.code_word_name, args.is_decimal, args.is_executable, args.is_definer_output)
