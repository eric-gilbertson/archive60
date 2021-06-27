##!/usr/bin/python

import math, datetime, subprocess, sys, getopt, os, shutil
import glob

base_path = '/home/ericg/mybook_archive/main_backup/bu1'

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
    silence_start_idx = err.find('silence_start:')
    silence_end_idx = err.find('silence_end:')

    if silence_start_idx >= 0:
        if silence_end_idx == -1:
            print(file + ': silent')
            shutil.move(file, file + '.silent')
        else:
            silence_start_idx = silence_start_idx + len('silence_start: ')
            silence_end_idx = silence_end_idx + len('silence_end:')
            silence_start_end_idx = err.find('\\n', silence_start_idx,)
            silence_end_end_idx = err.find('|', silence_end_idx)
            silence_start = math.floor(float(err[silence_start_idx : silence_start_end_idx]))
            silence_end = math.floor(float(err[silence_end_idx : silence_end_end_idx]))
            suffix = '_{}-{}.partial'.format(silence_start, silence_end)
            print(file + ': partial ' + suffix)
            shutil.move(file, file + suffix)

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
    check_for_silence(file)


