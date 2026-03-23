#!/usr/bin/env python3

import argparse
import datetime
import os
import sqlite3

def save_sequence(connection, cursor):
    while True:
        # User input: make new record or quit
        make_record_inst = input("[M]ake new record or [Q]uit?\n")
        if make_record_inst == "Q":
            break
        elif make_record_inst != "M":
            print("Error during user input: Must be 'M' or 'Q'")
            continue

        abort_record = False
        record_id = None

        try:
            # Title
            title = input("Enter a title for the new record (or leave blank):\n")
            if not title:
                title = "null"
            cursor.execute("insert into records (title) values (?)", (title,))
            record_id = cursor.lastrowid

            # Tags
            tags = input("Enter a comma-separated list of tags for the new record (or leave blank):\n")
            tag_list = tags.split(",")
            values_list = [(record_id, tag) for tag in tag_list]
            cursor.executemany("insert into tags (record_id, name) values (?, ?)", values_list)

        except Exception as e:
            print("Error during record construction: ", e)
            connection.rollback()
            continue

        make_new_entry = True
        entry_idx = 0

        while make_new_entry:
            entry_id = None

            try:
                # Insert entry
                cursor.execute("insert into record_entries (record_id, idx) values (?, ?)", (record_id, entry_idx))
                entry_id = cursor.lastrowid
                entry_idx += 1

            except Exception as e:
                print("Error during entry construction: ", e)
                connection.rollback()
                continue

            make_new_file = True
            while make_new_file:
                # User input: grabbed blob file, copied text file, next entry, finish record, abort record
                make_file_inst = input("[B]lob file, pasted [T]ext file, [N]ext entry, [F]inish record, [A]bort record\n")

                if make_file_inst == "B":
                    try:
                        # Grabbed blob file
                        filename = None
                        image_path = input("Enter the path for your file. Or leave blank for latest downloaded file.\n")
                        if image_path:
                            if os.path.isfile(image_path):
                                filename = image_path
                            else:
                                print("Error during file construction: Invlid path ", image_path)
                                continue
                        else:
                            filename = max(os.listdir(), key=os.path.getctime)
                            print ("Using ", filename)

                        cursor.execute("insert into files (entry_id, filename) values (?, ?)", (entry_id, filename))
                    except Exception as e:
                        print("Error during file construction: ", e)
                        continue

                elif make_file_inst == "T":
                    try:
                        # Copied text file
                        filename = datetime.datetime.now().strftime("%m%d%y%H%M%S") + ".txt"

                        if os.path.isfile(filename):
                            print("Error during file construction: Duplicate path ", filename)
                            continue

                        print("Enter/Paste your content. Ctrl-D or Ctrl-Z ( windows ) to save it.")
                        contents = []
                        while True:
                            try:
                                line = input()
                            except EOFError:
                                break
                            contents.append(line)

                        output = '\n'.join(contents).strip()

                        with open(filename, 'w') as file:
                            file.write(output)

                        cursor.execute("insert into files (entry_id, filename) values (?, ?)", (entry_id, filename))
                    except Exception as e:
                        print("Error during file construction: ", e)
                        continue

                elif make_file_inst == "N":
                    # Next entry
                    make_new_file = False
                elif make_file_inst == "F":
                    # Next record:
                    make_new_file = False
                    make_new_entry = False
                elif make_file_inst == "A":
                    # Abort record:
                    make_new_file = False
                    make_new_entry = False
                    abort_record = True
                else:
                    print("Error during file construction: Invlid instruction ", make_file_inst)
                    continue

        if abort_record:
            connection.rollback()
        else:
            connection.commit()


def check_integrity(connection, cursor):
    # Compare files in DB to files in data dir
    # The lists of all files in data directory and all files in files table are the same size
    dir_list = os.listdir()
    db_list = [row[1] for row in cursor.execute("select * from files").fetchall()]
    dir_only_set = set(dir_list) - set(db_list)
    db_only_set = set(db_list) - set(dir_list)
    if dir_only_set or db_only_set:
        print("Error during integrity check: Mismatch between data dir and files table")
        print("    Entries in data dir only: ", ", ".join(dir_only_set))
        print("    Entries in files table only: ", ", ".join(db_only_set))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Save collections of images and text using a SQLite database.")
    parser.add_argument("--db", default="./database.db", help="The filename of the SQLite database.")
    parser.add_argument("--data_dir", default="./data", help="The directory the files will be saved to")

    args = parser.parse_args()

    # Open connection
    connection = sqlite3.connect(args.db)
    cursor = connection.cursor()
    cursor.execute("PRAGMA foreign_keys = ON")

    # Enter data dir
    if not os.path.isdir(args.data_dir):
        print("Error during initialization: ", data_dir, " is not a directory")
        quit()
    os.chdir(args.data_dir)

    save_sequence(connection, cursor)

    check_integrity(connection, cursor)
