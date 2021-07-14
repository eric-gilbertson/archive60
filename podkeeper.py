#!/usr/bin/python
#
# This file moves podkeeper files into a hierarchival structure based on file creation
# date. Because the creation year is not included in the file name it must be obtained via
# the file creation info. The create month and day is found by parsing the file name which
# is of the format 'podkeeper MM DD HH.IDX.mp3' where MM is month, DD is day, HH is hour
# of day that recording started at (and may be ommitted on some days) and IDX is the
# 15 minute segment of the day.
import glob, time, sys, getopt, os, shutil

create_files = False

SRC_PATH = './podkeeper'

def log_it(msg):
   print(msg, flush=True)

def parse_args(argv):
   global start_date, create_files, time_skew

   try:
      opts, args = getopt.getopt(argv,"c:",["create_files"])
   except getopt.GetoptError:
      log_fatal ('test.py -c -d YYYY-MM-DD -s +/-<0-60>')

   for opt, arg in opts:
      if opt == '-h':
         log_it ('test.py -c [T|F]')
         sys.exit()
         start_date = arg
      elif opt in ("-c", "--create-files"):
         create_files = True

   log_it ('Show args: {}'.format(create_files))


def make2Digit(some_int):
    res = str(some_int)
    if some_int < 10:
        res = '0' + res

    return res

def log_fatal(msg):
    log_it(msg)
    sys.exit()

parse_args(sys.argv[1:])
path = '{}/podkeeper*.mp3'.format(SRC_PATH)
files = glob.glob(path)
log_it("found files: {}".format(len(files)))
months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

for file in files:
    print(file)
    ctimeStr = time.ctime(os.path.getctime(file))
    ctimeAr = ctimeStr.split(' ')
    year = int(ctimeAr[len(ctimeAr) - 1])
    if year < 2010 or year > 2021: ########### adjust this
        log_fatal("Invalid file year: " + file)

    lastSlash = file.rindex('/') + 1
    fileName = file[lastSlash:]
    fileNameAr = fileName.split(' ')
    if fileNameAr[0] != 'podkeeper':
        log_fatal("invalid file: " + file)

    month = int(fileNameAr[1])
    day = int(fileNameAr[2][:2])
    outdir = '{}/{}/{}/{}'.format(SRC_PATH, year, months[month], make2Digit(day))
    if not os.path.exists(outdir):
        os.makedirs(outdir)

    outfilePath = outdir + '/' + fileName
    log_it("move: {} to {}".format(file, outfilePath))
    if create_files:
        shutil.move(file, outfilePath)
    

