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


FORTH_WORDS = dict()


class Formatter(object):
  def __init__(self, max_line_length, fd = sys.stdout):
    self.__buffer = ""
    self.__max_line_length = max_line_length
    self.__fd = fd

  def add(self, string):
    v = str(string) + ' '
    #print("PRE APPEND %d" % (len(v) + len(self.__buffer)))
    if len(v) + len(self.__buffer) > self.__max_line_length:
      self.flush('\n')
    self.__buffer += v
    if '\n' in self.__buffer:
      self.flush()

  def flush(self, end = ''):
    print(self.__buffer, end = end, file = self.__fd)
    self.__buffer = ""

  def __enter__(self):
    return self

  def __exit__(self, exception_type, exception_value, exception_traceback):
    self.flush()


class Word(object):
  def __init__(self,
               name_field,
               name_length,
               word_length,
               word_exec_addr,
               code_addr_field,
               parameters,
               processor = None,
               new_idx = None):
    self.name = name_field
    self.exec_addr = word_exec_addr
    self.code_addr = code_addr_field
    self.parameters = parameters
    self.length = word_length
    self.__is_immediate = (name_length & 0x40) == 0x40
    self.__processor = processor
    self.__new_idx = new_idx if new_idx else lambda _, idx: idx + 2

  @property
  def has_processor(self):
    return self.__processor is not None

  @property
  def is_immediate(self):
    return self.__is_immediate

  def process(self, word_parameters, idx):
    return self.__processor(word_parameters, idx)

  def get_new_idx(self, word_parameters, idx):
    return self.__new_idx(word_parameters, idx)

  def __str__(self):
    return self.name

  def __repr__(self):
    return "<Word: %s, 0x%.4x, %s>" % (self.name, self.code_addr, self.parameters)


class InternalWord(Word):
  def __init__(self, name = None, processor = None, new_idx = None):
    super(InternalWord, self).__init__(name, 0, 0, None, None, None, processor, new_idx)


class DefinitionWord(InternalWord):
  def __init__(self, definition):
    super(DefinitionWord, self).__init__()
    self.__definition = definition

  def definition(self, word_name, word_addr, word_parameters):
    return self.__definition(word_name, word_addr, word_parameters)


# Words that don't need a processor
for addr, word_name in [(0x0099, "QUIT"), (0x00ab, "ABORT"), (0x0460, "HERE"), (0x0473, "CONTEXT"),
                        (0x0480, "CURRENT"), (0x048a, "BASE"), (0x0499, "PAD"), (0x4b6, "\n;\n"),
                        (0x0506, "LINE"), (0x058c, "QUERY"), (0x0578, "RETYPE"), (0x05ab, "WORD"),
                        (0x062d, "VLIST"), (0x063d, "FIND"), (0x069a, "EXECUTE"), (0x098d, "<#"),
                        (0x09f7, "#"), (0x06a9, "NUMBER"), (0x078a, "CONVERT"), (0x0818, "VIS"),
                        (0x0828, "INVIS"), (0x0837, "FAST"), (0x0846, "SLOW"), (0x086b, "DUP"),
                        (0x0879, "DROP"), (0x0885, "SWAP"), (0x0896, "C@"), (0x08a5, "C!"),
                        (0x08b3, "@"), (0x08c1, "!"), (0x08d2, ">R"), (0x08df, "R>"),
                        (0x08ee, "?DUP"), (0x08ff, "ROT"), (0x0912, "OVER"), (0x0925, "PICK"),
                        (0x0933, "ROLL"), (0x096e, "TYPE"), (0x098D, "<#"), (0x099c, "#>"),
                        (0x0a4a, "SIGN"), (0x09b3, "."), (0x09d0, "U."), (0x09e1, "#S"),
                        (0x09f7, "#"), (0x0a1d, "CLS"), (0x0a5c, "HOLD"), (0x0a73, "SPACE"),
                        (0x0a83, "SPACES"), (0x0a95, "CR"), (0x0aa3, "EMIT"), (0x0aaf, "F."),
                        (0x0b19, "AT"), (0x0b4a, "PLOT"), (0x0b98, "BEEP"), (0x0bdb, "INKEY"),
                        (0x0beb, "IN"), (0x0bfd, "OUT"), (0x0c0d, "ABS"), (0x0c1a, "0="),
                        (0x0c2e, "0<"), (0x0c3a, "0>"), (0x0c4a, "="), (0x0c56, ">"),
                        (0x0c65, "<"), (0x0c72, "U<"), (0x0c83, "D<"), (0x0ca8, "U*"),
                        (0x0d00, "/MOD"), (0x0d31, "*/MOD"), (0x0d51, "/"), (0x0d61, "MOD"),
                        (0x0d6d, "*"), (0x0d7a, "*/"), (0x0d8c, "U/MOD"), (0x0da9, "NEGATE"),
                        (0x0dba, "DNEGATE"), (0x0dd2, "+"), (0x0de1, "-"), (0x0dee, "D+"),
                        (0x0e09, "1+"), (0x0e13, "2+"), (0x0e1f, "1-"), (0x0e29, "2-"),
                        (0x0e36, "OR"), (0x0e4b, "AND"), (0x0e60, "XOR"), (0x0e75, "MAX"),
                        (0x0e87, "MIN"), (0x0ea3, "DECIMAL"), (0x0ed0, "CREATE"),
                        (0x0f4e, ","), (0x0f5f, "C,"), (0x0f76, "ALLOT"),
                        (0x0fcf, "VARIABLE"), (0x0fe2, "CONSTANT"), (0x10a7, "CALL"),
                        (0x117d, "VOCABULARY"), (0x11ab, "DEFINITIONS"), (0x12e9, "I"),
                        (0x12f7, "I'"), (0x1302, "J"), (0x1316, "LEAVE"),
                        (0x12a4, "\nTHEN\n"), (0x129f, "\nBEGIN\n"),
                        (0x1323, "\nDO\n"),
                        (0x1361, "("), (0x13f0, "EXIT"),
                        (0x13fd, "REDEFINE"), (0x1638, "FORGET"), (0x165e, "EDIT"), (0x1670, "LIST"),
                        (0x1934, "SAVE"), (0x1944, "BSAVE"), (0x1954, "BLOAD"), (0x1967, "VERIFY"),
                        (0x1979, "BVERIFY"), (0x198a, "LOAD"), (0x1ba4, "F-"), (0x1bb1, "F+"),
                        (0x1c4b, "F*"), (0x1c7b, "F/"), (0x1d0f, "FNEGATE"), (0x1d22, "INT"),
                        (0x1d59, "UFLOAT"), (0x3c4a, "FORTH")]:
  FORTH_WORDS[addr] = InternalWord(word_name)

