import os
import zipfile


class FileNavigator:
    def __init__(self, dirname = None, filelist = None):
        source_dir = os.path.dirname(os.path.realpath(__file__))
        self.tmp_dir = os.path.join(source_dir, "tmp")
        self.resource_dir = os.path.join(source_dir, "resources")

        if filelist is not None:
            self.files = filelist
        elif dirname is not None:
            self.files = [os.path.join(dirname, f) for f in os.listdir(dirname) if os.path.isfile(os.path.join(dirname, f))]
        else:
            raise ValueError("FileNavigator must have either dirname or filelist")

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

    def advance(self, wrap = True):
        if wrap:
            self.idx = self.wrap_idx(self.idx+1, len(self.files))
        else:
            self.idx += 1

    def get_current(self):
        self.wipe_tmp()
        self.wipe_seq_data()
        return self.multiplex(self.files[self.idx])

    def get_next(self):
        self.advance()
        return self.get_current()

    def get_prev(self):
        self.idx = self.wrap_idx(self.idx-1, len(self.files))
        return self.get_current()

    def delete(self):
        os.remove(self.files[self.idx])
        self.files.pop(self.idx)
        self.idx = self.wrap_idx(self.idx, len(self.files))
        self.wipe_tmp()
        self.wipe_seq_data()
        return self.multiplex(self.files[self.idx])

    def advance_seq(self, wrap = True):
        if wrap:
            self.subIdx = self.wrap_idx(self.subIdx+1, len(self.subfiles))
        else:
            self.subIdx += 1

    def get_current_seq(self):
        self.wipe_tmp()

        tmp_name = os.path.join(self.tmp_dir, self.subfiles[self.subIdx])
        with zipfile.ZipFile(self.albumfile) as zip:
            zip.extract(self.subfiles[self.subIdx], self.tmp_dir)

        return self.multiplex(tmp_name)

    def get_next_seq(self):
        self.advance_seq()
        return self.get_current_seq()

    def get_prev_seq(self):
        self.subIdx = self.wrap_idx(self.subIdx-1, len(self.subfiles))
        return self.get_current_seq()

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

    def isSeq(self):
        return self.albumfile is not None

    def get_filename(self):
        return self.files[self.idx]

    def get_sub_filename_if_seq(self):
        if self.isSeq():
            return self.subfiles[self.subIdx]
        else:
            return None

    def __del__(self):
        self.wipe_tmp()

    def __iter__(self):
        return self

    def __next__(self):
        imgname, txtname = ""

        if self.isSeq():
            try:
                imgname,txtname = self.get_current_seq()
                self.advance_seq(False)
            except IndexError:
                self.advance(False)
                imgname,txtname = self.get_current()
        else:
            try:
                imgname,txtname = self.get_current()
                self.advance(False)
            except IndexError:
                raise StopIteration

        return imgname,txtname

