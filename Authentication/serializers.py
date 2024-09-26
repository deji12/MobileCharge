from rest_framework import serializers
from .models import User

class UserInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'vehicle_type', 'phone', 'profile_image', 'is_active', 'is_superuser', 'date_joined']

