from .models import User
from django.contrib.auth import authenticate
from django.conf import settings
from rest_framework.exceptions import AuthenticationFailed
from django.conf import settings
from django.core.mail import EmailMessage

def send_password_reset_code(email, code):

    email_message = EmailMessage(
        'Your Password Reset Code',
        f'Your password reset code is {code}',
        settings.EMAIL_HOST_USER,
        [email]
    )
    email_message.fail_silently = True
    email_message.send()