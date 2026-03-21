#!/usr/bin/env python3

import argparse

def save_sequence(db_file, data_dir):
    make_new_record = True
    while make_new_record:
        abort_record = False
        # TODO: Title
        # TODO: Tags
        make_new_entry = True
        entry_idx = 0
        while make_new_entry:
            # TODO: Insert entry
            make_new_file = True
            while make_new_file:
                # TODO: User input: grabbed blob file, copied text file, next entry, next record, abort record, quit
                # TODO: Grabbed blob file
                # TODO: Copied text file
                # TODO: Next entry: make_new_file = False
                # TODO: Next record: make_new_file = False; make_new_entry = False
                # TODO: Abort record:  make_new_file = False; make_new_entry = False; abort_record = True
                # TODO: Quit:  make_new_file = False; make_new_entry = False; make_new_record = False
        if abort_record:
            # TODO: rollback transaction
        else:
            # TODO: commit transaction
        

def check_integrity(dbFile, dataDir):
    # TODO: compare files in DB to files in data dir
    pass

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Save collections of images and text using a SQLite database.")
    parser.add_argument('--db', default="./database.db", help='The filename of the SQLite database.')
    parser.add_argument('--data_dir', default="./data", help='The directory the files will be saved to')

    args = parser.parse_args()

    save_sequence(args.db, args.data_dir)

    check_integrity(args.db, args.data_dir)
