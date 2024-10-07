from rest_framework.serializers import ModelSerializer
from .models import PricingPlans
from Booking.serializers import BookingSerializer
from taggit.serializers import TagListSerializerField

class PricingSerializer(ModelSerializer):
    features = TagListSerializerField()

    class Meta:
        model = PricingPlans
        fields = '__all__'