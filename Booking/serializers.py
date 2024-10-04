from rest_framework.serializers import ModelSerializer
from .models import Booking
from Authentication.serializers import UserInfoSerializer

class BookingSerializer(ModelSerializer):
    user = UserInfoSerializer()
    driver = UserInfoSerializer()
    
    class Meta:
        model = Booking
        fields = '__all__'