##!/usr/bin/python

import datetime, subprocess, sys, getopt, os, shutil
from calendar import monthrange
from array import *
import glob
import urllib


start_date = ''
SRC_PATH = '/home/ericg/mybook_archive/main_backup/bu1'
DEST_PATH = './archive_files'

def parse_args(argv):
   global start_date, is_today

   try:
      opts, args = getopt.getopt(argv,"d:",["date"])
   except getopt.GetoptError:
      print ('test.py -d YYYY-MM-DD')
      sys.exit(2)

   for opt, arg in opts:
      if opt == '-h':
         print ('test.py -date YYYY-MM-DD')
         sys.exit()
      elif opt in ("-d", "--date"):
         start_date = arg

   print ('Show date: {}'.format(start_date))

# return time length of an mp3 file using ffmpeg or -1 if invalid.
# assumes user has ffmpeg in PATH.
def execute_cmd(cmd):
    try:
        print("Execute: +{}+\n".format(cmd))
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        (output, err) = p.communicate()
        p_status = p.wait()
        err = str(err)
        print("Returned +{}+, +{}+\n".format(output, str(err)))
        sys.exit()
    except Exception as ioe:
        print('Exception getting duration for: {}, {}'.format(cmd, ioe))
        sys.exit()

def get_file_path(year_int, month_int, day_int):
    file_path = '{}/{}/kzsu_archive_{}{}{}*'.format(SRC_PATH, year, year, make2digit(month), make2digit(day))
    return file_path

def get_file_minutes(file_path):
    minutes_str = file_path[-6:-4]
    minutes = int(minutes_str)
    return minutes

def get_file_time(file_path):
    time_str = file_path[-8:-4]
    time_int = int(time_str)
    return time_int

def get_src_last_file(year, month, day):
    month2d = make2digit(month)
    day2d = make2digit(day)
    path = '{}/{}/{}-{}-{}/kzsu_archive_{}{}{}_23*.mp3'.format(SRC_PATH, year, year, month2d, day2d, year,month2d,day2d)
    last_files = glob.glob(path)
    return last_files[len(last_files) - 1]

def get_src_files(year, month, day):
    month2d = make2digit(month)
    day2d = make2digit(day)
    path = '{}/{}/{}-{}-{}/kzsu_archive_{}{}{}*.mp3'.format(SRC_PATH, year, year, month2d, day2d, year,month2d,day2d)
    files = glob.glob(path)
    return files

def get_prev_file(year, month, day):
    if day > 1:
        day = day - 1
    elif month > 1:
        month = month - 1
        day = num_days = monthrange(year, month)[1]
    else:
        year = year - 1
        month = 12
        day = 31

    month2d = make2digit(month)
    day2d = make2digit(day)
    last_file = get_src_last_file(year, month, day)
    file_time = get_file_time(last_file)
    if file_time < 2345 or file_time > 2400:
        print("Invalid last file: " + last_file)
        sys.exit()

    return last_file

def make2digit(some_int):
    res = str(some_int)
    if some_int < 10:
        res = '0' + res

    return res

def create_audio_file(concat_files, time_offset_mins_int, year, month, day, hour):
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    time_offset_opt = ''
    if time_offset_mins_int != 0:
        time_offset = make2digit(time_offset_mins_int)
        time_offset_opt = ' -ss 00:{}:00 '.format(time_offset)

    outdir = '{}/{}/{}/{}/'.format(DEST_PATH, year,  months[month], make2digit(day))
    if not os.path.exists(outdir):
        os.makedirs(outdir)

    outfile = 'kzsu-{}-{}-{}-{}00.mp3'.format(year, make2digit(month), make2digit(day), make2digit(hour))
    cmd = '/usr/local/bin/ffmpeg -hide_banner -y {} -t 3600 -i "concat:{}" -acodec copy {}/{}'.format(time_offset_opt, concat_files, outdir, outfile)
    print("ffmpeg cmd: " + cmd)
    execute_cmd(cmd)

def process_day(year, month, day):
    print("Process day {}, {}, {}".format(year, month, day))
    prev_file = get_prev_file(year, month, day)
    prev_minutes = get_file_minutes(prev_file)
    extra_time = prev_minutes - 45

    files = get_src_files(year, month, day)
    lost_time = get_file_minutes(files[0])
    idx = 0;
    if len(files) != 96 and len(files) != 97:
        print("Missing files: {}-{}-{} {}".format(year, month, day, len(files)))
        sys.exit()
    elif(extra_time != lost_time):
        print("Extra time mismatch {}, {}".format(prev_file, files[1]))
        sys.exit()

    concat_files = prev_file if lost_time != 0 else ''
    file_time_len = lost_time
    hour = 0
    for file in files:
        if file_time_len >= 60:
            skip_time = 15 - lost_time
            create_audio_file(concat_files, skip_time, year, month, day, hour)
            file_time_len = lost_time
            concat_files = file if extra_time > 0 else ''
            hour = hour + 1
        else:
            concat_files = concat_files + ('|' if len(concat_files) >  0 else '') + file
            file_time_len = file_time_len + 15

def process_month(year, month):
    print("Process month {}, {}".format(year, month))
    num_days = monthrange(year, month)[1]
    for day in range(num_days):
        process_day(year, month, day)

def process_year(year):
    print("Process year {}".format(year))
    for month in range(12):
        process_month(year, month)

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
    print("Invalid date: " + start_date)




