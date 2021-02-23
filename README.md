# Jester Ace Utilities and Firmware

Jester Ace is the micro SD Card reader for the [Tynemouth Software](http://www.tynemouthsoftware.co.uk/) Minstrel 4th. This repository makes available utilities and firmware updates for the Jester Ace.

## Using the Jester Ace with existing TZX Files

The [Jupiter Ace Archive](https://www.jupiter-ace.co.uk/) has a large collection of software for the Jupiter Ace/Minstrel 4th in TZX format. This resource can be used with the Jester Ace by using the [tzxtools](https://github.com/shred/tzxtools) suite and the utilities provided here.

Processing the TZX file can be done by:
  * Convert a TZX file to TAP format using `tzxtap`, and for multi-program TAP files,
  * Use `tapsplit.py` to split into individual TAP files.

The zxtools `tzxtap` sometimes does not convert TZX files properly, so your mileage may vary using this tool. If you have a familiarity with the TZX format some file editing can get it through the conversion process.

### TZX File Conversion Example

[Fire One](https://www.jupiter-ace.co.uk/downloads/software/allowed/FireOne-tzx-091.zip) is a multi-program TZX file containing a game that is to be loaded in two parts. Steps for use with the Jester Ace:

1. Unpack the ZIP file:

```
unzip FireOne-tzx-091.zip
```

2. Convert TZX to TAP file

```
tzxtap -o FireOne.tap FireOne-091.tzx
```

3. Split the TAP file

```
tapsplit.py FireOne.tap
```

This produces two files: `FIRE.TAP` and `ONE.TAP`. Copy these files to your SD card, and follow the game's [loading instructions](https://www.jupiter-ace.co.uk/sw_nine_games_fire_one.html).

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
