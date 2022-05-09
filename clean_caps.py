#!/usr/bin/env python3

import argparse

import navigate_caps
import view_caps


def cleanDirectory(dirname):
    fileNav = navigate_caps.FileNavigator(dirname)
    for imgfile,txtfile in fileNav:
        # get hash of imgfile and sqash-case of txtfile
        # iterate through the rest of the directory, keeping a list of files that match either
        # open a cap viewer on that list, allowing the user to delete duplicates if necessary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Search collections of images and text for duplicates")
    parser.add_argument('--dirname', default=".", help='The directory to be opened')

    args = parser.parse_args()

    cleanDirectory(args.dirname)
