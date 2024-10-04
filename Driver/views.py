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
    tags=["Drivers"]  # Group this endpoint under "Drivers" in the documentation
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