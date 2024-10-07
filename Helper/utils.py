import cloudinary
import cloudinary.uploader
from django.conf import settings
import urllib.parse
from django.core.mail import EmailMessage
    
cloudinary.config(
    cloud_name = settings.CLOUDINARY_CLOUD_NAME,
    api_key = settings.CLOUDINARY_API_KEY,
    api_secret = settings.CLOUDINARY_API_SECRET
)

class EmailUser:
    
    def __init__(self, email, failed=False, code=None, booking=None):
        self.email = email
        self.failed = failed

        if code is not None:
            self._set_reset_code_email(code)
        elif booking is not None:
            self._set_purchase_confirmation_email(booking)

    def _set_reset_code_email(self, code):
        self.code = code
        self.subject = 'Your Password Reset Code'
        self.message = f'Your password reset code is {self.code}.'

    def _set_purchase_confirmation_email(self, booking):
        if not self.failed:
                self.subject = 'Nre Booking Purchase'
                self.message = (
                f'Your payment for the booking has been successfully verified. Below are the details of your booking and purchase:\n\n'
                f'BOOKING DETAILS:\n\n'
                f'Booking Type: {booking.booking_type}\n'
                f'Driver Name: {booking.driver.get_full_name()}\n'
                f'Driver Phone Number: {booking.driver.phone}\n\n'
                f'PURCHASE DETAILS:\n\n'
                f'Invoice ID: {booking.invoice_id}\n'
                f'Amount: ${booking.price:.2f}\n'
                f'Date: {booking.date.strftime("%B %d, %Y")}\n\n'
                'Thank you for your purchase!'
            )
                
        else:
            self.subject = 'Failed Booking Purchase'
            self.message = (
                f'Your payment for the booking failed and could not be verified.'
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

def upload_image_to_cloudinary_and_get_url(image):

    response = cloudinary.uploader.upload(image)
    uploaded_image_url = response['secure_url']

    decoded_url = urllib.parse.unquote(uploaded_image_url)
    
    return decoded_url

"""
+16088646206
17712249021
17747753620


# need
51926557090
27842732703
254727391192
528661953584
584168798965
2250504409950
5511960957418
12607274717
13504441442
13676007267
13822886028
13822887291
13822887522
16837030638
13825006523
13824572828
18352097658
13825006271
13825006394
13825007032
15822602049
8801715946986
15744751677
50374893305
50374893305
2348147868139
38651300030
"""