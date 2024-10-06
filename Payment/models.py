from django.db import models
from Booking.models import Booking
import uuid

class Invoice(models.Model):
    invoice_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE)
    amount = models.FloatField(null=True, blank=True)
    paid = models.BooleanField(default=False)
    date = models.DateField(null=True, blank=True, auto_now_add=True)
