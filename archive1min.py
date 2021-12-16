#!/usr/bin/python
#
# This file assembles 60 second archive files into 1 hour blocks starting on the hour.
# The source files are contained in per day tar files named YYYY_MM_DD.tar. First the 
# size of the tar files is sanity checked because some contain only empty mp3 files.
#
import sys, tarfile, getopt, os, shutil
from calendar import monthrange

start_date = ''
create_files = False

#SRC_PATH = '/Users/Barbara/Downloads/markm_archive'
SRC_PATH = '/home/ericg/GoogleDrive/markm_archive'

#DEST_PATH = '/Users/Barbara/Downloads/markm_archive/archive_files/'
DEST_PATH = '/media/pr2100/kzsu-aircheck-archives'


def log_it(msg):
   print(msg, flush=True)

def parse_args(argv):
   global start_date, create_files

   try:
      opts, args = getopt.getopt(argv,"d:c:",["date","create_files"])
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

   log_it ('Show args: {}, {}'.format(start_date, create_files))

def make2digit(some_int):
    res = str(some_int)
    if some_int < 10:
        res = '0' + res

    return res

def log_fatal(msg):
    log_it(msg)
    sys.exit()

def process_day(year, month, day):
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    MIN_FILE_SIZE_1MIN = 900000
    START_HOUR = 6
    END_HOUR = 23

    #log_it("Process day {}, {}, {}".format(year, make2digit(month), make2digit(day)))
    tarfile_path = "{}/{}_{}_{}.tar".format(SRC_PATH, year, make2digit(month), make2digit(day))
    if not os.path.exists(tarfile_path):
        log_it("Tar file does not exist: " + tarfile_path)
        return

    srcfile = tarfile.open(tarfile_path);
    members = srcfile.getmembers()
    members_len = len(members)
    if len(members) < 8640:
        if not os.path.exists(tarfile_path):
            log_it("Incomplete tar file: " + tarfile_path)
            return

#    member_list = []
#    dash_idx = members[0].name.rindex('-') + 1
#    for member in members:
#        print("file: {} - {}".format(member.name[dash_idx:-4], member.size))
#        if member.size == FILE_SIZE_1MIN:
#            member_list.append(int(member.name[dash_idx:-4]))


    outdir = '{}/{}/{}/{}/'.format(DEST_PATH, year,  months[month-1], make2digit(day))
    if not os.path.exists(outdir):
        os.makedirs(outdir)

    for hour in range(START_HOUR, END_HOUR+1):
        dest_path = '{}/kzsu-{}-{}-{}-{}00.mp3'.format(outdir, year, make2digit(month), make2digit(day), make2digit(hour))
        if os.path.exists(dest_path):
            log_fatal("File exists: " + dest_path)

        total_size = 0
        dest = open(dest_path, 'wb') if create_files else None

        for minute in range(hour*60, (hour+1)*60):
            fsize = members[minute].size if minute < members_len else -1
            if  fsize < MIN_FILE_SIZE_1MIN:
                log_fatal('Incomplete minute: {}, {}, {}'.format(fsize, minute, tarfile_path))

            buffer = srcfile.extractfile(members[minute])
            total_size = total_size + fsize
            if not buffer:
                log_fatal('Missing minute: {}, {}'.format(minute, tarfile_path))
            elif dest:
                shutil.copyfileobj(buffer, dest, 100000)

        print("File ceated: {}, {}".format(dest_path, total_size))
        if dest:
            dest.close()

def process_month(year, month):
    log_it("Process month {}, {}".format(year, month))
    num_days = monthrange(year, month)[1]
    for day in range(num_days):
        log_it('process day: ' + str(day+1))
        process_day(year, month, day+1)

def process_year(year):
    log_it("Process year {}".format(year))
    for month in range(12):
        log_it("process month: " + str(month+1))
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




