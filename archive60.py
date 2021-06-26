##!/usr/bin/python
#
# This file converts the 15 minute archive files created by the old podkeeper archiver
# to the new 60 minute files that start on the hour. The source files are stored under
# a directory structure of <YEAR>/<YEAR>-<MM>-<DD>/kzsu_archive_<YYYY><MM><DD>_<HH><MM>.mp3.
# The files are assumed to be intact, e.g. those with large audio gaps have been removed. 
# The 15 minute segments are joined to form an hour long file that starts on the hour. Because
# the source files do not usually start on the hour up to five of them are needed to create
# a new 60 minute file. Challenges to be aware of include:
#
#    - source files are incomplete, e.g. there are time gaps
#    - segment start time offset drifts over time
#
import datetime, subprocess, sys, getopt, os, shut
from calendar import monthrange

from array import *
import glob
import urllib


start_date = ''
create_files = False
#SRC_PATH = '/home/ericg/mybook_archive/main_backup/bu1'
SRC_PATH = './archives'
DEST_PATH = './archive_files'

SEG_LEN_MINS = 15
SEG_LEN_SECS = SEG_LEN_MINS * 60

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
      elif opt in ("-cf", "--create-files"):
         create_files = True

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

def get_file_hours(file_path):
    hours_str = file_path[-8:-6]
    hours = int(hours_str)
    return hours

def get_file_time(file_path):
    time_str = file_path[-8:-4]
    time_int = int(time_str)
    return time_int

def get_file_datetime(file):
    ar = file.split('_')
    date_str = ar[2] + '_' + ar[3][0:4]
    date = datetime.datetime.strptime(date_str, '%Y%m%d_%H%M')
    return date

def get_src_last_file(year, month, day):
    month2d = make2digit(month)
    day2d = make2digit(day)
    path = '{}/{}/{}-{}-{}/kzsu_archive_{}{}{}_23*.mp3'.format(SRC_PATH, year, year, month2d, day2d, year,month2d,day2d)
    last_files = glob.glob(path)
    last_file = last_files[len(last_files) - 1] if len(last_files) else None

def get_src_files(year, month, day):
    month2d = make2digit(month)
    day2d = make2digit(day)
    path = '{}/{}/{}-{}-{}/kzsu_archive_{}{}{}_*.mp3'.format(SRC_PATH, year, year, month2d, day2d, year,month2d,day2d)
    files = glob.glob(path)
    return files

def get_prev_file(year, month, day):
    last_file = None
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
    file = get_src_last_file(year, month, day)
    if file:
        file_time = get_file_time(last_file)
        if file_time < 2345 or file_time > 2400:
            last_file = file

    return last_file

def are_consecutive_files(file, next_file):
    date = get_file_datetime(file)
    next_date = get_file_datetime(next_file)
    delta = next_date - date
    # must account for 1 minute time drifts
    return abs(delta.seconds - SEG_LEN_SECS) < 61

def make2digit(some_int):
    res = str(some_int)
    if some_int < 10:
        res = '0' + res

    return res

def log_fatal(msg):
    print(msg)
    sys.exit()

# check that the parameters for the audio file are correct, e.g:
# start at TOTH, consecutive segments & correct time offset.
def check_audio_validity(concat_files, time_offset_mins):
    concat_len = len(concat_files)
    if concat_len < 4 or concat_len > 5:
        log_fatal('incorrect file count: ' + concat_files[0])

    first_file = concat_files[0]
    skip_time_mins = 60 - get_file_minutes(first_file)
    if concat_len == 4 and time_offest != 0:
        log_fatal('Invalid time offset for four count: ' + first_file)
    elif skip_time_mins != time_offset_mins:
        log_fatal('Time offset mismatch: ' + first_file)
    elif time_offset_mins < 0 or time_offset_mins  > 14:
        log_fatal('Incorrect time offset: ' + first_file)

    prev_file = None
    for file in concat_files:
        if not prev_file:
            if not is_valid_start_time(file):
                log_fatal("invalid start time offset: " + file)

            prev_file = file
            continue

        if not are_consecutive_files(prev_file, file):
            log_fatal('files not conseutive: {}, {}'.format(prev_file, file))

        prev_file = file

    return True

def create_audio_file(concat_files, time_offset_mins_int):
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

    # will exit if invalid params
    check_audio_validity(concat_files, time_offset_mins_int)

    file = concat_files[len(concat_files) - 1]
    date = get_file_datetime(file)
    year = date.year
    month = date.month
    day = date.day
    hour = date.hour
    time_offset_opt = ''
    if time_offset_mins_int != 0:
        time_offset = make2digit(time_offset_mins_int)
        time_offset_opt = ' -ss 00:{}:00 '.format(time_offset)

    outdir = '{}/{}/{}/{}/'.format(DEST_PATH, year,  months[month], make2digit(day))
    if not os.path.exists(outdir):
        os.makedirs(outdir)

    outfile = 'kzsu-{}-{}-{}-{}00.mp3'.format(year, make2digit(month), make2digit(day), make2digit(hour))
    concat_str = '|'.join(concat_files)
    cmd = '/usr/local/bin/ffmpeg -hide_banner -y {} -t 3600 -i "concat:{}" -acodec copy {}/{}'.format(time_offset_opt, concat_str, outdir, outfile)
    print("ffmpeg cmd: " + cmd)
    if create_files:
        execute_cmd(cmd)

def is_valid_start_time(file):
    mins = get_file_minutes(file)
    is_valid = mins == 0 or mins >= 46
    return is_valid

def process_day(year, month, day):
    print("Process day {}, {}, {}".format(year, month, day))
    files = get_src_files(year, month, day)
    prev_file = get_prev_file(year, month, day)
    if prev_file:
        files.insert(0, prev_file)

    if len(files) == 0:
        print("no files for: {}-{}-{}".format(year, month, day))
        return

    concat_files = ''
    offset_mins = get_file_minutes(files[0])
    concat_files = []
    for file in files:
        concat_len = len(concat_files)
        if concat_len == 0 and not is_valid_start_time(file):
            continue

        if concat_len == 0 or  are_consecutive_files(concat_files[len(concat_files)-1], file):
            concat_files.append(file)
            concat_len = len(concat_files)
            if len(concat_files) > 4 or len(concat_files) == 4 and offset_mins == 0:
                skip_time = 60 - get_file_minutes(concat_files[0])
                create_audio_file(concat_files, skip_time)
                concat_files.clear()
                if skip_time > 0:
                    concat_files.append(file)
        else:
            concat_files.clear()
            if is_valid_start_time(file):
                concat_files.append(file)

def process_month(year, month):
    print("Process month {}, {}".format(year, month))
    num_days = monthrange(year, month)[1]
    for day in range(num_days):
        print('process day: ' + str(day+1))
        process_day(year, month, day+1)

def process_year(year):
    print("Process year {}".format(year))
    for month in range(12):
        print("process month: " + month+1)
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
    print("Invalid date: " + start_date)




