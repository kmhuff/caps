#!/usr/bin/env python3

import tkinter as tk
import tkinter.scrolledtext as ScrolledText
from tkinter import messagebox
import PIL
from PIL import Image
from PIL import ImageTk
from PIL import ImageFile
ImageFile.LOAD_TRUNCATED_IMAGES = True
import cv2
import os
import random
import zipfile
import numpy
import argparse
import filetype
import sys


# constants and enums
BEGIN = "BEGIN"


class ImageManager():
    def __init__(self, filename):
        self.image = Image.open(filename)
        self.animated = False
        try:
            self.image.seek(1)
            self.animated = True
            self.image.seek(0)
        except:
            self.animated = False

    def get_raw_frame(self):
        if self.animated:
            try:
                self.image.seek(self.image.tell() + 1)
            except:
                self.image.seek(0)

        # make an RGB copy of the image to return (gifs can't be opened in RGB)
        copy = Image.new("RGB", self.image.size, (255, 255, 255))
        copy.paste(self.image)
        return numpy.array(copy)

    def get_duration(self):
        try:
            if self.animated:
                return self.image.info['duration']
            else:
                return None
        except KeyError:
            return None

    def __del__(self):
        self.image.close()


class VideoManager():
    def __init__(self, filename):
        self.vcap = cv2.VideoCapture(filename)
        if self.vcap.isOpened() == False:
            raise ValueError("Unable to open video file", filename)

        # duration in miliseconds per frame
        self.framerate = None
        fps = self.vcap.get(cv2.CAP_PROP_FPS)
        if fps != 0:
            self.framerate = int(1 / (fps/1000))

    def get_raw_frame(self):
        ret, frame = self.vcap.read()

        if ret:
            return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        else:
            self.vcap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret, frame = self.vcap.read()
            if ret:
                return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            else:
                raise ValueError("Error with video stream")

    def get_duration(self):
        return self.framerate

    def __del__(self):
        if self.vcap.isOpened():
            self.vcap.release()


class MediaManager:
    def __init__(self, filename):
        file = filename

        self.scale = 1.0
        self.scrollX = 0
        self.scrollY = 0
        self.maxX = 0
        self.maxY = 0
        self.unscaledX = 0
        self.unscaledY = 0

        self.manager = None

        ext = filetype.guess_extension(file)
        if ext is None:
            print("Filetype of " + filename + " couldn't be detected, aborting")
            file = "blank.jpg"
            ext = "jpg"
            #os.remove(raw_filename)

        if ext in ['jfif', 'jpeg', 'jpg', 'JPG', 'png', 'webp']:
            self.manager = ImageManager(file)
        else:
            self.manager = VideoManager(file)

    def get_frame(self, winX, winY):
        img = self.manager.get_raw_frame();

        self.unscaledX = img.shape[1]
        self.unscaledY = img.shape[0]

        self.maxX = int(self.unscaledX * self.scale)
        self.maxY = int(self.unscaledY * self.scale)

        resized = cv2.resize(img, (self.maxX, self.maxY))
        sliced = resized[self.scrollY:self.scrollY+winY, self.scrollX:self.scrollX+winX]

        return sliced

    def get_duration(self):
        out = self.manager.get_duration()
        if out is None:
            return 15
        else:
            return out

    def scroll_vert(self, offset, winY):
        self.set_scrollY(self.scrollY + offset, winY)

    def scroll_hor(self, offset, winX):
        self.set_scrollX(self.scrollX + offset, winX)

    def set_scrollY(self, value, winY):
        if value < 0: 
            self.scrollY = 0
        elif value + winY > self.maxY:
            self.set_scrollY(self.maxY - winY, winY)
        else:
            self.scrollY = value

    def set_scrollX(self, value, winX):
        if value < 0: 
            self.scrollX = 0
        elif value + winX > self.maxX:
            self.set_scrollX(self.maxX - winX, winX)
        else:
            self.scrollX = value

    def zoom(self, offset, winX, winY):
        if not self.scale + offset <= 0:
            self.scale = self.scale + offset

            propY = self.scrollY / self.maxY
            propX = self.scrollX / self.maxX

            self.maxX = int(self.unscaledX * self.scale)
            self.maxY = int(self.unscaledY * self.scale)

            self.set_scrollY(int(propY * self.unscaledY * self.scale), winY)
            self.set_scrollX(int(propX * self.unscaledX * self.scale), winX)


