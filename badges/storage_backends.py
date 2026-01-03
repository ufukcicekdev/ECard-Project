from storages.backends.s3boto3 import S3Boto3Storage
import os


class MediaStorage(S3Boto3Storage):
    def __init__(self, **settings):
        # Use environment variables for DigitalOcean Spaces
        settings.setdefault('access_key', os.environ.get('AWS_ACCESS_KEY_ID'))
        settings.setdefault('secret_key', os.environ.get('AWS_SECRET_ACCESS_KEY'))
        settings.setdefault('bucket_name', os.environ.get('AWS_STORAGE_BUCKET_NAME'))
        settings.setdefault('region_name', os.environ.get('AWS_S3_REGION_NAME', 'fra1'))
        settings.setdefault('endpoint_url', os.environ.get('AWS_S3_ENDPOINT_URL', 'https://fra1.digitaloceanspaces.com'))
        
        # Additional settings for DigitalOcean Spaces
        settings.setdefault('default_acl', 'public-read')
        settings.setdefault('file_overwrite', False)
        
        super().__init__(**settings)