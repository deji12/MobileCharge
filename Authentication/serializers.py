from rest_framework import serializers
from .models import User
from Payment.models import Subscription

class UserInfoSerializer(serializers.ModelSerializer):
    profile_image = serializers.SerializerMethodField()
    subscription_type = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'phone', 'is_active', 'is_superuser', 'date_joined', 'profile_image', 'subscription_type']

    def get_profile_image(self, obj):
        return obj.profile_image_url()

    def get_subscription_type(self, obj):
        # Try to get the user's active subscription
        try:
            subscription = obj.subscription_set.get(status='active')  # Get active subscription
            return subscription.plan.title  # Return the plan title if subscription is active
        except Subscription.DoesNotExist:
            return "Visitor"  # Return 'Visitor' if no active subscription exists