# Definition words
FORTH_WORDS[0x0ec3] = DefinitionWord(lambda wn, _, wp: (": %s" % wn, 0))
FORTH_WORDS[0x0fec] = DefinitionWord(lambda wn, _, wp: ("CREATE %s %d ALLOT" % (wn, len(wp)),
                                                                  len(wp)) if len(wp) > 152 else \
                                     ("( May be CREATE %s %d ALLOT )\nCREATE %s %s" % \
                                      (wn, len(wp), wn, ' '.join(map(lambda b: '%d c,' % b, wp))), len(wp)))
FORTH_WORDS[0x0ff0] = DefinitionWord(lambda wn, _, wp: ("%d VARIABLE %s" % (int.from_bytes(wp[0 : 2], "little"), wn), len(wp)))
FORTH_WORDS[0x0ff5] = DefinitionWord(lambda wn, _, wp: ("%d CONSTANT %s" % (int.from_bytes(wp[0 : 2], "little") , wn), len(wp)))
def definer_definition(word_name, _, word_parameters):
  def_word = DefinitionWord(lambda wn, _, wp: ('%s %s %s' % (word_name, wn, ' '.join(map(lambda b: '%d c,' % b, wp))), len(wp)))
  FORTH_WORDS[int.from_bytes(word_parameters[0 : 2], "little")] = def_word
  return ("DEFINER %s" % word_name, 2)
FORTH_WORDS[0x1085] = DefinitionWord(definer_definition)
def compiler_definition(word_name, word_addr, word_parameters):
  first_runs_word_addr = int.from_bytes(word_parameters[0 : 2], "little")
  offset = first_runs_word_addr - (word_addr + len(word_name) + 10)
  no_words = word_parameters[offset]
  return ("%d COMPILER %s" % (no_words, word_name), 2)
FORTH_WORDS[0x1108] = DefinitionWord(compiler_definition)

def char_processor(b):
  if (b >= 0x01 and b <= 0x0c) or (b >= 0x0e and b <= 0x0f) or \
     (b >= 0x19 and b <= 0x1f) or (b >= 0x80 and b <= 0x8f) or \
     (b >= 0x98 and b <= 0x9f):
    return ''
  if (b >= 0x10 and b <= 0x17) or (b >= 0x90 and b <= 0x97):
    return "_GR(0x%x)" % b
  if b & 0x80 == 0x80:
    return "_INV(%c)" % (b & 0x7f)
  else:
    return "%c" % (b & 0x7f)

