from django.db import models
from Authentication.models import User
import uuid

STATUS = (
    ('Pending', 'Pending'),
    ('Approved', 'Approved'),
    ('Completed', 'Completed'),
)

BOOKING_TYPE = (
    ('Normal', 'Normal'),
    ('Emergency', 'Emergency'),
)

class Booking(models.Model):

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    driver = models.ForeignKey(User, related_name='booking_driver', null=True, blank=True, on_delete=models.CASCADE)
    location = models.CharField(max_length=225)
    car_make = models.CharField(max_length=225)
    battery_type = models.CharField(max_length=50)
    battery_level = models.PositiveSmallIntegerField(default=0)
    kilometers_left = models.FloatField(default=0)
    date = models.DateTimeField(auto_now_add=True)
    vehicle_image = models.URLField()
    description = models.TextField(null=True, blank=True)
    booking_type = models.CharField(max_length=10, choices=BOOKING_TYPE, default='Normal')

    invoice_id = models.UUIDField(null=True, blank=True, default=uuid.uuid4, editable=False)
    price = models.FloatField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS, default='Pending')
    paid = models.BooleanField(default=False)
    scheduled_date_and_time = models.DateTimeField(null=True, blank=True)
    date = models.DateField(null=True, blank=True, auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {self.car_make}"
