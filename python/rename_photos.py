#! /usr/bin/python3

import os
from datetime import datetime

import crc32c
import argparse
import time
import logging
import sys
import piexif
import exiftool

from PIL import Image

## config
IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png']
VIDEO_EXTENSIONS = ['.mts', '.mpg', '.mov', '.mp4', '.3gp']
RAW_EXTENSIONS = ['.nef', '.raw', '.lrf']

# create logger
log = logging.getLogger("rename_photos")
log.setLevel(logging.INFO)

# create console handler and set level to debug
ch = logging.StreamHandler(stream=sys.stdout)
ch.setLevel(logging.INFO)
# ch.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
ch.setFormatter(logging.Formatter("%(message)s"))
log.addHandler(ch)


def is_img(file_ext):
    """
    Checks if the given file extension is an image file.

    :param file_ext: The file extension to be checked.
    :type file_ext: str
    :return: True if the given file extension is an image file, false if not.
    """
    if file_ext.lower() in IMAGE_EXTENSIONS:
        return True
    else:
        return False


def is_vid(file_ext):
    """
    Checks if the given file extension is a video file.

    :param file_ext: The file extension to be checked.
    :type file_ext: str
    :return: True if the given file extension is a video file, false if not.
    """
    if file_ext.lower() in VIDEO_EXTENSIONS:
        return True
    else:
        return False


def is_raw(file_ext):
    """
    Checks if the given file extension is a raw image file.

    :param file_ext: The file extension to be checked.
    :type file_ext: str
    :return: True if the given file extension is a raw image file, false if not.
    """
    if file_ext.lower() in RAW_EXTENSIONS:
        return True
    else:
        return False


def get_file_extension(file_ext):
    file_ext_lower = file_ext.lower()
    if file_ext_lower in [".jpg", '.jpeg']:
        return ".jpg"
    elif file_ext_lower == ".png":
        return ".png"
    elif file_ext_lower == ".nef":
        return ".nef"
    elif file_ext_lower == ".lrf":
        return ".lrf"
    elif file_ext_lower in VIDEO_EXTENSIONS:
        return file_ext_lower
    else:
        log.warning(f"Couldn't find rule for extension '{file_ext}'.")
        return file_ext_lower()


def parse_arguments():
    # create argument parser and add arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--dir", type=str, required=True, help="target directory for file renaming")
    parser.add_argument("-r", "--recursive", dest='recursive', action='store_true', default=False,
                        help="rename photos recursively")
    parser.add_argument("-dr", "--dry-run", dest='dry_run', action='store_true', default=False,
                        help="output potential changes without performing them")
    parser.add_argument("-l", "--log", type=str, help="define log file location and enable file logging")
    parser.add_argument("-y", "--year", type=int, help="define the default year for all files")
    parser.add_argument("-e", "--exclude", nargs='+', help="define folder names to be excluded")

    # parse arguments from input
    args = parser.parse_args()

    log.debug("Parsed parameters")

    return args


def init_logging(log_file=None, start_dir=None, enabled=True):
    if not enabled:
        return

    if log_file is None:
        log_file = os.path.join(start_dir, "rename_photos.log")
        log.info(f"No log file provided, saving log to root dir: {start_dir}")

    if os.path.isfile(log_file):
        file_id = 1
        while os.path.isfile(f"{log_file}.{file_id}"):
            file_id += 1
        os.rename(log_file, f"{log_file}.{file_id}")

    fh = logging.FileHandler(log_file, mode='w', encoding='utf-8')
    fh.setLevel(logging.INFO)
    fh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)-8s] %(message)s"))
    log.addHandler(fh)


def get_file_datetime(file_path, file_ext):
    """
    Retrieve the date and time of a picture/video, either when it was taken or when it was created/modified.

    :param file_path: The path to the visual file.
    :param file_ext: The extension of the visual file.
    :return: The date time as string (%Y:%m:%d %H:%M:%S).
    :return type: str
    """
    date_time = None

    if is_img(file_ext):
        # open the image
        image = Image.open(file_path)

        # extracting the exif metadata
        # exifdata = image.getexif()

        try:
            exif_dict = piexif.load(image.info['exif'])
            if piexif.ExifIFD.DateTimeOriginal in exif_dict['Exif'].keys():
                date_time = exif_dict['Exif'][piexif.ExifIFD.DateTimeOriginal].decode("utf-8")
        except KeyError:
            pass

    elif is_vid(file_ext):
        with exiftool.ExifToolHelper() as et:
            metadata = et.get_metadata(file_path)
            for d in metadata:
                date_time = d["QuickTime:CreateDate"]

        # # looping through all the tags present in exifdata
        # for tagid in exifdata:
        #     # getting the tag name instead of tag id
        #     tagname = TAGS.get(tagid, tagid)
        #
        #     # printing the final result
        #     if tagname == "DateTimeOriginal":
        #         # passing the tagid to get its respective value
        #         date_time = exifdata.get(tagid)

    if date_time is None:
        time_stamp = min(os.path.getctime(file_path), os.path.getmtime(file_path))
        date_time = time.strftime("%Y:%m:%d %H:%M:%S", time.gmtime(time_stamp))

    try:
        datetime.strptime(date_time, "%Y:%m:%d %H:%M:%S").timestamp()
    except ValueError:
        date_time = datetime.fromtimestamp(0).strftime("%Y:%m:%d %H:%M:%S")

    return date_time