# Stack next 16 bit word
FORTH_WORDS[0x1011] = InternalWord(processor = lambda wp, idx: int.from_bytes(wp[idx + 2 : idx + 4], "little"),
                                   new_idx = lambda p, idx: idx + 4)
FORTH_WORDS[0x104b] = InternalWord("ASCII",
                                   lambda p, idx: char_processor(p[idx + 2]),
                                   lambda p, idx: idx + 3)
# Floating point numbers
def floating_point_processor(word_parameters, idx):
  high_nibble = lambda b: (b & 0xf0) >> 4
  low_nibble = lambda b: b & 0x0f
  one = word_parameters[idx + 2 : idx + 4]
  two = word_parameters[idx + 4 : idx + 6]
  negative_char = '-' if (two[1] & 0x80) == 0x80 else ''
  exp = (two[1] & 0x7f) - 0x41
  exp_str = "e%d" % exp if exp != 0 else ''
  fp = float("%s%d.%d%d%d%d%d%s" % (negative_char,
                                    high_nibble(two[0]), low_nibble(two[0]),
                                    high_nibble(one[1]), low_nibble(one[1]),
                                    high_nibble(one[0]), low_nibble(one[0]),
                                    exp_str))
  return str(fp)
FORTH_WORDS[0x1064] = InternalWord(processor = floating_point_processor, new_idx = lambda p, idx: idx + 6)
FORTH_WORDS[0x10e8] = InternalWord("DOES>\n", new_idx = lambda p, idx: idx + 7)
FORTH_WORDS[0x1140] = InternalWord("\nRUNS>\n",new_idx = lambda p, idx: idx + 7)
FORTH_WORDS[0x1271] = InternalWord("\nELSE\n", new_idx = lambda p, idx: idx + 4)
FORTH_WORDS[0x1276] = InternalWord("REPEAT\n", new_idx = lambda p, idx: idx + 4)
FORTH_WORDS[0x1283] = InternalWord("IF\n", new_idx = lambda p, idx: idx + 4)
FORTH_WORDS[0x1288] = InternalWord("\nWHILE\n", new_idx = lambda p, idx: idx + 4)
FORTH_WORDS[0x128d] = InternalWord("\nUNTIL\n", new_idx = lambda p, idx: idx + 4)
FORTH_WORDS[0x1332] = InternalWord("\nLOOP\n", new_idx = lambda p, idx: idx + 4)
FORTH_WORDS[0x133c] = InternalWord("\n+LOOP\n", new_idx = lambda p, idx: idx + 4)
def comment_processor(word_parameters, idx):
  comment_length = int.from_bytes(word_parameters[idx + 2 : idx + 4], "little")
  comment_bytes = word_parameters[idx + 4 : idx + 4 + comment_length]
  comment_string = functools.reduce(lambda acc, b: acc + ("%c" % (b & 0x7f)), comment_bytes, "")
  return "( %s )\n" % comment_string
FORTH_WORDS[0x1379] = InternalWord(processor = comment_processor,
                                   new_idx = lambda p, idx: idx + 4 + int.from_bytes(p[idx + 2 : idx + 4], "little"))
def string_processor(word_parameters, idx):
  string_length = int.from_bytes(word_parameters[idx + 2 : idx + 4], "little")
  string_bytes = word_parameters[idx + 4 : idx + 4 + string_length]
  string = functools.reduce(lambda acc, b: acc + char_processor(b), string_bytes, "")
  return string + '"'
FORTH_WORDS[0x1396] = InternalWord('."',
                                   string_processor,
                                   lambda p, idx: idx + 4 + int.from_bytes(p[idx + 2 : idx + 4], "little"))


class BlockDataExhausted(Exception):
  pass


class BlockDataCorruption(Exception):
  pass


class BlockDataNotSupportedType(Exception):
  pass


class TapBlock(object):
  def __init__(self, tap_file):
    block_length_bytes = tap_file.read(2)
    self.__block_length = int.from_bytes(block_length_bytes, "little")
    self._data = tap_file.read(self.__block_length)
    if not self._data or len(self._data) != self.__block_length:
      raise BlockDataExhausted
    self._checksum = functools.reduce(lambda acc, b: acc ^ b, self._data[1:-1], 0)
    if self._checksum != self._data[-1]:
      raise BlockDataCorruption("Block checksum 0x%x, expected 0x%x" % (self._data[-1], self._checksum))
    self.__origin = int.from_bytes(self._data[14:16], "little")

  @property
  def origin(self):
    return self.__origin

  @property
  def program_type(self):
    return self.__program_type

  @property
  def length(self):
    return self.__block_length


