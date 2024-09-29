from django.conf import settings
import cloudinary
import cloudinary.uploader

cloudinary.config(
    cloud_name = settings.CLOUDINARY_CLOUD_NAME,
    api_key = settings.CLOUDINARY_API_KEY,
    api_secret = settings.CLOUDINARY_API_SECRET
)

def upload_image_to_cloudinary_and_get_url(image):

    response = cloudinary.uploader.upload(image)
    uploaded_image_url = response['secure_url']

    return uploaded_image_url
