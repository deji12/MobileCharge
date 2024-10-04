from .models import Driver
from Authentication.serializers import UserInfoSerializer
from rest_framework.serializers import ModelSerializer

class DriverSerializer(ModelSerializer):
    user = UserInfoSerializer()

    class Meta:
        model = Driver
        fields = '__all__'