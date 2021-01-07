import shutil
import os
import zipfile
import datetime
import filetype

def filebase(sequence):
    return str(sequence) + '_' + datetime.datetime.now().strftime("%m%d%y%H%M%S")

def write_data(filename, raw_data, location):
    if isinstance(location, zipfile.ZipFile):
        location.writestr(filename, raw_data)
    elif isinstance(location, str):
        with open(os.path.join(location, filename), 'wb') as file:
            file.write(raw_data)
    else:
        raise TypeError("location must be ZipFile or string path")

def pack_image(raw_data, location, sequence=1):
    ext = filetype.guess_extension(raw_data)
    if ext is None:
        raise RuntimeError("Could not guess filetype")

    filename = filebase(sequence) + '.' + ext
    write_data(filename, raw_data, location)

def pack_text(text, location, sequence=1):
    filename = filebase(sequence) + '.txt'
    write_data(filename, text, location)

def pack_caption(img_data, txt_data, location, sequence=1):
    loc_str = isinstance(location, str)
    loc_zip = isinstance(location, zipfile.ZipFile)
    if not loc_str and not loc_zip:
        raise TypeError("location must be ZipFile or string path")

    filename = filebase(sequence) + '.zip'
    if loc_str:
        filename = os.path.join(location, filename)

    with zipfile.ZipFile(filename, 'w') as zipFile:
        pack_image(img_data, zipFile)
        pack_text(txt_data, zipFile)

    if loc_zip:
        location.write(filename)
        os.remove(filename)

def pack_album(cap_list, location, sequence=1):
    if isinstance(location, zipfile.ZipFile):
        raise TypeError("Recursive albums not allowed")

    filename = os.path.join(location, filebase(sequence) + '.zip')

    with zipfile.ZipFile(filename, 'w') as zipFile:
        for cap in cap_list:
            cap.pack(zipFile)


class CapData:
    def __init__(self, sequence):
        self.sequence = sequence
        self.img_data = None
        self.txt_data = None

    def append(self, image, text):
        self.img_data = image
        self.txt_data = text

    def pack(self, location):
        hasImg = self.img_data is not None
        hasTxt = self.txt_data is not None

        if not hasImg and not hasTxt:
            raise RuntimeError("Cannot pack null CapData")
        elif hasImg and hasTxt:
            pack_caption(self.img_data, self.txt_data, location, self.sequence)
        elif hasImg:
            pack_image(self.img_data, location, self.sequence)
        else:
            pack_text(self.txt_data, location, self.sequence)


class AlbumData:
    def __init__(self, sequence):
        self.caps = []
        self.sequence = sequence
        self.subseq = 0

    def append(self, image, text):
        cap = CapData(self.subseq)
        self.subseq += 1

        cap.img_data = image
        cap.txt_data = text

        self.caps.append(cap)

    def pack(self, location):
        pack_album(self.caps, location, self.sequence)

