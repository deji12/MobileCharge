from django.shortcuts import render, redirect
import stripe
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import PricingPlans
from Booking.models import Booking
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .serializers import PricingSerializer
from Helper.utils import EmailUser
from django.views.decorators.csrf import csrf_exempt
from Helper.utils import upload_image_to_cloudinary_and_get_url
from django.http import HttpResponse
from Driver.models import Driver
from Authentication.models import User

# This is your test secret API key.
stripe.api_key = settings.STRIPE_SECRET_KEY


@swagger_auto_schema(
    method='get',
    operation_description="Retrieve all available pricing plans from the system.",
    responses={
        200: openapi.Response(
            description="A list of all available pricing plans.",
            examples={
                "application/json": [
                    {
                        "id": 1,
                        "title": "Basic Plan",
                        "price": 29,
                        "description": "Basic subscription plan",
                        "features": ["Feature 1", "Feature 2"]
                    },
                    {
                        "id": 2,
                        "title": "Premium Plan",
                        "price": 52,
                        "description": "Premium subscription plan",
                        "features": ["Feature 1", "Feature 2", "Feature 3"]
                    }
                ]
            }
        ),
        500: openapi.Response(
            description="An error occurred while retrieving pricing plans."
        )
    },
    operation_summary="Get all pricing plans"
)
@api_view(['GET'])
def get_pricing_plans(request):
    """
    Retrieves all available pricing plans from the system.
    """

    plans = PricingPlans.objects.all()
    serializer = PricingSerializer(plans, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


class StripeOneTimeCheckoutView(APIView):

    permission_classes = [IsAuthenticated]

    """
    Handles the creation of a Stripe one-time payment session and generates an invoice.

    This view is responsible for initiating a payment process using Stripe's checkout system. It accepts 
    a POST request containing payment details and returns a URL for the Stripe checkout session. 
    Upon successful payment, an invoice is generated and associated with a booking.

    Methods:
        post(request): 
            Creates a one-time checkout session with Stripe and generates an invoice.
    """

    @swagger_auto_schema(
        operation_description="Create a Stripe one-time checkout session for a booking payment and generate an invoice.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'plan_id': openapi.Schema(type=openapi.TYPE_STRING, description='The title of the plan being purchased'),
                'booking_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='The ID of the booking related to the payment')
            },
            required=['amount', 'plan_title', 'booking_id'],
        ),
        responses={
            200: openapi.Response(
                description="Returns the Stripe checkout session URL upon successful creation.",
                examples={
                    "application/json": {
                        "checkout_url": "https://checkout.stripe.com/pay/cs_test_a1b2c3d4e5?success=true&session_id=cs_test_a1b2c3d4e5"
                    }
                }
            ),
            400: openapi.Response(
                description="Missing required fields in the request."
            ),
            500: openapi.Response(
                description="Error occurred during checkout session creation."
            )
        },
        operation_summary="Create a one-time payment session via Stripe and generate an invoice"
    )
    def post(self, request):
        """
        Handles POST requests to create a Stripe checkout session and an associated invoice.

        Parameters:
            request (Request): The request object containing the payment details in JSON format.
                Expected fields:
                    - amount (float): The total amount to be charged (in USD).
                    - plan_title (str): The name of the plan being purchased.
                    - booking_id (int): The unique identifier for the booking.

        Returns:
            Response: A JSON response containing the checkout session URL if successful, 
                      or an error message in case of failure.

        Error Handling:
            If any required fields are missing, a 400 BAD REQUEST response is returned.
            If an error occurs during the creation of the checkout session or invoice, 
            a 500 INTERNAL SERVER ERROR response is returned.
        """
        try:
            # Retrieve payment details from the request
            plan_id = request.data.get('plan_id')
            location = request.data.get('location')
            car_make = request.data.get('car_make')
            battery_type = request.data.get('battery_type')
            battery_level = request.data.get('battery_level')
            kilometers_left = request.data.get('kilometers_left')
            vehicle_image = request.FILES.get('vehicle_image')
            description = request.data.get('description')
            booking_type = request.data.get('booking_type')

            try:
                plan = PricingPlans.objects.get(id=plan_id)
                
            except PricingPlans.DoesNotExist:
                return Response(
                    {'error': 'Invalid plan_id'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Validate required fields
            if not (plan_id):
                return Response(
                    {'error': 'Missing required field: plan_id'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            _metadata = {
                    'plan_id': plan_id,
                    'location': location,
                    'car_make': car_make,
                    'battery_type': battery_type,
                    'battery_level': battery_level,
                    'kilometers_left': kilometers_left,
                    'description': description,
                    'booking_type': booking_type,
                    'user_email': request.user.email,
            },
            
            if vehicle_image:
                _metadata["veicle_image"] = upload_image_to_cloudinary_and_get_url(vehicle_image)

            # Create a Stripe checkout session
            checkout_session = stripe.checkout.Session.create(
                line_items=[
                    {
                        'price_data': {
                            'currency': 'usd',
                            'unit_amount': (plan.price * 100),  # Convert amount to cents
                            'product_data': {
                                'name': plan.title,
                                'images': ['https://res.cloudinary.com/dqathrf7e/image/upload/v1728217409/logo.0430ece9704bdaedc044_xoulcl.png']
                            },
                        },
                        'quantity': 1,
                    },
                ],
                metadata = _metadata,
                payment_method_types=['card'],
                mode='payment',
                success_url=settings.SITE_PURCHASE_SUCCESS_URL + '/?success=true&session_id={CHECKOUT_SESSION_ID}',
                cancel_url=settings.SITE_PURCHASE_FAILED_URL + '/canceled=true',
            )

            # Return the checkout session URL
            return Response({'checkout_url': checkout_session.url}, status=status.HTTP_200_OK)

        except Exception as e:
            print(e)
            # Handle errors during checkout session creation
            return Response(
                {'error': f'Something went wrong when creating the Stripe checkout session: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        

@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']
    event = None

    try:
        event = stripe.Webhook.construct_event(
        payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        # Invalid payload
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        return HttpResponse(status=400)

    if event['type'] == 'checkout.session.completed':

        session = event['data']['object']

        location = session['metadata']['location']
        car_make = session['metadata']['car_make']
        battery_type = session['metadata']['battery_type']
        battery_level = session['metadata']['battery_level']
        kilometers_left = session['metadata']['kilometers_left']
        description = session['metadata']['description']
        booking_type = session['metadata']['booking_type']
        user_email = session['metadata']['user_email']
        vehicle_image = None
        
        try:
            vehicle_image = session['metadata']['vehicle_image']
        except:
            pass

        # get the last created driver (assuming there is only one driver)
        driver = Driver.objects.last()
        user = User.objects.get(email=user_email)

        # create a new booking object and save it to the database
        booking = Booking(
            user = user,
            location=location,
            battery_type = battery_type,
            car_make = car_make,
            driver = driver.user,
            paid = True,
            status = "Completed",
        )

        if vehicle_image is not None:
            booking.vehicle_image = vehicle_image

        if battery_level:
            booking.battery_level = battery_level
        
        if kilometers_left:
            booking.kilometers_left = kilometers_left

        if description:
            booking.description = description

        if booking_type:
            booking.booking_type = booking_type

        booking.save()


        # update driver pending bookings count
        driver.number_of_pending_bookings += 1
        driver.save()

        # email user
        EmailUser(email=user.email, booking=booking)


    elif event['type'] == 'checkout.session.async_payment_failed':
        session = event['data']['object']

        user_email = session['metadata']['user_email']

        EmailUser(email=user_email, failed=True)

    # Passed signature verification
    return HttpResponse(status=200)