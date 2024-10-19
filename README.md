# Google Keep to Evernote notes converter

Cloned from https://gitlab.com/charlescanato/google-keep-to-evernote-converter by Charles Roberto Canato

Originally created and posted by user **dgc** on https://discussion.evernote.com/topic/97201-how-to-transfer-all-the-notes-from-google-keep-to-ever
note/

At the above URL, you can also find the motto and instructions for this script.

## Features
* Convert notes :)
* Includes embedded images  
    * Image types tested include .png and .jpg.
    * Handles multiple attachments
* Applies tags

## Usage

1. Make sure you have Python 3 installed (It requires `parsedatetime` module)
2. Download your Google Keep notes with Google Takeout
3. Extract the .HTMLs to a dir (Usually the dir is called `Keep`)
4. Run this script providing:  
    a. Optionally, pass "-o <output_file>.enex" (WITHOUT quotes). If not specified this script will write a file named "keep.enex" into the working directory  
    b. "\<dir>/*.html" as an argument (WITHOUT quotes). If not specified, this script will check for all .html files in the working directory  

Usage can also be printed by passing "-h" at the command line.

```
// Example with Keep directory

python3 keep-to-enex.py Keep/*.html

```

:+1: Tested ok under Windows, Mac and Linux

I've never tested this with more than 800 notes, but anyway this has worked for me.

I made this public 'cause I feel it might be useful for more people, but this is far from a beautiful code. I *might* modify it in case it can't help anyone in its current state.
