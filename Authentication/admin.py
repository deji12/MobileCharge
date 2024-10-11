from django.contrib import admin
from .models import *

class UserAdmin(admin.ModelAdmin):

    list_display = ["email", "id", "first_name", "last_name", "phone", "is_active", "is_staff", "is_superuser", "date_joined"]
    search_fields = ["username", "email", "first_name", "last_name"]
    list_filter = ["is_staff", "is_superuser", "is_active", "date_joined"]

admin.site.register(User, UserAdmin)

admin.site.register(PasswordResetCode)