class FileNavigator:
    def __init__(self, dirname, tmp_dir, resource_dir, filelist = None):
        self.tmp_dir = tmp_dir
        self.resource_dir = resource_dir

        if filelist is not None:
            self.files = filelist
        else:
            self.files = [os.path.join(dirname, f) for f in os.listdir(dirname) if os.path.isfile(os.path.join(dirname, f))]

        self.files.sort()
        self.idx = 0

        self.albumfile = None
        self.subfiles = []
        self.subIdx = 0

    def get_random_file(self):
        self.idx = random.randint(0, len(self.files) - 1)
        self.wipe_tmp()
        self.wipe_seq_data()
        return self.multiplex(self.files[self.idx])

    def get_file_from_name(self, filename):
        self.idx = self.files.index(filename)
        self.wipe_tmp()
        self.wipe_seq_data()
        return self.multiplex(self.files[self.idx])

    def get_first_file(self):
        self.idx = 0
        self.wipe_tmp()
        self.wipe_seq_data()
        return self.multiplex(self.files[self.idx])

    def get_next(self):
        self.idx = self.wrap_idx(self.idx+1, len(self.files))
        self.wipe_tmp()
        self.wipe_seq_data()
        return self.multiplex(self.files[self.idx])

    def get_prev(self):
        self.idx = self.wrap_idx(self.idx-1, len(self.files))
        self.wipe_tmp()
        self.wipe_seq_data()
        return self.multiplex(self.files[self.idx])

    def delete(self):
        os.remove(self.files[self.idx])
        self.files.pop(self.idx)
        self.idx = self.wrap_idx(self.idx, len(self.files))
        self.wipe_tmp()
        self.wipe_seq_data()
        return self.multiplex(self.files[self.idx])

    def get_next_seq(self):
        self.subIdx = self.wrap_idx(self.subIdx+1, len(self.subfiles))

        self.wipe_tmp()

        tmp_name = os.path.join(self.tmp_dir, self.subfiles[self.subIdx])
        with zipfile.ZipFile(self.albumfile) as zip:
            zip.extract(self.subfiles[self.subIdx], self.tmp_dir)

        return self.multiplex(tmp_name)

    def get_prev_seq(self):
        self.subIdx = self.wrap_idx(self.subIdx-1, len(self.subfiles))

        self.wipe_tmp()

        tmp_name = os.path.join(self.tmp_dir, self.subfiles[self.subIdx])
        with zipfile.ZipFile(self.albumfile) as zip:
            zip.extract(self.subfiles[self.subIdx], self.tmp_dir)

        return self.multiplex(tmp_name)

    def multiplex(self, filename):
        _,ext = os.path.splitext(filename)
        if ext == '.zip':
            with zipfile.ZipFile(filename) as zip:
                ziplist = sorted(zip.namelist())

                # reading caption
                nonimg = [f for f in ziplist if os.path.splitext(f)[1] == '.txt']
                img = [f for f in ziplist if os.path.splitext(f)[1] != '.txt']
                if len(nonimg) == 1 and len(img) == 1:
                    imgname = os.path.join(self.tmp_dir, img[0])
                    nonimgname = os.path.join(self.tmp_dir, nonimg[0])

                    zip.extract(nonimg[0], self.tmp_dir)
                    zip.extract(img[0], self.tmp_dir)

                    return imgname, nonimgname

                # reading album
                if self.albumfile is not None:
                    # We shouldn't have recursive albums
                    return os.path.join(self.resource_dir, 'blank.jpg'), os.path.join(self.resource_dir, 'album_error.txt')

                self.albumfile = filename
                self.subfiles = ziplist

                tmp_name = os.path.join(self.tmp_dir, self.subfiles[self.subIdx])
                zip.extract(self.subfiles[self.subIdx], self.tmp_dir)
                return self.multiplex(tmp_name)

        elif ext == '.txt':
            return os.path.join(self.resource_dir, 'blank.jpg'), filename
        else:
            return filename, os.path.join(self.resource_dir, 'empty.txt')

    def wipe_tmp(self):
        for file in os.listdir(self.tmp_dir):
            os.remove(os.path.join(self.tmp_dir, file))

    def wipe_seq_data(self):
        self.albumfile = None
        self.subfiles = []
        self.subIdx = 0

    def wrap_idx(self, idx, max_len):
        out_idx = idx
        if idx == max_len:
            out_idx = 0
        if idx == -1:
            out_idx = max_len - 1
        return out_idx

    def get_filename(self):
        return self.files[self.idx]

    def get_sub_filename_if_seq(self):
        if self.albumfile is not None:
            return self.subfiles[self.subIdx]
        else:
            return None

    def __del__(self):
        self.wipe_tmp()


