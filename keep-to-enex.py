#!/usr/bin/env python3

# originally created and posted by user dgc on
# https://discussion.evernote.com/topic/97201-how-to-transfer-all-the-notes-from-google-keep-to-evernote/
# Modified by user charlescanato https://gitlab.com/charlescanato/google-keep-to-evernote-converter
# Modified by gokhan mete erturk to enable bulk operation of html files without any parameters and
# solves the character set problems on Windows
# Modified by Leonard777 to add importing of image data.

# until now, Google Takeout for Keep does NOT export:
# - correct order of lists notes (non-checked first, checked last)
# - list items indentation

import argparse
import sys
import re
import parsedatetime as pdt
import time
import glob
import hashlib
import base64
import os

cal = pdt.Calendar()

r1 = re.compile('<li class="listitem checked"><span class="bullet">&#9745;</span>.*?<span class="text">(.*?)</span>.*?</li>')
r2 = re.compile('<li class="listitem"><span class="bullet">&#9744;</span>.*?<span class="text">(.*?)</span>.*?</li>')
r3 = re.compile('<span class="chip label"><span class="label-name">([^<]*)</span>[^<]*</span>')
# Use non-greedy expressions to support multiple image tags for each note
r4 = re.compile('<img alt="" src="data:(.*?);(.*?)\,(.*?)" />')  # Per immagini base64
r5 = re.compile('<div class="content">(.*)</div>')
r_img_file = re.compile(r'<img alt="" src="([^"]+)" />')  # Per immagini con src file

def readlineUntil(file, str):
    currLine = ""
    while str not in currLine:
        currLine = file.readline()
    return currLine

def readTagsFromChips(line):
    # line might still have chips
    if line.startswith('<div class="chips">'):
        return line + '\n'

def readImagesFromAttachment(line, note_dir):
    # Attachments need a name, so we will use the note title with a numeric suffix to make them unique.
    # Suffix number for multiple attachments of the same name
    attachmentNumber = 0
    result = ()

    # Primo: gestione immagini base64
    m = r4.search(line)
    while m:
        h = hashlib.md5(base64.b64decode(m.group(3).encode("utf-8")))
        # Import all images at 1024px wide. Not sure if we can determine original size from binary data or not.
        newContent = '\n<div><en-media type="' + m.group(1) + '" width="1024" hash="' + h.hexdigest() + '" /></div>'
        imageFormat = m.group(1).split('/')[1]
        newResource = '<resource><data encoding="' + m.group(2) + '">' + m.group(3) + '</data>\n<mime>' + m.group(1) + '</mime><resource-attributes><file-name>IMAGE_FILE_NAME_' + str(attachmentNumber) + '.' + imageFormat + '</file-name></resource-attributes></resource>\n'
        result += (newContent, newResource)
        attachmentNumber += 1
        line = line[m.end():]
        m = r4.search(line)

    # Secondo: gestione immagini con src file
    m_file = r_img_file.search(line)
    while m_file:
        img_file = os.path.join(note_dir, m_file.group(1))  # Percorso completo dell'immagine
        if os.path.exists(img_file):
            with open(img_file, "rb") as img_f:
                img_data = img_f.read()
                img_b64 = base64.b64encode(img_data).decode("utf-8")
                h = hashlib.md5(img_data)
                newContent = '\n<div><en-media type="image/jpeg" width="1024" hash="' + h.hexdigest() + '" /></div>'
                newResource = '<resource><data encoding="base64">' + img_b64 + '</data>\n<mime>image/jpeg</mime><resource-attributes><file-name>IMAGE_FILE_NAME_' + str(attachmentNumber) + '.jpg</file-name></resource-attributes></resource>\n'
                result += (newContent, newResource)
        else:
            print(f"Warning: File {img_file} not found.")
        attachmentNumber += 1
        line = line[m_file.end():]
        m_file = r_img_file.search(line)

    return result

