import boto3
import json
import base64
import re
from datetime import datetime, timedelta, timezone
from email import policy
from email.parser import BytesParser

# ✅ Manually set AWS keys for the **target** S3 bucket
TARGET_AWS_ACCESS_KEY = "zzz"
TARGET_AWS_SECRET_KEY = "zzz"
TARGET_REGION = "us-west-2"

# ✅ Initialize S3 clients
s3_client = boto3.client("s3")  # For reading from the source bucket (us-east-1)

# ✅ Use explicit credentials for writing to the target bucket in `us-west-2`
s3_target_client = boto3.client(
    "s3",
    region_name=TARGET_REGION,
    aws_access_key_id=TARGET_AWS_ACCESS_KEY,
    aws_secret_access_key=TARGET_AWS_SECRET_KEY,
)

# ✅ Define S3 bucket and group
SOURCE_BUCKET = "zzz"  # Source bucket in us-east-1
TARGET_BUCKET = "zzz"  # Target bucket in us-west-2 (different owner)
GROUP = "zzz"  # Change as needed

from datetime import datetime, timedelta

def convert_to_utc(et_timestamp):
    """Converts an Eastern Time timestamp to UTC using exact DST dates."""
    # ✅ Parse the ET timestamp
    local_dt = datetime.strptime(et_timestamp, "%Y-%m-%d %H:%M:%S")

    # ✅ Calculate DST transition dates for the given year
    year = local_dt.year
    dst_start = datetime(year, 3, 8, 2) + timedelta(days=(6 - datetime(year, 3, 8).weekday()))  # 2nd Sunday in March
    dst_end = datetime(year, 11, 1, 2) + timedelta(days=(6 - datetime(year, 11, 1).weekday()))  # 1st Sunday in November

    # ✅ Determine if timestamp is in DST
    is_dst = dst_start <= local_dt < dst_end
    et_offset = timedelta(hours=-4) if is_dst else timedelta(hours=-5)  # EDT = UTC-4, EST = UTC-5

    # ✅ Convert to UTC
    utc_dt = local_dt - et_offset  # Shift to UTC
    return utc_dt.strftime("%Y-%m-%d_%H:%M:%SZ")  # Format for filename


def extract_subject(email_content):
    """Extracts the subject line from the email."""
    msg = BytesParser(policy=policy.default).parsebytes(email_content)
    return msg["subject"] if msg["subject"] else "unknown_subject"

def parse_subject(subject):
    """Parses the subject line to extract timestamp and camera ID."""
    #match = re.match(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}),\s*([\w\d-]+)", subject)

    """Parses the subject line to extract timestamp and camera ID,
    handling both comma and dash separators."""
    match = re.match(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\s*[,-]\s*([\w\d-]+)", subject)
    if match:
        et_timestamp, camera_id = match.groups()
        
        # ✅ Convert to UTC
        utc_timestamp = convert_to_utc(et_timestamp)

        # ✅ Handle camera ID overrides
        if camera_id == "folly6th":
            camera_id = "folly6thavenue"
        elif camera_id == "scmm":
            camera_id = "georgetownscmm"
            global group  # Modify the global group variable
            group = "scmm"            
        else:
            print(f"Camera ID '{camera_id}' is not allowed. Exiting without uploading.")
            return None, None  # 🚨 Exit without processing

        return camera_id, utc_timestamp
    return None, None  # 🚨 Exit if parsing fails

def extract_attachments(email_content, subject):
    """Extracts image attachments and renames them based on email subject."""
    msg = BytesParser(policy=policy.default).parsebytes(email_content)
    attachments = []
    
    camera_id, utc_timestamp = parse_subject(subject)

    # ✅ If the camera ID is invalid, exit
    if not camera_id or not utc_timestamp:
        return None, None, None

    for part in msg.iter_attachments():
        if part.get_content_maintype() == "image":  # Only process images
            original_filename = part.get_filename()
            
            # ✅ Generate new filename with UTC time: `jc1_2025-03-02_15:13:19Z.jpg`
            new_filename = f"{camera_id}_{utc_timestamp}.jpg"
            content = part.get_payload(decode=True)
            attachments.append((new_filename, content))

            print(f"Renaming file: {original_filename} → {new_filename}")

    return attachments, camera_id, utc_timestamp  # ✅ Include utc_timestamp


def lambda_handler(event, context):
    try:
        print("Received event:", json.dumps(event, indent=4))  # Debugging

        # ✅ Determine whether the event is from SES or S3
        if "Records" in event and "s3" in event["Records"][0]:
            print("Processing S3 event")
            record = event["Records"][0]
            object_key = record["s3"]["object"]["key"]
            bucket_name = record["s3"]["bucket"]["name"]
        else:
            raise ValueError("Unknown event format: missing S3 event details")

        print(f"Attempting to retrieve S3 object: {object_key} from {bucket_name}")

        # ✅ Read email file from S3 (us-east-1)
        response = s3_client.get_object(Bucket=bucket_name, Key=object_key)
        email_content = response["Body"].read()

        # ✅ Extract email subject
        subject = extract_subject(email_content)
        print(f"Email Subject: {subject}")

        # ✅ Extract and rename attachments
        attachments, camera_id, utc_timestamp = extract_attachments(email_content, subject)

        # ✅ If the camera ID is invalid, exit
        if not camera_id or not utc_timestamp:
            return {"statusCode": 400, "body": json.dumps("Camera ID is not allowed. Skipping upload.")}

        # ✅ Upload attachments using Boto3 to **different region (us-west-2)**
        for filename, content in attachments:
            # ✅ Construct file path based on the camera ID and timestamp
            file_path = f"media/sources/webcoos/groups/{GROUP}/assets/{camera_id}/feeds/raw-video-data/products/10-minute-stills/elements/{utc_timestamp[:4]}/{utc_timestamp[5:7]}/{utc_timestamp[8:10]}/{filename}"

            s3_target_client.put_object(
                Bucket=TARGET_BUCKET,
                Key=file_path,  # Store using the structured path
                Body=content,
                ContentType="image/jpeg"
            )
            print(f"Uploaded {filename} to {TARGET_BUCKET}/{file_path} in us-west-2")

        return {"statusCode": 200, "body": json.dumps("Email processed successfully.")}

    except Exception as e:
        print(f"Error processing email: {e}")
        return {"statusCode": 500, "body": json.dumps(f"Error: {str(e)}")}
