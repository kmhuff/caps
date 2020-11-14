#!/usr/bin/env python3

import requests
import shutil
import os
import zipfile
import glob
import datetime
import filetype

def save_image(zip_file=None, filebase='saved'):
    image_url = input("Enter/Paste the URL for your image.\n")
    raw_filename = filebase + '.dat'

    data = requests.get(image_url, stream=True)
    data.raw.decode_content = True

    with open(raw_filename, 'wb') as f:
        shutil.copyfileobj(data.raw, f)

    ext = filetype.guess_extension(raw_filename)
    if ext is None:
        print("Filetype couldn't be detected, aborting")
        os.remove(raw_filename)
        return False

    filename = filebase + '.' + ext
    os.rename(raw_filename, filename)

    if zip_file is not None:
        zip_file.write(filename)
        os.remove(filename)

    return True

def save_text(zip_file=None, filebase='saved'):
    filename = filebase + '.txt'
    print("Enter/Paste your content. Ctrl-D or Ctrl-Z ( windows ) to save it.")
    contents = []
    while True:
        try:
            line = input()
        except EOFError:
            break
        contents.append(line)

    output = '\n'.join(contents).strip()

    if zip_file is None:
        with open(filename, 'w') as f:
            f.write(output)
    else:
        zip_file.writestr(filename, output)

    return True

def save_album(zip_file=None, filebase='saved'):
    filename = filebase + '.zip'
    if zip_file is not None:
        print("Cannot save album in archive.")
        return True

    with zipfile.ZipFile(filename, 'w') as file:
        save_sequence("Saving [I]mage, [T]ext, or [C]aption? ([Q]uit)\n", file, None, "    ")

    return True

def save_caption(zip_file=None, filebase='saved'):
    filename = filebase + '.zip'
    with zipfile.ZipFile(filename, 'w') as file:
        save_image(file)
        save_text(file)

    if zip_file is not None:
        zip_file.write(filename)
        os.remove(filename)

    return True
    
def quit(zip_file=None, filename=None):
    print("Quitting")
    return False

instructions = {
    "I":save_image,
    "T":save_text,
    "A":save_album,
    "C":save_caption,
    "Q":quit
}

def save_sequence(prompt, zip_file=None, post_save=None, indent=""):
    sequence = 1
    while True:
        instruction = input(indent + prompt)
        keep_saving = True
        filebase = str(sequence) + '_' + datetime.datetime.now().strftime("%m%d%y%H%M%S")
        try:
            keep_saving = instructions[instruction](zip_file, filebase)

            if post_save is not None:
                post_save(filebase)
    
            print(indent + "Done!")
        except Exception as e:
            print(indent + "Error processing instruction " + instruction + ": ", e)

        if not keep_saving:
            break

        sequence += 1

def post_save(filebase):
    names = glob.glob(filebase + '*')
    for name in names:
        shutil.move(name, '../Incoming/' + name)

if __name__ == "__main__":
    save_sequence("Saving [I]mage, [T]ext, [A]lbum, or [C]aption? ([Q]uit)\n", None, post_save)