def mungefile(fn):
    fp = open(fn, 'r', encoding="utf8")
    note_dir = os.path.dirname(fn)  # Cartella della nota per trovare le immagini
    
    title = readlineUntil(fp, "<title>").strip().replace('<title>', '').replace('</title>', '')
    
    readlineUntil(fp, "<body>")
    t = fp.readline()
    tags = ''
    resources = ''
    if '"archived"' in t:
        tags = '<tag>archived</tag>'
    fp.readline()  # </div> alone

    date = fp.readline().strip().replace('</div>', '')
    dt, flat = cal.parse(date)
    iso = time.strftime('%Y%m%dT%H%M%SZ', time.gmtime(time.mktime(dt)))

    fp.readline()  # extra title

    content = fp.readline()
    m = r5.search(content)
    if m:
        content = m.group(1)
    content = content.replace('<ul class="list">', '')

    for line in fp:
        line = line.strip()
        if line == '</div></body></html>':
            break
        # Chips contain the tags as well as dynamic content previews.. but we care mostly about the tags
        elif line.startswith('<div class="chips">'):
            content += readTagsFromChips(line)
        # Attachments contains the image data
        elif line.startswith('<div class="attachments">'):
            result = readImagesFromAttachment(line, note_dir)
            i = 0
            while i < len(result):
                if i+1 < len(result):
                    content += result[i]
                    # Use the note title without spaces as the image file name
                    currentResource = result[i+1].replace("IMAGE_FILE_NAME", title.replace(' ', ''))
                    resources += currentResource
                i += 2
        else:
            content += line + '\n'

    content = content.replace('<br>', '<br/>')
    content = content.replace('\n', '\0')

    while True:
        m = r1.search(content)
        if not m:
            break
        content = content[:m.start()] + '<en-todo checked="true"/>' + m.group(1) + '<br/>' + content[m.end():]

    while True:
        m = r2.search(content)
        if not m:
            break
        content = content[:m.start()] + '<en-todo checked="false"/>' + m.group(1) + '<br/>' + content[m.end():]

    content = content.replace('\0', '\n')

    # remove list close (if it was a list)
    lastUl = content.rfind('</ul>')
    if lastUl != -1:
        content = content[:lastUl] + content[lastUl+5:]

    m = r3.search(content)
    if m:
        content = content[:m.start()] + content[m.end():]
        tags = '<tag>' + m.group(1) + '</tag>'

    content = re.sub(r'class="[^"]*"', '', content)

    fp.close()
    
    print('''
  <note>
    <title>{title}</title>
    <content><![CDATA[<?xml version="1.0" encoding="UTF-8"?><!DOCTYPE en-note SYSTEM "http://xml.evernote.com/pub/enml2.dtd"><en-note style="word-wrap: break-word; -webkit-nbsp-mode: space; -webkit-line-break: after-white-space;">{content}</en-note>]]></content>
    <created>{iso}</created>
    <updated>{iso}</updated>
    {tags}
    <note-attributes>
      <latitude>0</latitude>
      <longitude>0</longitude>
      <source>google-keep</source>
      <reminder-order>0</reminder-order>
    </note-attributes>
    {resources}
  </note>
'''.format(**locals()), file=fxt)

parser = argparse.ArgumentParser(description="Convert Google Keep notes from .html to .enex for Evernote")
parser.add_argument('-o', '--output', help="The output file to write into. If not specified output goes to stdout.", default="sys.stdout")
parser.add_argument("htmlSource", help="The HTML file or list of files that should be converted", default="*.html", nargs="*")
args = parser.parse_args()

if args.output == "sys.stdout":
    fxt = sys.stdout
else:
    fxt = open(args.output, "w", encoding="utf8")

print('''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE en-export SYSTEM "http://xml.evernote.com/pub/evernote-export3.dtd">
<en-export export-date="20180502T065115Z" application="Evernote/Windows" version="6.x">''', file=fxt)

if len(args.htmlSource) > 1:
    print( args.htmlSource )
    for filename in args.htmlSource:
        print( filename )
        mungefile(filename)
else:
    mungefile(args.htmlSource[0])

print('''</en-export>''', file=fxt)
fxt.close()
