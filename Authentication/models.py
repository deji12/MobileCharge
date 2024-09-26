from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from datetime import timedelta
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(max_length=20, null=True, blank=True)
    email = models.EmailField(unique=True, help_text="The user's unique email address.")
    first_name = models.CharField(max_length=30, default='', null=True, blank=True, help_text="The user's first name.")
    last_name = models.CharField(max_length=30, default='', null=True, blank=True, help_text="The user's last name.")
    
    phone = models.CharField(max_length=15, default='', null=True, blank=True, help_text="The user's phone number.")
    profile_image = models.FileField(upload_to="profile-photos/", null=True, blank=True, help_text="User's profile image")
    vehicle_type = models.CharField(max_length=50, default="email")
    
    is_staff =  models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False, help_text="Indicates whether the user has all admin permissions. Defaults to False.")
    is_active = models.BooleanField(default=True, help_text="Indicates whether the user account is active. Defaults to False and user needs to verify email on signup before it can be set to True.")
    date_joined = models.DateTimeField(auto_now_add=True, help_text="The date and time when the user joined.")
    
    def __str__(self):
        return self.email
    
    def profile_image_url(self):
        """
        Gets the URL of the user's profile picture.

        Returns:
            str: The URL of the user's profile picture or a default image URL.
        """
        if self.profile_image and hasattr(self.profile_image, 'url'):
            return self.profile_image.url
        
        
        return "https://res.cloudinary.com/the-proton-guy/image/upload/v1660906962/6215195_0_pjwqfq.webp"
        
    def tokens(self):
        refresh = RefreshToken.for_user(self)
        return {
            "refresh": str(refresh),
            "access": str(refresh.access_token)
        }

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    # REQUIRED_FIELDS = ['email']

class PasswordResetCode(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_valid(self):
        return self.created_at >= timezone.now() - timedelta(minutes=10)

    def __str__(self):
        return f"{self.user.email} - {self.code}"