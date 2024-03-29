# Jester Ace Utilities and Firmware

Jester Ace is the micro SD Card reader for the [Tynemouth Software](http://www.tynemouthsoftware.co.uk/) Minstrel 4th. This repository makes available utilities and firmware updates for the Jester Ace.

## Using the Jester Ace with existing TZX Files

The [Jupiter Ace Archive](https://www.jupiter-ace.co.uk/) has a large collection of software for the Jupiter Ace/Minstrel 4th in TZX format. This resource can be used with the Jester Ace by using the `tzx2tap.py` utility available here. This utility converts TZX files, writing TAP files into separate directories associated with each TZX file specified. All generated directory and file names will be compatible with the SD card file system. They can be copied directly to your SD card. The name of the generated directory is the first 8 uppercased characters of the TZX filename. Generated TAP files will have filenames as the first 8 uppercased characters from the filename in the header block stored in the TZX file. Separate TAP files will be generated for each program stored in the TZX file.

### TZX File Conversion Example

[Fire One](https://www.jupiter-ace.co.uk/downloads/software/allowed/FireOne-tzx-091.zip) is a multi-program TZX file containing a game that is to be loaded in two parts. Steps for use with the Jester Ace:

1. Unpack the ZIP file:

```
unzip FireOne-tzx-091.zip
```

2. Convert TZX to TAP file

```
tzx2tap.py FireOne-091.tzx
```

This produces two files: `FIRE.TAP` and `ONE.TAP` in a directory called `FIREONE-`. Copy the `FIREONE-` directory to your SD card, and follow the game's [loading instructions](https://www.jupiter-ace.co.uk/sw_nine_games_fire_one.html).

## Using the Jester Ace with existing TAP Files

You may have got Jupiter Ace compatible TAP files from an emulator. These files can be used with the Jester Ace providing they contain only one program. Use the `tapls.py` to ascertain the number of programs in your TAP file. If more than one program, then use the `tapsplit.py` utility to split the TAP file into its individual programs. TAP files will be generated for each program in the conglomerate TAP file. A TAP file's filename will be the first 8 uppercased characters of the filename stored in the TAP header block of each program.

### TAP file spliting example

Spliting the Fire One TAP file:

```
tapsplit.py FireOne.tap
```

This will generate two files: `FIRE.TAP` and `ONE.TAP` in a directory called `FIREONE`. Copy the directory to the SD card used with the Jester Ace.

## Using Jester Ace TAP files with Emulators

The TAP files created with Jester Ace can be used with Jupiter Ace emulators. If your emulator supports the TAP file format the Jester Ace TAP files can be used as is. They can also be concatenated to create multi-program TAP files. Otherwise, it is likely that your emulator supports the TZX format. Jester Ace TAP files can be converted to TZX using `tap2tzx.py`.

### TAP to TZX Conversion Example

Using the Fire One TAP files as an example, run the `tap2tzx.py` to convert to TZX format:

```
tap2tzx.py -o FIREONE.TZX FIRE.TAP ONE.TAP
```

Use the `FIREONE.TZX` file with your emulator.

## List TAP file contents

The contents of a TAP file can be listed with the `tapls.py` utility. To list the `FireOne.tap` file, for example:

```
tapls.py FireOne.tap
```

You can specify as many TAP files as you require.

## Auto-run TAP files

Using programs and playing games on the Minstrel 4th can be a bit tricky if you don't know, or if you've forgotten how to load and run them. Even if programs do not require a multi-step loading procedure, remembering the run instructions is difficult since there is consistent word used to run Forth programs. Machine code programs can be located anywhere in memory. So we must remember which memory location to call to start the program.

The `tapautorun.py` script allows you to generate a TAP file that will automatically load and run a Forth or machine code program. The TAP file is loaded in the same way no matter which program to auto-run. The limitation is that the resultant command given to this script is no longer than 31 characters.

### Auto-run example for Ace Star

Assuming the TZX file has been converted to a TAP file called `astar.tap`, from the [Ace Star](https://www.jupiter-ace.co.uk/sw_dstar.html) ZIP file, an auto-run TAP file can be made with:

```
tapautorun.py 0 0 bload astar 16384 call
```

Move the `exec.tap` file to the same directory as `astar.tap` is located. To auto-run Ace Star type:

```
0 0 bload exec
```

### Auto-run example for Firebird

Convert the `Firebird-108.tzx` file, from the [Firebird](https://www.jupiter-ace.co.uk/sw_Firebird_VoyagerSoftware.html) ZIP file, to `firebird.tap`. Create an auto-run TAP file with:

```
tapautorun.py load firebird run
```

Move the generated `exec.tap` to the same location of the `firebird.tap` file. To auto-run Firebird type:

```
0 0 bload exec
```

## Covert TAP files to Forth Source Code

The Forth TAP files written by the Jester Ace can be converted to Forth source code files using `tap2forth.py`.

### Forth Source Code from Firebird

The following command line will write the Forth source code to a file called `firebird.fs`.

```
tap2forth.py firebird.tap
```

## Create Forth Words from Machine Code Binary Files

The Jupiter Ace maunal (Chapter 25) shows users how to encapsulate machine code in Forth words. The tool `bin2forth.py` allows you to use the output of your favourite Z80 assembler and create Forth words using this machine code. Your assembler is required to output a raw binary file of the assembled Z80 code. Assuming you have a raw binary file called `findword.bin`, using the following command line:

```
bin2forth.py -o findword.bin
```

will generate a Forth word called `FINDWORD` using hexadecimal for the machine code bytes:

```forth
DEFINER CODE
DOES>
	CALL
;

16 BASE C!

CODE FINDWORD DF C, AF C, 47 C, 1A C, 4F C, 13 C, 2A C, ...  C3 C, 8A C, 06 C,

DECIMAL
```

It is also possible to use the `CREATE` Forth word to create executable machine code. The `bin2forth.py` tool can generate these words using the following command line:

```
bin2forth.py -x findword.bin
```

This generates the following:

```forth
16 BASE C!

CREATE FINDWORD DF C, AF C, 47 C, 1A C, 4F C, 13 C, 2A C, ... C3 C, 8A C, 06 C, FINDWORD DUP 2- !

DECIMAL
```
