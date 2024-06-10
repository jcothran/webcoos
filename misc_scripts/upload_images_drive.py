import subprocess
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from oauth2client.service_account import ServiceAccountCredentials
import os
import re
import time

#this script will find Reolink ftp'd files with filename format location_00_YYYYMMDD*.jpg and forward them to a target google drive folder split up by location name and datetime, then remove the same file from the local server to conserve space

# Authenticate and create PyDrive client
# more info see https://www.youtube.com/watch?v=tamT_iGoZDQ

gauth = GoogleAuth()
scope = ['https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('xxx-xxxxxxx-xxxxxxxxxxxx-xxxxxxxxxxxx.json', scope)
# ID of the existing parent folder in Google Drive
existing_parent_folder_id = 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
gauth.credentials = creds
drive = GoogleDrive(gauth)

# Function to create folder recursively starting from an existing folder ID
def create_folder_recursive(drive, folder_path, parent_id=None):
    folders = folder_path.split('/')
    current_parent_id = parent_id
    for folder in folders:
        folder_exists = False
        # Check if the folder exists
        file_list = drive.ListFile({'q': "'{}' in parents and trashed=false".format(current_parent_id)}).GetList()
        for file in file_list:
            if file['title'] == folder and file['mimeType'] == 'application/vnd.google-apps.folder':
                folder_exists = True
                current_parent_id = file['id']
                break
        # Create the folder if it doesn't exist
        if not folder_exists:
            new_folder = drive.CreateFile({'title': folder, 'parents': [{'kind': 'drive#fileLink', 'id': current_parent_id}], 'mimeType': 'application/vnd.google-apps.folder'})
            new_folder.Upload()
            current_parent_id = new_folder['id']
    return current_parent_id


# Array of folder names to search for in the find command and as starting target folder names
folder_names = ['Hoboken', 'camden', 'RISE E1 Outdoor']

# Loop through each folder name
for folder_name in folder_names:
    # Run the find command to get the list of files for the current folder name
    #find_command = f'find /home/ftp -type f -name "{folder_name}_00_2024051*.jpg"'
    find_command = f'find /home/ftp -type f -mtime +5 -name "{folder_name}_00_*.jpg"' #SET datetime here as needed, -mtime +5 = files older than 5 days
    output = subprocess.check_output(find_command, shell=True)
    file_paths = output.decode('utf-8').split('\n')

    # Upload each file to the corresponding date folder if it doesn't already exist
    for file_path in file_paths:
        if file_path:
            file_name = os.path.basename(file_path)
            # Extract date from filename using regular expression
            match = re.search(r'(\d{4})(\d{2})(\d{2})', file_name)
            if match:
                year, month, day = match.groups()
                date_folder_path = f'{folder_name}/{year}/{month}/{day}'
                # Create the folder structure if it doesn't exist and get the ID of the leaf folder
                leaf_folder_id = create_folder_recursive(drive, date_folder_path, existing_parent_folder_id)
                # Check if the file already exists in the leaf folder
                file_exists = False
                file_list = drive.ListFile({'q': "'{}' in parents and trashed=false".format(leaf_folder_id)}).GetList()
                for file in file_list:
                    if file['title'] == file_name:
                        file_exists = True
                        break
                # If the file doesn't already exist, upload it to the leaf folder
                if not file_exists:
                    file = drive.CreateFile({'title': file_name, 'parents': [{'kind': 'drive#fileLink', 'id': leaf_folder_id}]})
                    file.SetContentFile(file_path)
                    file.Upload()
                    print('File uploaded successfully:', file['title'])
                    print('Link to the file:', file['alternateLink'])
                    #os.remove(file_path)
                    try:
                        os.remove(file_path)
                        #time.sleep(1)
                    except OSError as e: # name the Exception `e`
                         print ("Failed with:", e.strerror) # look what it says
                         print ("Error code:", e.code)
                    print('File removed from the file system:', file_path)
                else:
                    print(f'File already exists on Google Drive: {file_name}')
                    #os.remove(file_path)
                    try:
                        os.remove(file_path)
                        #time.sleep(1)
                    except OSError as e: # name the Exception `e`
                         print ("Failed with:", e.strerror) # look what it says
                         print ("Error code:", e.code)
                    print('File removed from the file system:', file_path)
            else:
                print(f'Unable to extract date from filename: {file_name}')
