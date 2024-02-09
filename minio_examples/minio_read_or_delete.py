from minio import Minio

# Initialize minioClient with an endpoint and access/secret keys.
client = Minio(
    #amazon region probably same as below, but check
    "s3.us-west-2.amazonaws.com",
    access_key="XXXXXXXXXXXXXXXXXXXX",
    secret_key="XxXxxxxxxXxxxXxxXXXXxxxxXXXXXXXXxxxxxxxx",
)

this_bucket = "webcoos"

#example prefix path using groups/assets/feeds/products/elements pathing convention - change as specifics as needed
this_prefix =  "media/sources/webcoos/groups/nerrs/assets/rosemontpeace/feeds/raw-video-data/products/10-minute-stills/elements/2023/10/09/"

# List objects
objects = client.list_objects(this_bucket, prefix=this_prefix, recursive=True )

for obj in objects:

    print(
        repr({
            'bucket_name': obj.bucket_name,
            'object_name': obj.object_name
        })
    )

    #delete selected objects in for loop
    #client.remove_object(obj.bucket_name,obj.object_name)
