#!/usr/bin/env python3

import argparse
import os.path
import sqlite3

def save_sequence(db_file, data_dir):
    # Open connection
    connection = sqlite3.connect(db_file)
    cursor = connection.cursor()
    cursor.execute("PRAGMA foreign_keys = ON")

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
                # User input: grabbed blob file, copied text file, next entry, next record, abort record
                make_file_inst = input("[B]lob file, [T]ext file, next [E]ntry, next [R]ecord, [A]bort record\n")

                if make_file_inst == "B":
                    try:
                        # Grabbed blob file
                        filename = None
                        image_path = input("Enter the path for your image. Or leave blank for latest downloaded image.\n")
                        if image_path:
                            if os.path.isfile(image_path):
                                filename = image_path
                            else:
                                print("Error during file construction: Invlid path ", image_path)
                                continue
                        else:
                            list_of_files = glob.glob(data_dir + '/*')
                            filename = max(list_of_files, key=os.path.getctime)
                            print ("Using ", filename)

                        cursor.execute("insert into files (entry_id, filename) values (?, ?)", (entry_id, filename))
                    except Exception as e:
                        print("Error during file construction: ", e)
                        continue

                elif make_file_inst == "T":
                    # TODO: Copied text file
                    try:
                        filename = None

                        print("Enter/Paste your content. Ctrl-D or Ctrl-Z ( windows ) to save it.")
                        contents = []
                        while True:
                            try:
                                line = input()
                            except EOFError:
                                break
                            contents.append(line)

                        output = '\n'.join(contents).strip()

                        #with open(os.path.join(location, filename), 'wb') as file:
                            #file.write(raw_data)

                        cursor.execute("insert into files (entry_id, filename) values (?, ?)", (entry_id, filename))
                    except Exception as e:
                        print("Error during file construction: ", e)
                        continue

                elif make_file_inst == "E":
                    # Next entry
                    make_new_file = False
                elif make_file_inst == "R":
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


def check_integrity(dbFile, dataDir):
    # TODO: compare files in DB to files in data dir
    pass

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Save collections of images and text using a SQLite database.")
    parser.add_argument("--db", default="./database.db", help="The filename of the SQLite database.")
    parser.add_argument("--data_dir", default="./data", help="The directory the files will be saved to")

    args = parser.parse_args()

    save_sequence(args.db, args.data_dir)

    check_integrity(args.db, args.data_dir)
