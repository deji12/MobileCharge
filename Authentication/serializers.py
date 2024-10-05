from rest_framework import serializers
from .models import User

class UserInfoSerializer(serializers.ModelSerializer):
    profile_image = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'phone', 'is_active', 'is_superuser', 'date_joined', 'profile_image']

    def get_profile_image(self, obj):
        return obj.profile_image_url()
