from django.contrib import admin
from .models import *
from import_export.admin import ImportExportModelAdmin

class PricingPlansAdmin(ImportExportModelAdmin):
    list_display = ['id', 'title', 'price', 'description']

admin.site.register(PricingPlans, PricingPlansAdmin)

class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ['user', 'plan', 'stripe_subscription_id', 'status', 'created_at', 'expires_at']

admin.site.register(Subscription, SubscriptionAdmin)