def set_file_datetime(file_path, file_ext, new_date_time):
    """
    Set the modification time of a given filename to the given mtime.
    mtime must be a datetime object.
    """
    set_date_time = False
    if is_img(file_ext):
        # open the image
        image = Image.open(file_path)


        # extracting the exif metadata
        try:
            exif_dict = piexif.load(image.info['exif'])
            new_date_time = new_date_time.strftime("%Y:%m:%d %H:%M:%S")
            if piexif.ExifIFD.DateTimeOriginal in exif_dict['Exif'].keys():
                exif_dict['Exif'][piexif.ExifIFD.DateTimeOriginal] = new_date_time
            if piexif.ExifIFD.DateTimeOriginal in exif_dict['Exif'].keys():
                exif_dict['Exif'][piexif.ExifIFD.DateTimeDigitized] = new_date_time
            if '0th' in exif_dict.keys() and piexif.ImageIFD.DateTime in exif_dict['0th'].keys():
                exif_dict['0th'][piexif.ImageIFD.DateTime] = new_date_time
            if '1st' in exif_dict.keys() and piexif.ImageIFD.DateTime in exif_dict['1st'].keys():
                exif_dict['1st'][piexif.ImageIFD.DateTime] = new_date_time

            exif_bytes = piexif.dump(exif_dict)
            image.save(file_path, image.format, exif=exif_bytes)
            set_date_time = True

            log.info(f"Set new exif-time ({new_date_time}) for file: {file_path}")
        except KeyError:
            pass

    if not set_date_time:
        stat = os.stat(file_path)
        atime = stat.st_atime
        os.utime(file_path, times=(atime, new_date_time.timestamp()))

        log.info(f"Set new mtime ({new_date_time}) for file: {file_path}")


def rename_file(file_path, file_ext, dry_run, default_year=None, file_mon_day=None, file_date_offset= None):
    """
    Renames the given file using the date, time and hash of the file.

    :param file_path: The path of the file to be renamed.
    :param file_ext: The extension of the file to be renamed.
    :param dry_run: Whether files should be actually renamed or potential actions should just be printed.
    :param default_year:
    :param file_mon_day:
    :param file_date_offset:
    :return: The new file path of the renamed file.
    """
    # open file, calculate and reformat hash
    with open(file_path, "rb") as byte_file:
        file_hash = crc32c.crc32c(byte_file.read())
    file_hash = f"{file_hash:08x}".upper()

    log.debug(f"File hash: {file_hash}")

    # get date and time from file
    date_time = get_file_datetime(file_path, file_ext)

    # extract date and time separately from time string
    date_time_tmp = date_time.replace(":", "").split(" ")
    dat = date_time_tmp[0]
    tim = date_time_tmp[1]

    file_mon_day_changed = False
    if default_year is not None and int(dat[:4]) != default_year:
        log.info(f"\nFound a file with non-matching date ({dat} vs {default_year}): {file_path}")
        if file_mon_day is None:
            file_mon_day = input("Please enter new date for given file (form: mmdd):  ")
            if file_mon_day is None or len(file_mon_day) < 4:
                log.info(f"No date entered, using day/month of original date ({dat[4:]})")
                # file_mon_day = dat[4:]
                file_mon_day_changed = False
            else:
                file_mon_day_changed = True

    if file_mon_day is not None and len(file_mon_day) == 4:
        dat = f'{default_year}{file_mon_day}'

        # change file date
        month = int(file_mon_day[:2])
        day = int(file_mon_day[2:])
        time_h = int(tim[:2])
        time_m = int(tim[2:4])
        time_s = int(tim[4:])

        new_date_time = datetime(default_year, month, day, time_h, time_m, time_s)
        old_date_time = datetime.strptime(date_time, "%Y:%m:%d %H:%M:%S")

        if file_date_offset is None:
            file_date_offset = new_date_time.timestamp() - old_date_time.timestamp()
        else:
            new_date_time = datetime.fromtimestamp(old_date_time.timestamp() + file_date_offset)
            dat = new_date_time.strftime("%Y%m%d")
            tim = new_date_time.strftime("%H%M%S")

        if not dry_run:
            set_file_datetime(file_path, file_ext, new_date_time)
        else:
            log.info(f"Set new {'exif-time' if is_img(file_ext) else 'mtime'} ({new_date_time}) for file: {file_path}")

        if file_mon_day_changed:
            if input(f"Would you like to use the date '{file_mon_day}' to update all "
                     f"files in '{os.path.dirname(file_path)}'? [y/n]    ").lower() not in ['y', 'yes']:
                file_mon_day = None
                file_date_offset = None
            else:
                date_diff_str = new_date_time - old_date_time
                if input(f"Would you like to use the offset '{date_diff_str}' to update all "
                         f"files in '{os.path.dirname(file_path)}'? [y/n]    ").lower() not in ['y', 'yes']:
                    file_date_offset = None
    else:
        file_mon_day = None

    # create new file name
    file_name_new = f"{dat}_{tim}_{file_hash}{get_file_extension(file_ext)}"
    file_path_new = os.path.join(os.path.dirname(file_path), file_name_new)

    # rename the file
    if file_path == file_path_new:
        log.info(f"Skipped file: '{file_path}' > '{file_name_new}'")
    else:
        if not dry_run:
            os.rename(file_path, file_path_new)

            # print message and write to logs
            log.info(f"Renamed file: '{file_path}' > '{file_name_new}'")
        else:
            log.info(f"File to rename: '{file_path}' > '{file_name_new}'")

    return file_path_new, file_mon_day, file_date_offset


