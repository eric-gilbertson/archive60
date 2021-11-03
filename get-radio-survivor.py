##!/usr/bin/python

# this file downloads Radio Survivor via its RSS feed and copies the file
# to the show staging directory using the date & time obtained from the schedule.

import httplib2, subprocess, datetime, glob, os, shutil, requests
import xml.etree.ElementTree as et

# TODO: add a get show by id or title
def get_show_day():
    DAYS_TO_INDEX = {"Mon": 0, "Tue" : 1, "Wed": 2, "Thu" : 3, "Fri": 4, "Sat":5, "Sun":6}
    r = requests.get('http://kzsu.stanford.edu/api/shows/thisweek/')
    r.raise_for_status()
    show_info = r.json()
    for day in show_info['days']:
        for show in day['shows']:
            if show['title'] == 'Radio Survivor':
                day_idx = show['weekday']
                hour = show['start_time'][0:2]
                return (int(DAYS_TO_INDEX[day_idx]), int(hour))

    return (-1, -1)


def download_mp3(url):
    cmd = "/usr/local/bin/wget '{}' ".format(url)
    print("execute: " + cmd)

    nameidx = url.index('/media/')
    downloaded_filename = url[nameidx + 7:]
    print("file: " + downloaded_filename)

    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    (output, err) = p.communicate()
    p_status = p.wait()
    print("error: " + str(err))
    return downloaded_filename

def stage_mp3(show_file):
    UPLOAD_DIR = '/Users/Barbara/studioq2/show_uploads'
    now = datetime.datetime.now()
    nowday = now.weekday()
    daydelta = showday - nowday if showday >= nowday else (7 - nowday) + showday
    showdate = now + datetime.timedelta(days=daydelta)

    show_date = showdate.strftime("%Y-%m-%d_") + "{:02}00-{:02}00".format(showhour, showhour + 1)
    full_path = '{}/{}_Radio-Survivor.mp3'.format(UPLOAD_DIR, show_date)
    shutil.copyfile(show_file, full_path)
    os.remove(show_file)


def get_download_url():
    resp, content = httplib2.Http().request('http://broadcast.radiosurvivor.com/pg/feed.xml');
    xml = et.fromstring(content)
    url = xml.find('channel').find('item').find('enclosure').attrib['url']
    return url


######################################################
(showday, showhour) = get_show_day()
if showday == -1:
    print("Radio Survior not found in schedule.")
    sys.exit()

url = get_download_url()
show_file = download_mp3(url)
stage_mp3(show_file)

