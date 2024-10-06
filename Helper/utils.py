from django.conf import settings
import cloudinary
import cloudinary.uploader
from django.conf import settings
from django.conf import settings
from django.core.mail import EmailMessage
    
class EmailUser:
    
    def __init__(self, email, code=None, invoice=None):
        self.email = email

        if code is not None:
            self._set_reset_code_email(code)
        elif invoice is not None:
            self._set_purchase_confirmation_email(invoice)

    def _set_reset_code_email(self, code):
        self.code = code
        self.subject = 'Your Password Reset Code'
        self.message = f'Your password reset code is {self.code}.'

    def _set_purchase_confirmation_email(self, invoice):
        self.subject = 'Thank you for your purchase'
        self.message = (
            f'Your payment for the booking has been successfully verified. Below are the details of your booking and purchase:\n\n'
            f'BOOKING DETAILS:\n\n'
            f'Booking Type: {invoice.booking.booking_type}\n'
            f'Driver Name: {invoice.booking.driver.get_full_name()}\n'
            f'Driver Phone Number: {invoice.booking.driver.phone}\n\n'
            f'PURCHASE DETAILS:\n\n'
            f'Invoice ID: {invoice.invoice_id}\n'
            f'Amount: ${invoice.amount:.2f}\n'
            f'Date: {invoice.date.strftime("%B %d, %Y")}\n\n'
            'Thank you for your purchase!'
        )

    def send(self):
        email_message = EmailMessage(
            self.subject,
            self.message,
            settings.EMAIL_HOST_USER,
            [self.email]
        )
        email_message.fail_silently = True
        email_message.send()


cloudinary.config(
    cloud_name = settings.CLOUDINARY_CLOUD_NAME,
    api_key = settings.CLOUDINARY_API_KEY,
    api_secret = settings.CLOUDINARY_API_SECRET
)

def upload_image_to_cloudinary_and_get_url(image):

    response = cloudinary.uploader.upload(image)
    uploaded_image_url = response['secure_url']

    return uploaded_image_url