def sort_files_by_date(directory, files):
    sorted_files = dict()

    for file_i in files:
        file_path_i = os.path.join(directory, file_i)
        file_name_i, file_ext_i = os.path.splitext(file_i)

        date_time_i = get_file_datetime(file_path_i, file_ext_i)
        date_time_i = datetime.strptime(date_time_i, "%Y:%m:%d %H:%M:%S").timestamp()

        while date_time_i in sorted_files.keys():
            date_time_i += 1
        sorted_files[date_time_i] = file_i

    return dict(sorted(sorted_files.items()))


def rename_dirs(start_dir, recursive=False, dry_run=False, default_year=None, excluded_dirs=None):
    # loop through all directories
    for root, dirs, files in os.walk(start_dir, topdown=True):
        files_raw = list()
        files_renamed = dict()
        file_mon_day = None
        file_date_offset = None

        if excluded_dirs is not None and os.path.basename(root) in excluded_dirs:
            log.info(f"Skipping excluded directory '{root}'")
            if not recursive:
                break
            else:
                continue

        log.info(f"Renaming images in '{root}'")

        files_sorted = sort_files_by_date(root, files)

        # loop over all files
        for file_i in files_sorted.values():
            file_path_i = os.path.join(root, file_i)
            # extract filename (path) and file extension from file path
            file_name_i, file_ext_i = os.path.splitext(file_i)

            if not is_img(file_ext_i) and not is_vid(file_ext_i):
                if is_raw(file_ext_i):
                    files_raw.append(file_i)
                continue

            if not os.path.isfile(file_path_i):
                log.warning(f"File doesn't exist: '{file_path_i}'")

            file_path_new, file_mon_day, file_date_offset = rename_file(file_path_i, file_ext_i, dry_run,
                                                                        default_year=default_year,
                                                                        file_mon_day=file_mon_day,
                                                                        file_date_offset=file_date_offset)

            files_renamed[file_name_i] = file_path_new

        # loop over raw files (nef)
        for file_i in files_raw:
            file_path_i = os.path.join(root, file_i)
            # extract filename (path) and file extension from file path
            file_name_i, file_ext_i = os.path.splitext(file_i)

            if file_name_i not in files_renamed.keys():
                log.warning(f"Skipped file: {file_name_i}, Corresponding image file not found")
                continue

            if not os.path.isfile(file_path_i):
                log.warning(f"File doesn't exist: '{file_path_i}'")

            file_path_img, file_ext_img = os.path.splitext(files_renamed[file_name_i])
            file_path_new = f"{file_path_img}{get_file_extension(file_ext_i)}"

            if not dry_run:
                os.rename(file_path_i, file_path_new)

            log.info(f"Renamed file: '{file_path_i}' > '{os.path.basename(file_path_new)}'")

        # stop if recursion isn't enabled
        if not recursive:
            break


def main():
    args = parse_arguments()

    # if not args.dry_run:
    init_logging(log_file=args.log, start_dir=args.dir, enabled=not args.dry_run)

    rename_dirs(start_dir=args.dir, recursive=args.recursive, dry_run=args.dry_run, default_year=args.year,
                excluded_dirs=args.exclude)


if __name__ == '__main__':
    main()
