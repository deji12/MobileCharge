from django.contrib import admin
from django.urls import path, include
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
   openapi.Info(
      title="Mobile charge API",
      default_version='v1',
      description="Below, you will find all endpoints and documentation to each of these endpoints",
    #   terms_of_service="https://www.google.com/policies/terms/",
      contact=openapi.Contact(email="adesolaayodeji53@gmail.com"),
      license=openapi.License(name="BSD License"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
   path('admin/', admin.site.urls),
   path('api/auth/', include('Authentication.urls')),
   path('api/chat/', include('Chat.urls')),
   path('api/booking/', include('Booking.urls')),

   path('swagger<format>/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
   path('', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
   path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]
