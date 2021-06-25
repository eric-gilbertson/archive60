##!/usr/bin/python

import datetime, subprocess, sys, getopt, os, shutil
import glob

NO_SILENCE = 0
SOME_SILENCE = 1
ALL_SILENCE = 2

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
        #print("Execute: +{}+\n".format(cmd))
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        (output, err) = p.communicate()
        p_status = p.wait()
        return (str(output), str(err))
    except Exception as ioe:
        print('Exception getting duration for: {}, {}'.format(cmd, ioe))
        sys.exit()

def check_for_silence(file):
    cmd = 'ffmpeg -i {}  -af silencedetect=n=-50dB:d=120.0 -f null -'.format(file)
    (output, err)  = execute_cmd(cmd)
    silence_start = "silence_start:" in err
    silence_end = "silence_end:" in err
    ret = NO_SILENCE
    if silence_start and silence_end:
        ret = SOME_SILENCE
    if silence_start and not silence_end:
        ret = ALL_SILENCE

    return ret


corrupt_files_path='/home/ericg/mybook_archive/main_backup/bu1/corrupt_files'
base_path = '/home/ericg/mybook_archive/main_backup/bu1'


parse_args(sys.argv[1:])
date_ar = start_date.split('-')
date_len = len(date_ar)

year = date_ar[0]
if date_len == 3:
    src_path = '{}/{}/{}/*.mp3'.format(base_path, year, start_date)
elif date_len == 2:
    src_path = '{}/{}/{}-{}*/*.mp3'.format(base_path, year, year, date_ar[1])
elif date_len == 1:
    src_path = '{}/{}/*/*.mp3'.format(base_path, year, date_ar[1])

print('src: ' + src_path)

files = glob.glob(src_path)
for file in files:
    silence_code = check_for_silence(file)
    print("{}: {}".format(file, silence_code))

    if silence_code == ALL_SILENCE:
        shutil.move(file, file + '.silent')


