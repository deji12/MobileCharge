from django.db import models
from Authentication.models import User

class Driver(models.Model):

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    number_of_completed_bookings = models.IntegerField(default=0)
    number_of_pending_bookings = models.IntegerField(default=0)
    