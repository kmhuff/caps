#!/usr/bin/env python3

import requests
import pack_caps
import argparse
import glob
import os

def get_img(filepath):
    image_url = input("Enter/Paste the URL for your image. Or leave blank for latest downloaded image.\n")
    if image_url:
        data = requests.get(image_url)
        return data.content
    else:
        # get latest image in folder
        list_of_files = glob.glob(filepath + '/*')
        latest_file = max(list_of_files, key=os.path.getctime)
        confirmation = input("Use file " + latest_file + "? Y/N (Warning: this will delete the file)\n")
        if confirmation == 'Y':
            data = None
            with open(latest_file, "rb") as in_file:
                data = in_file.read()
            os.remove(latest_file)
            return data

def get_txt():
    print("Enter/Paste your content. Ctrl-D or Ctrl-Z ( windows ) to save it.")
    contents = []
    while True:
        try:
            line = input()
        except EOFError:
            break
        contents.append(line)

    output = '\n'.join(contents).strip()

    return bytes(output, "utf-8")


def load_image(capData, filepath):
    capData.append(get_img(filepath), None)
    return True

def load_text(capData, filepath=None):
    capData.append(None, get_txt())
    return True

def load_caption(capData, filepath):
    capData.append(get_img(filepath), get_txt())
    return True

def quit_loading(capData, filepath=None):
    print("    Quitting album load!")
    return False


def save_image(sequence, filepath):
    capData = pack_caps.CapData(sequence)
    load_image(capData, filepath)
    capData.pack(filepath)
    return True

def save_text(sequence, filepath):
    capData = pack_caps.CapData(sequence)
    load_text(capData)
    capData.pack(filepath)
    return True

def save_caption(sequence, filepath):
    capData = pack_caps.CapData(sequence)
    load_caption(capData, filepath)
    capData.pack(filepath)
    return True

albumInsts = {
    'I':load_image,
    'T':load_text,
    'C':load_caption,
    'Q':quit_loading
}

def save_album(sequence, filepath):
    albumData = pack_caps.AlbumData(sequence)

    keep_saving = True
    while keep_saving:
        try:
            instruction = input("    Saving [I]mage, [T]ext, or [C]aption? ([Q]uit)\n")
            keep_saving = albumInsts[instruction](albumData, filepath)
            print("    Done loading!")
        except Exception as e:
            print("    Error processing instruction " + instruction + " during album load:", e)

    albumData.pack(filepath)
    return True

def quit(sequence, filepath):
    print("Quitting!")
    return False


instructions = {
    "I":save_image,
    "T":save_text,
    "A":save_album,
    "C":save_caption,
    "Q":quit
}

def save_sequence(filepath):
    sequence = 1
    keep_saving = True
    while keep_saving:
        try:
            instruction = input("Saving [I]mage, [T]ext, [A]lbum, or [C]aption? ([Q]uit)\n")
            keep_saving = instructions[instruction](sequence, filepath)
            print("Done!")
        except Exception as e:
            print("Error processing instruction " + instruction + ":", e)

        sequence += 1

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Save collections of images and text.")
    parser.add_argument('--dirname', default="../Incoming", help='The directory the caps will be saved to')

    args = parser.parse_args()

    save_sequence(args.dirname)