class VideoPlayerApp:
    def __init__(self, root, dirname, filename, filelist = None):
        self.root = root

        m1 = tk.PanedWindow(root, borderwidth=16, sashrelief=tk.RAISED)
        m1.pack(fill=tk.BOTH, expand=True)
    
        self.imageLabel = tk.Label(m1, text="image")
        self.imageLabel.pack(fill=tk.BOTH, expand=True)
        m1.add(self.imageLabel)

        self.textBox = ScrolledText.ScrolledText(m1, wrap=tk.WORD, state=tk.DISABLED, font=("Sans Serif", 13))
        self.textBox.pack(fill=tk.BOTH, expand=True)
        m1.add(self.textBox)

        # update dimensions
        root.update()
        m1.paneconfigure(self.imageLabel, width=(2*m1.winfo_width()/3))

        source_dir = os.path.dirname(os.path.realpath(__file__))
        self.fileNav = FileNavigator(dirname, os.path.join(source_dir, "tmp"), os.path.join(source_dir, "resources"), filelist)

        # select first file and make a manager for it
        if filename is None:
            imgfile,txtfile = self.fileNav.get_random_file()
        elif filename == BEGIN:
            imgfile,txtfile = self.fileNav.get_first_file()
        else:
            imgfile,txtfile = self.fileNav.get_file_from_name(filename)

        self.media = MediaManager(imgfile)
        self.newText(txtfile)

        # register handlers
        root.bind("<Key>", self.onKey)

        # call update
        self.update()

    def get_filename(self):
        return self.fileNav.get_filename()

    def update(self):
        # Update image
        img = self.media.get_frame(self.imageLabel.winfo_width(), self.imageLabel.winfo_height())

        photoImg = ImageTk.PhotoImage(image=Image.fromarray(img))
        self.imageLabel.configure(image=photoImg)
        self.imageLabel.image = photoImg

        # Call update until we quit
        self.root.after(self.media.get_duration(), self.update)

    def newText(self, txtfile):
        text = "Filename: " + self.fileNav.get_filename() + "\n"

        opt_subfile_name = self.fileNav.get_sub_filename_if_seq()
        if opt_subfile_name is not None:
            text += "Subfile " + str(self.fileNav.subIdx) + ": " + opt_subfile_name + "\n"

        text += "\n"
        with open(txtfile, "r") as file:
            text += file.read()
        
        self.textBox.configure(state=tk.NORMAL)
        self.textBox.delete("1.0", tk.END)
        self.textBox.insert(tk.END, text)
        self.textBox.configure(state=tk.DISABLED)

    def onKey(self, event):
        if event.char == 'w':
            self.media.scroll_vert(-10, self.imageLabel.winfo_height())
        elif event.char == 's':
            self.media.scroll_vert(10, self.imageLabel.winfo_height())
        elif event.char == 'a':
            self.media.scroll_hor(-10, self.imageLabel.winfo_width())
        elif event.char == 'd':
            self.media.scroll_hor(10, self.imageLabel.winfo_width())
        elif event.char == 'r':
            self.media.zoom(0.1, self.imageLabel.winfo_width(), self.imageLabel.winfo_height())
        elif event.char == 'f':
            self.media.zoom(-0.1, self.imageLabel.winfo_width(), self.imageLabel.winfo_height())
        elif event.char == 'q':
            imgfile,txtfile = self.fileNav.get_prev()
            self.media = MediaManager(imgfile)
            self.newText(txtfile)
        elif event.char == 'e':
            imgfile,txtfile = self.fileNav.get_next()
            self.media = MediaManager(imgfile)
            self.newText(txtfile)
        elif event.char == 'z':
            imgfile,txtfile = self.fileNav.get_prev_seq()
            self.media = MediaManager(imgfile)
            self.newText(txtfile)
        elif event.char == 'c':
            imgfile,txtfile = self.fileNav.get_next_seq()
            self.media = MediaManager(imgfile)
            self.newText(txtfile)
        elif event.char == 'x':
            if messagebox.askokcancel("Warning", "Deleting " + self.fileNav.get_filename() + " is permanent. Proceed?"):
                imgfile,txtfile = self.fileNav.delete()
                self.media = MediaManager(imgfile)
                self.newText(txtfile)


def capViewerFromDir(dirname, startFilename):
    root = tk.Tk()
    root.title("Viewer")
    root.geometry("1400x900")

    app = VideoPlayerApp(root, dirname, startFilename)

    root.mainloop()

    return app


def capViewerFromList(filelist):
    root = tk.Tk()
    root.title("Viewer")
    root.geometry("1400x900")

    app = VideoPlayerApp(root, None, BEGIN, filelist)

    root.mainloop()

    return app


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="View collections of images and text.")
    parser.add_argument('--dirname', default=".", help='The directory to be opened')
    parser.add_argument('--filename', help='The file to be viewed (relative to dirname, can\'t be in a subdirectory). Incompatible with other starting file options.')
    parser.add_argument('--begin', action='store_true', help='View the first file in dirname, alphabetically. Incompatible with other starting file options.')
    parser.add_argument('--ignore-mark', dest='ignore_mark', action='store_true', help='Ignore the bookmark file. Other starting file options (like filename and begin) imply ignore-mark.')
    parser.add_argument('--bookmark', default='bookmark.txt', help='Bookmark file to use to determine starting file. If not present, default is random selection.')
    parser.add_argument('--no-marking', dest='no_marking', action='store_true', help='Do not write your final position to the bookmark.')
    parser.add_argument('--marking-file', dest='marking_file', default=None, help='File to write final position. Default is the value of --bookmark')

    args = parser.parse_args()

    if args.filename is not None and args.begin:
        sys.exit("--filename and --begin incompatible")

    startFilename = None
    if args.filename is not None:
        startFilename = args.filename
    elif args.begin:
        startFilename = BEGIN
    elif not args.ignore_mark and os.path.isfile(args.bookmark):
        with open(args.bookmark, "r") as markfile:
            startFilename = markfile.read().rstrip('\n')

    app = capViewerFromDir(args.dirname, startFilename)

    if not args.no_marking:
        markfileName = args.bookmark
        if args.marking_file is not None:
            markfileName = args.marking_file
        with open(markfileName, "w") as markfile:
            markfile.write(app.get_filename())

