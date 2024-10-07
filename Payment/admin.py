from django.contrib import admin
from .models import *
from import_export.admin import ImportExportModelAdmin

class PricingPlansAdmin(ImportExportModelAdmin):
    list_display = ['id', 'title', 'price', 'description']

admin.site.register(PricingPlans, PricingPlansAdmin)
