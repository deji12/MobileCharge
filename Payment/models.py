from django.db import models
from Booking.models import Booking
import uuid
from taggit.managers import TaggableManager

class PricingPlans(models.Model):

    title = models.CharField(max_length=20)
    price = models.IntegerField(default=0, null=True, blank=True)
    description = models.TextField()
    features = TaggableManager()

    def __str__(self):
        return self.title
