from django.db import models
from Booking.models import Booking
from Authentication.models import User
from taggit.managers import TaggableManager

class PricingPlans(models.Model):

    title = models.CharField(max_length=20)
    price = models.IntegerField(default=0, null=True, blank=True)
    stripe_price_id = models.CharField(max_length=225, null=True, blank=True)
    description = models.TextField()
    features = TaggableManager()

    def __str__(self):
        return self.title

class Subscription(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    plan = models.ForeignKey(PricingPlans, on_delete=models.CASCADE, null=True, blank=True)
    stripe_subscription_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
    status = models.CharField(max_length=20, choices=[
        ('active', 'Active'),
        ('canceled', 'Canceled'),
        ('expired', 'Expired'),
        ('payment_failed', 'Payment Failed'),
    ], default='inactive')
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)