Each of the below scripts can be run independently as continuously running scripts. They reference and pass processed files between the below folders.

#fetch_clips.py
beach/video_fetched

#process_clips.py
beach/thumbs

#process_clips.py
beach/thumbs/buf
beach/thumbs/done

#txt2db.py
runs/detect/exp/labels
beach/results
beach/results/empty


######################################

fetch_clips.py - retrieve video clips
  this currently uses wget, assuming the video clip is pulled from another site, change as needed for system internal file references

process_clips.py - convert video clips to image stills using ffmpeg
  this currently uses a lock file to limit ffmpeg to running sequentially on files, this can be altered/threaded to suit system/performance

thumb2txt.py - batch(or not depending on system/performance) process image files with object detection, creates summary txt files

txt2db.py - use filename to carry forward camera id and datetime with summary detection info in csv files


