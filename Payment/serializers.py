from rest_framework.serializers import ModelSerializer
from .models import Invoice
from Booking.serializers import BookingSerializer

class InvoiceSerializer(ModelSerializer):
    booking = BookingSerializer()
    
    class Meta:
        model = Invoice
        fields = '__all__'