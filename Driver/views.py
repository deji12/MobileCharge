from django.shortcuts import render
from Authentication.models import User
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from .models import Driver
from .serializers import DriverSerializer
from rest_framework import status
from rest_framework.response import Response

from django.shortcuts import render
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.response import Response
from .models import Driver
from .serializers import DriverSerializer
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

@swagger_auto_schema(
    method="get",  # The method of the API view
    operation_description="Retrieve a list of all drivers",  # Description of the operation
    responses={  # Possible responses for the view
        200: openapi.Response(
            description="List of drivers",
            schema=DriverSerializer(many=True),  # The schema for the response
        ),
        401: "Unauthorized",  # Example of another response status
    },
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_drivers(request):
    """
    Retrieves all drivers from the system. 
    Requires authentication.

    Returns a list of drivers.
    """
    drivers = Driver.objects.all()
    serializer = DriverSerializer(drivers, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

@swagger_auto_schema(
    method='get',
    operation_description="Retrieve the details of the last driver in the system.",
    responses={
        200: openapi.Response(
            description="Successfully retrieved the last driver.",
            examples={
                "application/json": {
                    "user": {
                        "id": 1,
                        "username": "johndoe",
                        "email": "johndoe@example.com",
                        "first_name": "John",
                        "last_name": "Doe",
                        "phone": "+1234567890",
                        "is_active": True,
                        "is_superuser": False,
                        "date_joined": "2023-10-07T12:34:56",
                        "profile_image": "https://example.com/media/images/profile.jpg"
                    },
                    "number_of_completed_bookings": 5,
                    "number_of_pending_bookings": 2
                }
            }
        ),
        404: openapi.Response(
            description="No drivers found.",
            examples={
                "application/json": {
                    "error": "No drivers found."
                }
            }
        ),
    },
    operation_summary="Retrieve the last driver"
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_last_driver(request):

    try:
        last_driver = Driver.objects.last()
        serializer = DriverSerializer(last_driver)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except:
        return Response({"error": "No drivers found."}, status=status.HTTP_404_NOT_FOUND)