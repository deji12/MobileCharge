from django.shortcuts import render
from .serializers import BookingSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import permission_classes
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Booking
from Helper.utils import upload_image_to_cloudinary_and_get_url
from Driver.models import Driver
from django.conf import settings
from django.core.mail import EmailMessage
from Payment.models import PricingPlans, Subscription
from django.utils import timezone
from datetime import datetime


@swagger_auto_schema(
    method='post',
    operation_description="Create a new booking for a user. Fields such as location, car_make, battery_type, and vehicle_image are required.",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['location', 'car_make', 'battery_type', 'vehicle_image'],
        properties={
            'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID of the booking'),
            'location': openapi.Schema(type=openapi.TYPE_STRING, description='Location of the booking'),
            'car_make': openapi.Schema(type=openapi.TYPE_STRING, description='Car make/model'),
            'battery_type': openapi.Schema(type=openapi.TYPE_STRING, description='Type of car battery'),
            'battery_level': openapi.Schema(type=openapi.TYPE_INTEGER, description='Battery level as a percentage (optional)'),
            'kilometers_left': openapi.Schema(type=openapi.TYPE_NUMBER, description='Kilometers left for the vehicle (optional)'),
            'vehicle_image': openapi.Schema(type=openapi.TYPE_FILE, description='Vehicle image file'),
            'description': openapi.Schema(type=openapi.TYPE_STRING, description='Additional details about the booking (optional)'),
            'booking_type': openapi.Schema(type=openapi.TYPE_STRING, description='Booking type (Normal or Emergency)', enum=['Normal', 'Emergency']),
        }
    ),
    responses={
        201: openapi.Response(
            description="Booking created successfully",
            schema=BookingSerializer()
        ),
        400: openapi.Response(description="Bad request. Missing required fields."),
        401: openapi.Response(description="Unauthorized. User not authenticated."),
    },
    operation_summary = "Create Booking"
)
@permission_classes([IsAuthenticated])
@api_view(["POST"])
def create_booking(request):
    
    user = request.user

    # get payload data
    plan_id = request.data.get('plan_id')
    location = request.data.get('location')
    car_make = request.data.get('car_make')
    battery_type = request.data.get('battery_type')
    battery_level = request.data.get('battery_level')
    kilometers_left = request.data.get('kilometers_left')
    vehicle_image = request.FILES.get('vehicle_image')
    description = request.data.get('description')
    booking_type = request.data.get('booking_type')

    # New date and time fields from the request
    year = request.data.get('year')
    month = request.data.get('month')
    day = request.data.get('day')
    hour = request.data.get('hour')
    minute = request.data.get('minute')
    

    # verify that required fields are present
    if not (location and battery_type and car_make and vehicle_image):
        return Response({"error": "Fill reuired fields."}, status=status.HTTP_400_BAD_REQUEST)
    
    # get the last created driver (assuming there is only one driver)
    driver = Driver.objects.last()

    try:
        # get the pricing plan detail
        plan = PricingPlans.objects.get(id=int(plan_id))
    
    except:
        return Response(
            {'error': 'Invalid plan_id'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # create a new booking object and save it to the database
    booking = Booking(
        user = user,
        location=location,
        battery_type = battery_type,
        car_make = car_make,
        driver = driver.user,
        price = plan.price
    )

    if year and month and day and hour and minute:

        try:
            scheduled_date_and_time = datetime(
                year=int(year),
                month=int(month),
                day=int(day),
                hour=int(hour),
                minute=int(minute),
                tzinfo=timezone.get_current_timezone()
            )

            # format the time properly
            scheduled_date_and_time = timezone.make_aware(scheduled_date_and_time, timezone.get_current_timezone())

            # Set the booking's scheduled date and time
            booking.scheduled_date_and_time = scheduled_date_and_time

        except (TypeError, ValueError) as e:
            return Response({"error": "Invalid date or time provided."}, status=400)
    
    # update driver pending bookings count
    driver.number_of_pending_bookings += 1
    driver.save()

    booking.vehicle_image = upload_image_to_cloudinary_and_get_url(vehicle_image)

    if battery_level:
        booking.battery_level = battery_level
    
    if kilometers_left:
        booking.kilometers_left = kilometers_left

    if description:
        booking.description = description

    if booking_type:
        booking.booking_type = booking_type

    booking.save()

    serializer = BookingSerializer(booking)

    response = {
        "message": "Booking created successfully. You will be notified when your booking is approved",
        "booking": serializer.data,
    }
    return Response(response, status=status.HTTP_201_CREATED)

@swagger_auto_schema(
    method='get',
    operation_description="Retrieve a list of bookings with the given status from the URL. The response will be ordered by the most recent date (descending). Acceptable statuses: Pending, Approved, Completed.",
    responses={
        200: openapi.Response(
            description="List of bookings",
            schema=BookingSerializer(many=True)
        ),
        400: openapi.Response(description="Invalid booking status."),
        401: openapi.Response(description="Unauthorized"),
    },
    operation_summary="List bookings by status"
)
@permission_classes([IsAuthenticated])
@api_view(["GET"])
def get_bookings(request, booking_status):

    if booking_status.lower() not in ['pending', 'approved', 'completed']:
        return Response({"error": "Invalid booking status."}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        bookings = Booking.objects.filter(status=booking_status).order_by("-date")  # Most recent first
        serializer = BookingSerializer(bookings, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)
    except Booking.DoesNotExist:
        return Response({"error": "No bookings found for the given status."}, status=status.HTTP_404_NOT_FOUND)
    
@swagger_auto_schema(
    method='get',
    operation_description="Retrieve detailed information for a specific booking by its ID.",
    responses={
        200: openapi.Response(
            description="Booking retrieved successfully",
            schema=BookingSerializer()
        ),
        404: openapi.Response(
            description="Booking not found",
            examples={
                "application/json": {
                    "error": "Booking with id: '1' not found."
                }
            }
        )
    },
    operation_summary = "Get booking",
    manual_parameters=[
        openapi.Parameter(
            'booking_id',
            openapi.IN_PATH,
            description="ID of the booking to retrieve",
            type=openapi.TYPE_INTEGER,
            required=True
        )
    ]
)
@permission_classes([IsAuthenticated])
@api_view(["GET"])
def get_booking(request, booking_id):

    try:
        booking = Booking.objects.get(id=booking_id)
        serializer = BookingSerializer(booking)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except:
        return Response({"error": f"Booking with id: '{booking_id}' not found."}, status=status.HTTP_404_NOT_FOUND)

@swagger_auto_schema(
    method='patch',
    operation_description="Update the status of a booking (choices: Pending, Approved, Completed) and update the driver's booking counts.",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'status': openapi.Schema(
                type=openapi.TYPE_STRING,
                enum=["Pending", "Completed", "Approved"],  # Indicate the valid choices
                description="New status of the booking. Choices are 'Pending', 'Approved', or 'Completed'."
            )
        },
        required=['status'],
        example={
            "status": "Pending", 
        }
    ),
    responses={
        200: openapi.Response(
            description="Booking status updated successfully",
            examples={
                "application/json": {
                    "message": "Booking status updated successfully",
                    "booking": {
                        "id": 1,
                        "status": "confirmed",
                        # Other fields from BookingSerializer
                    },
                    "driver_name": "John Doe"
                }
            },
        ),
        400: openapi.Response(description="Invalid request (e.g., status not provided)"),
        404: openapi.Response(description="Booking not found"),
    },
    # tags=["Bookings"],  # Group this under 'Bookings' in the API docs
    operation_summary="Update booking status (Pending or Completed) and modify driver's booking counts"
)  
@permission_classes([IsAuthenticated])
@api_view(["PATCH"])
def update_booking_status(request, invoice_id):
    
    try:
        booking = Booking.objects.get(invoice_id=invoice_id)
        driver = Driver.objects.get(user=booking.driver)

        new_status = request.data.get("status")

        if not new_status:
            return Response({"error": "Status is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        new_status = new_status.capitalize()

        # update driver stats accourdingly
        if new_status == "Pending":
            driver.number_of_pending_bookings += 1
            driver.number_of_completed_bookings -= 1

        elif new_status == "Approved" and booking.status != "Approved":

            # make sure to only send email if user is not subscribed
            if not Subscription.objects.filter(user=booking.user, status='active').exists():

                # send email to user
                email_message = EmailMessage(
                    "Booking request approved",
                    f"Your booking request with ID {booking.invoice_id} has been approved. Please make use of the link below make payment and complete your booking request\n\n{settings.CHECKOUT_URL}?booking_invoice_id={booking.invoice_id}",
                    settings.EMAIL_HOST_USER,
                    [booking.user.email]
                )
                email_message.fail_silently = True
                email_message.send()

            else:
                # set booking as paid if user is a membership user
                booking.paid = True

        elif new_status == "Completed" and booking.status != "Completed":
            driver.number_of_pending_bookings -= 1
            driver.number_of_completed_bookings += 1
        
        driver.save()

        # Update the status field of the booking
        booking.status = new_status
        booking.save()

        serializer = BookingSerializer(booking)
        response = {
            "message": "Booking status updated successfully",
            "booking": serializer.data,
        }
        return Response(response, status=status.HTTP_200_OK)
        
        
    except Booking.DoesNotExist:
        return Response({"error": f"Booking with invoice id: '{invoice_id}' not found."}, status=status.HTTP_404_NOT_FOUND)