class HeaderBlock(TapBlock):
  def __init__(self, tap_file):
    super(HeaderBlock, self).__init__(tap_file)
    if self._data[1] != 0x00:
      raise BlockDataNotSupportedType("Unsupported program type [0x%x]" % self._data[1])


class DataBlock(TapBlock):
  def __init__(self, tap_file):
    super(DataBlock, self).__init__(tap_file)

  def decompile(self, origin, formatter = None):
    words = list()
    idx = 1
    while idx < len(self._data) - 1:
      # Extract name
      name = ''
      b = self._data[idx]
      while True:
        idx += 1
        name += '%c' % (b & 0x7f)
        if b >= 128:
          break
        b = self._data[idx]
      # Word length
      word_length = int.from_bytes(self._data[idx : idx + 2], "little")
      idx += 2
      word_exec_addr = origin + idx + 1
      # Previous word
      link_addr = int.from_bytes(self._data[idx : idx + 2], "little")
      idx += 2
      word_name_length = self._data[idx]
      idx += 1
      code_addr_field = int.from_bytes(self._data[idx : idx + 2], "little")
      idx += 2
      parameters = self._data[idx : idx + (word_length - 7)]
      idx += (word_length - 7)
      word = Word(name, word_name_length, word_length, word_exec_addr + 1, code_addr_field, parameters)
      FORTH_WORDS[word.exec_addr] = word
      words.append(word)

    with formatter:
      addr = origin
      for word in words:
        idx = 0
        parameters = word.parameters

        try:
          code_word = FORTH_WORDS[word.code_addr]
        except KeyError as ex:
          raise KeyError("Unknown word 0x%.4x at offset %d" % (word.code_addr, addr - origin))
        assert isinstance(code_word, DefinitionWord) == True, "Word [%s] is not a defintion" % code_word
        definition, idx = code_word.definition(word.name, addr, word.parameters)
        formatter.add("\n%s\n" % definition)

        while idx < len(word.parameters):
          command = int.from_bytes(parameters[idx : idx + 2], "little")
          try:
            command_word = FORTH_WORDS[command]
          except KeyError as ex:
            raise KeyError("Unknown word 0x%.4x in word [%s], word offset %d, at parameter offset %d" % \
                           (command, word.name, addr - origin, idx))
          if command_word.name:
            formatter.add(command_word.name)
          if command_word.has_processor:
            thing = command_word.process(word.parameters, idx)
            formatter.add(thing)
          idx = command_word.get_new_idx(word.parameters, idx)

        if word.is_immediate and definition.startswith(':'):
          formatter.add("IMMEDIATE\n")

        addr += word.length + len(word.name)


def decompile(directory, force, tap_files, max_line_size):
  if not os.path.exists(directory):
    print("Directory [%s] does not exist" % directory)
    sys.exit(1)

  for tap_file in tap_files:
    with open(tap_file, "rb") as forth_tap_fd:
      hdr = HeaderBlock(forth_tap_fd)
      data = DataBlock(forth_tap_fd)
      forth_name = os.path.splitext(os.path.basename(tap_file))[0].lower()
      forth_filename = os.path.join(directory, forth_name + '.fs')
      if not force and os.path.exists(forth_filename):
        print("Forth file [%s] exists. Ignoring [%s]..." % (forth_filename, tap_file), file = sys.stderr)
        continue
      with open(forth_filename, "w") as forth_fd:
        data.decompile(hdr.origin, Formatter(max_line_size, forth_fd))


if __name__ == '__main__':
  import argparse

  __VERSION = "1.0.0"

  default_tap_name = "exec"
  default_tap_dir = os.path.curdir
  default_max_line_size = 80

  parser = argparse.ArgumentParser(prog = "tap2forth.py",
                                   description = "Decompile a Forth TAP file (v%s)." % __VERSION)
  parser.add_argument('-d', '--directory',
                      type = str,
                      dest = 'directory',
                      default = default_tap_dir,
                      help = 'Directory to which Forth files are written (default: %s)' % default_tap_dir)
  parser.add_argument('-f', '--force',
                      dest = 'force',
                      action = 'store_true',
                      help = 'Overwrite generated TAP file if it exists')
  parser.add_argument('-m', '--maxlinesize',
                      type = int,
                      dest = 'max_line_size',
                      default = default_max_line_size,
                      help = 'Maximum number of character per Forth line (default: %d)' % default_max_line_size)
  parser.add_argument('tap_file',
                      nargs = '+',
                      type = str,
                      help = 'Command to autorun')
  args = parser.parse_args()

  decompile(os.path.realpath(args.directory), args.force, args.tap_file, args.max_line_size)
