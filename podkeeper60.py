#!/usr/bin/python
#
# This file converts the 15 minute archive files created by the old podkeeper archiver
# to the new 60 minute files that start on the hour. The source files are stored under
# a directory structure of <YEAR>/<MMM>/<DD>/podkeeper <MM> <DD> <HH>.<IDX>.mp3.
# The files are assumed to be intact, e.g. those with large audio gaps have been removed. 
# The 15 minute segments are joined to form an hour long file that starts on the hour.
#
# Typical input file:
# podkeeper/2013/Sep/07/podkeeper 09 07 09.9.mp3
#
import datetime, subprocess, sys, getopt, os, math, shutil
from calendar import monthrange

from array import *
import glob
import urllib


start_date = ''
create_files = False

SRC_PATH = '/home/ericg/mybook_archive/main_backup/podkeeper'
#SRC_PATH = './podkeeper'
DEST_PATH = '/media/pr2100/kzsu-aircheck-archives'
#DEST_PATH = './archive_files'

SEG_LEN_MINS = 15
SEG_LEN_SECS = SEG_LEN_MINS * 60
MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

def log_it(msg):
   print(msg, flush=True)

def parse_args(argv):
   global start_date, create_files

   try:
      opts, args = getopt.getopt(argv,"d:c:",["date","create_files"])
   except getopt.GetoptError:
      log_fatal ('Invalid input: test.py -c -d YYYY-MM-DD')

   for opt, arg in opts:
      if opt == '-h':
         log_it ('test.py -c -date YYYY-MM-DD')
         sys.exit()
      elif opt in ("-d", "--date"):
         start_date = arg
      elif opt in ("-c", "--create-files"):
         create_files = True

   log_it ('Show args: {}'.format(start_date))

# return time length of an mp3 file using ffmpeg or -1 if invalid.
# assumes user has ffmpeg in PATH.
def execute_cmd(cmd):
    try:
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        (output, err) = p.communicate()
        p_status = p.wait()
        if p.returncode != 0:
            err = str(err)
            log_it("Execute: +{}+\n".format(cmd))
            log_fatal("Returned +{}+, +{}+\n".format(output, str(err)))
    except Exception as ioe:
        log_it("Execute: +{}+\n".format(cmd))
        log_fatal('Exception getting duration for: {}, {}'.format(cmd, ioe))

def get_file_path(year_int, month_int, day_int):
    file_path = '{}/{}/kzsu_archive_{}{}{}*'.format(SRC_PATH, year, year, make2digit(month), make2digit(day))
    return file_path

def get_file_params(file):
    # podkeeper/2013/Sep/07/podkeeper 09 07 09.9.mp3
    ar = file.split(' ')
    month = int(ar[1])

    if month < 1 or month > 12:
        log_fatal("Incorrect month: " + file)

    day = int(ar[2])
    if day < 1 or day > 31:
        log_fatal("Incorrect day: " + file)

    suffix_ar = ar[3].split('.')
    if suffix_ar[2] != 'mp3':
        log_fatal('Invalid file suffix: ' + file)
    hour = int(suffix_ar[0])
    if hour < 0 or hour > 23:
        log_fatal("Incorrect hour: " + file)

    idx = int(suffix_ar[1])
    if idx < 0 or idx > 48:
        log_fatal("Incorrect index: " + file)

    return (hour, idx)

def get_sort_key(file):
    print("key: " + file)
    ar = file.split(' ')
    suffix_ar = ar[3].split('.')
    return int(ar[1] + ar[2] + suffix_ar[0] + suffix_ar[1])

def get_src_files(year, month, day):
    global MONTHS
    day2d = make2digit(day)
    path = '{}/{}/{}/{}/podkeeper *.mp3'.format(SRC_PATH, year, MONTHS[month-1], day2d)
    files = glob.glob(path)
    files.sort(key=lambda x: get_sort_key(x))
    return files

def make2digit(some_int):
    res = str(some_int)
    if some_int < 10:
        res = '0' + res

    return res

def log_fatal(msg):
    log_it(msg)
    sys.exit()

# check that the parameters for the audio file are correct, e.g:
# start at TOTH, consecutive segments & correct time offset.
def check_audio_validity(concat_files):
    if len(concat_files) != 4:
        log_fatal("Improper file count: " + concat_files[0])

    prev_idx = -1
    prev_hour = -1
    for file in concat_files:
        (hour, idx) = get_file_params(concat_files[0])
        if prev_hour != -1 and (hour != prev_hour or idx != prev_idx + 1):
            log_fatal("Inalid concat file: " + file)

        prev_idx = idx

    return True


def create_audio_file(year, month, day, concat_files):
    global MONTHS
    # will exit if invalid params
    check_audio_validity(concat_files)
    start_hour, start_idx = get_file_params(concat_files[0])
    start_hour = start_hour + math.floor(start_idx / 4)

    file = concat_files[len(concat_files) - 1]

    outdir = '{}/{}/{}/{}/'.format(DEST_PATH, year,  MONTHS[month-1], make2digit(day))
    if not os.path.exists(outdir):
        os.makedirs(outdir)

    outfile = 'kzsu-{}-{}-{}-{}00.mp3'.format(year, make2digit(month), make2digit(day), make2digit(start_hour))
    concat_str = '|'.join(concat_files)
    outpath = '{}/{}'.format(outdir, outfile)
    cmd = '/usr/local/bin/ffmpeg -hide_banner -y -t 3600 -i "concat:{}" -acodec copy {}'.format(concat_str, outpath)
    log_it("ffmpeg cmd: " + cmd)
    if create_files:
        if os.path.exists(outpath):
           suffix = datetime.datetime.now().strftime(".%Y-%m-%dT%H:%M:%S.backup")
           # only move the original file to backup
           if not os.path.exists(outpath + suffix):
               shutil.move(outpath, outpath + suffix)

        execute_cmd(cmd)

def process_day(year, month, day):
    log_it("Process day {}, {}, {}".format(year, month, day))
    files = get_src_files(year, month, day)

    if not files or len(files) == 0:
        log_it("no files for: {}-{}-{}".format(year, month, day))
        return

    concat_files = []
    hour = -1 
    idx = -1
    is_first = True
    for file in files:
        lastSlash = file.rindex('/') + 1
        file = file[lastSlash:]
        (new_hour, new_idx) = get_file_params(file)
        if hour != -1  and (new_hour != hour or new_idx != idx +1):
            log_fatal("start hour/index mismatch: " + file)

        concat_files.append(file)
        hour = new_hour
        idx = new_idx
        if len(concat_files) == 4:
            create_audio_file(year, month, day, concat_files)
            concat_files.clear()

def process_month(year, month):
    log_it("Process month {}, {}".format(year, month))
    num_days = monthrange(year, month)[1]
    for day in range(num_days):
        log_it('process day: ' + str(day+1))
        process_day(year, month, day+1)

def process_year(year):
    log_it("Process year {}".format(year))
    for month in range(12):
        log_it("process month: " + month+1)
        process_month(year, month+1)

parse_args(sys.argv[1:])
date_ar = start_date.split('-')
date_len = len(date_ar)

if date_len == 1:
    process_year(int(date_ar[0]))
elif date_len == 2:
    process_month(int(date_ar[0]), int(date_ar[1]))
elif date_len == 3:
    process_day(int(date_ar[0]), int(date_ar[1]), int(date_ar[2]))
else:
    log_it("Invalid date: " + start_date)




