#!/usr/bin/python
#
# This file adjusts the time start of 60 minute archive files to start on the hour.
# Typical input file: kzsu_archive_20150807_0053.mp3.
#
import datetime, subprocess, sys, getopt, os, math, shutil
from calendar import monthrange

from array import *
import glob
import urllib


start_date = ''
create_files = False

#SRC_PATH = '/home/ericg/mybook_archive/main_backup/bu1'
SRC_PATH = '/tmp/archives'
#DEST_PATH = '/media/pr2100/kzsu-aircheck-archives'
DEST_PATH = './archive_files'
months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

def log_it(msg):
   print(msg, flush=True)

def parse_args(argv):
   global start_date, create_files

   try:
      opts, args = getopt.getopt(argv,"d:c:s:",["date","create_files"])
   except getopt.GetoptError:
      log_fatal ('test.py -c -d YYYY-MM-DD -s +/-<0-60>')

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
    print("path: " + file_path)
    return file_path

def get_file_minutes(file_path):
    minutes_str = file_path[-6:-4]
    minutes = int(minutes_str)
    return minutes

def get_file_hours(file_path):
    hours_str = file_path[-8:-6]
    hours = int(hours_str)
    return hours

def get_file_time(file_path):
    time_str = file_path[-8:-4]
    time_int = int(time_str)
    return time_int

def get_file_datetime(file):
    date_str = file[-17:-9] + '_' + file[-8:-4]
    date = datetime.datetime.strptime(date_str, '%Y%m%d_%H%M')
    return date

def get_src_files(year, month, day):
    month2d = make2digit(month)
    day2d = make2digit(day)
    path = '{}/{}/{}/{}/kzsu_archive_{}{}{}*'.format(SRC_PATH, year, months[month-1], day2d, year, month2d, day2d)
    print("path: " + path)
    files = glob.glob(path)
    return files


def make2digit(some_int):
    res = str(some_int)
    if some_int < 10:
        res = '0' + res

    return res

def log_fatal(msg):
    log_it(msg)
    sys.exit()


def create_audio_file(prev_file, file, time_offset_mins_int):
    date = get_file_datetime(file)
    year = date.year
    month = date.month
    day = date.day
    hour = date.hour
    time_offset_opt = ''
    if time_offset_mins_int != 0:
        total_seconds = (60 - time_offset_mins_int) * 60
        mins = math.floor(total_seconds / 60)
        seconds = total_seconds % 60
        time_offset_opt = ' -ss 00:{}:{} '.format(make2digit(mins), make2digit(seconds))

    outdir = '{}/{}/{}/{}/'.format(DEST_PATH, year,  months[month-1], make2digit(day))
    if not os.path.exists(outdir):
        os.makedirs(outdir)

    outfile = 'kzsu-{}-{}-{}-{}00.mp3'.format(year, make2digit(month), make2digit(day), make2digit(hour))
    concat_str = '{}|{}'.format(prev_file, file)
    outpath = '{}/{}'.format(outdir, outfile)
    cmd = '/usr/local/bin/ffmpeg -hide_banner -y {} -t 3600 -i "concat:{}" -acodec copy {}'.format(time_offset_opt, concat_str, outpath)
    log_it("ffmpeg cmd: " + cmd)
    if create_files:
        if os.path.exists(outpath):
           suffix = datetime.datetime.now().strftime(".%Y-%m-%dT%H:%M:%S.backup")
           # only move the original file to backup
           if not os.path.exists(outpath + suffix):
               shutil.move(outpath, outpath + suffix)

        execute_cmd(cmd)

def is_valid_start_time(file):
    mins = get_file_minutes(file)
    is_valid = mins == 0 or mins >= 46
    return is_valid

def process_day(year, month, day):
    log_it("Process day {}, {}, {}".format(year, month, day))
    files = get_src_files(year, month, day)

    if len(files) == 0:
        log_it("no files for: {}-{}-{}".format(year, month, day))
        return

    #0053 - 0153,  0153 - 0253
    prev_hour = -100
    prev_file = None
    for file in files:
        hour = get_file_hours(file)
        if hour == prev_hour + 1:
            file_mins = get_file_minutes(file)
            create_audio_file(prev_file, file, file_mins)
        else:
            log_fatal("Does not appear to be an hourly archive.")

        prev_file = file
        prev_hour = hour

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




