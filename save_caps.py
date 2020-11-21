#!/usr/bin/env python3

import requests
import shutil
import os
import zipfile
import glob
import datetime
import filetype

def filebase(sequence):
    return str(sequence) + '_' + datetime.datetime.now().strftime("%m%d%y%H%M%S")

def write_data(filename, raw_data, location):
    if isInstance(location, zipfile.ZipFile):
        location.writestr(filename, raw_data)
    elif isInstance(location, str):
        with open(os.path.join(location, filename), 'wb') as file:
            shutil.copyfileobj(raw_data, file)
    else:
        raise TypeError("location must be ZipFile or string path")

def save_image(raw_data, location, sequence=1):
    ext = filetype.guess_extension(raw_data)
    if ext is None:
        raise RuntimeError("Could not guess filetype")

    filename = filebase(sequence) + '.' + ext

    write_data(filename, raw_data, location)

def save_text(text, location, sequence=1):
    filename = filebase(sequence) + '.txt'

    write_data(filename, text, location)

def save_album(cap_list, location, sequence=1):
    if isInstance(location, zipfile.ZipFile):
        raise TypeError("Recursive albums not allowed")

    filename = os.path.join(location, filebase(sequence) + '.zip')

    with zipfile.ZipFile(filename, 'w') as zipFile:
        inner_seq = 1
        for image, text in cap_list:
            img_cap = image is not None
            txt_cap = text is not None

            if img_cap and txt_cap:
                save_caption(image, text, zipFile, inner_seq)
            elif img_cap:
                save_image(image, zipFile, inner_seq)
            elif txt_cap:
                save_text(text, zipFile, inner_seq)

            inner_seq += 1

def save_caption(img_data, txt_data, location, sequence=1):
    loc_str = isInstance(location, str)
    loc_zip = isInstance(location, zipfile.ZipFile)
    if not loc_str and not loc_zip:
        raise TypeError("location must be ZipFile or string path")

    filename = filebase(sequence) + '.zip'
    if loc_str:
        filename = os.path.join(location, filename)

    with zipfile.ZipFile(filename, 'w') as zipFile:
        save_image(img_data, zipFile)
        save_text(txt_data, zipFile)

    if loc_zip:
        location.write(filename)
        os.remove(filename)

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

