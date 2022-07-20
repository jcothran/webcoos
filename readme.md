---
Server install
 
apt-get update
apt-get upgrade

pip install wget

apt-get install ffmpeg

---
Video clip processing

Each of the below scripts can be run independently as continuously running scripts. They reference and pass processed files between the below folders.

#fetch_clips.py
beach/video_fetched

#process_clips.py
beach/video_fetched
beach/thumbs

#thumb2txts.py
beach/thumbs
beach/thumbs/buf
beach/thumbs/done
runs/detect/exp/labels

#txt2db.py
runs/detect/exp/labels
beach/results
beach/results/empty


####
fetch_clips.py - retrieve video clips
  this currently uses wget, assuming the video clip is pulled from another site, change as needed for system internal file references

process_clips.py - convert video clips to image stills using ffmpeg
  this currently uses a lock file to limit ffmpeg to running sequentially on files, this can be altered/threaded to suit system/performance

thumb2txt.py - batch(or not depending on system/performance) process image files with object detection, creates summary txt files

txt2db.py - use filename to carry forward camera id and datetime with summary detection info in csv files

---
RTSP processing

beach/rtsp_fetched

get_northlinet_every5min.py - use ffmpeg to get a RTSP feed image sample at time interval(5 minutes)
  this could be changed to loop through multiple RTSP sources

ts_filename.py - creates cam id, timestamp and 'thumb' suffix for later file processing
