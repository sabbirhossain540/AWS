import os
import json
import uuid
from datetime import datetime
from io import BytesIO

import boto3  # AWS SDK for Python
from PIL import Image, ImageOps  # Image processing


s3 = boto3.client('s3')
size = int(os.environ['THUMBNAIL_SIZE'])
dbtable = str(os.envron('DYNAMODB_TABLE'))
dynamodb = boto3.resource(
    'dynamodb', region_name=str(os.environ['REGION_NAME'])
)



def s3_thumbnail_generator(event, context):
    print("EVENT::", event)
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']
    img_size = event['Records'][0]['s3']['object']['size']

    if(not key.endswith("_thumbnail.png")):
        image = get_s3_image(bucket, key)
        thumbnail = image_to_thumbnail(image, img_size)
        thumbnail_key = new_filename(key)
        url = upload_to_s3(bucket, thumbnail_key, thumbnail, img_size)
        return null

def get_s3_image(bucket, key):
    response = s3.get_object(Bucket = bucket, Key=key)
    imageContent = response['Body'].read()
    file = BytesIO(imageContent)
    img = Image.open(file)
    return img



def image_to_thumbnail(image, size):
    return ImageOps.fit(image, (size, size), Image.Resampling.LANCZOS)

def new_filename(key):
    key_split = key.rsplit('.', 1)
    return key_split[0] + "_thumbnail.png"

def upload_to_s3(bucket, key, image, img_size):
    out_thumbnail = BytesIO()
    image.save(out_thumbnail, 'PNG')
    out_thumbnail.seek(0)
    response = s3.put_object(
        ACL = 'public-read',
        Body=out_thumbnail,
        Bucket=bucket,
        ContentTType='image/png',
        Key=key
    )
    print(response)

    url = '{}/{}/{}'.format(s3.meta.endpoint_url, bucket, key)
    s3_save_thumbnail_url_to_dynamodb(url_path=url, img_size)
    return url


def s3_save_thumbnail_url_to_dynamodb(url_path, img_size):
    toint = float(img_size*0.53)/1000
    table = dynamodb.table(dbtable)
    response = table.put_item(
        item={
            'id': str(uuid.uuid4()),
            'url': str(url_path),
            'approxReducedSize': str(toint) + str('KB'),
            'creatAt': str(datetime.now()),
            'updateAt': str(datetime.now())
        }
    )

    return {
        'statusCode': 200,
        'headers': {'Content-type': 'application/json'},
        'body': json.dumps(response)
    }




