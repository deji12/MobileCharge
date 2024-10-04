from django.db import models
from Authentication.models import User

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
    description = models.TextField()
    booking_type = models.CharField(max_length=10, choices=BOOKING_TYPE, default='Normal')
    status = models.CharField(max_length=10, choices=STATUS, default='Pending')

    def __str__(self):
        return f"{self.user} - {self.car_make}"
