import subprocess
from glob import glob
from minio import Minio

# Initialize minioClient with an endpoint and access/secret keys.
client = Minio(
    #amazon region probably same as below, but check
    "s3.us-west-2.amazonaws.com",
    access_key="XXXXXXXXXXXXXXXXXXXX",
    secret_key="XxXxxxxxxXxxxXxxXXXXxxxxXXXXXXXXxxxxxxxx",
)

this_bucket = "webcoos"

#example code loop below executed periodically from scheduled cron job
# - returns jpg files from a default target folder
# - reorganizes the filename parts to be substituted in the path to be placed at the target amazon bucket storage
# - moves the processed file to the processed folder

allFiles = sorted(glob('/home/pi/project/photos/*.jpg'))
if len(allFiles) == 0:
    print ('no jpg files to process');
    exit()

for file in allFiles:
    print (file)

    #filename format - asset(location), datetime in GMT(Z) timezone - rosemontpeace_2024-02-09_03:10:00Z.jpg

    filename = file.split('/')[-1]
    #print (filename)

    filepath = file.split('_')
    #print (filepath)

    camsite = filepath[0].split('/')[-1]
    #print (camsite)

    thisDate = filepath[1][-10:]

    thisYear = filepath[1][0:4]
    #print (thisYear)

    thisMonth = filepath[1][5:7]
    #print (thisMonth)

    thisDay = filepath[1][8:10]
    #print (thisDay)

    #example str_path using groups/assets/feeds/products/elements pathing convention - change as specifics as needed
    str_path = 'media/sources/webcoos/groups/nerrs/assets/rosemontpeace/feeds/raw-video-data/products/10-minute-stills/elements/'+thisYear+'/'+thisMonth+'/'+thisDay+'/'+filename
    print (str_path)

    #put an object
    minioClient.fput_object(this_bucket, str_path, file)

    #transfer file to processed folder so not processed again 
    cmd = 'mv '+file+' /home/pi/project/processed/'+filename
    returncode = subprocess.call(cmd,shell=True)
