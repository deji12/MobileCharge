from django.shortcuts import render, redirect
import stripe
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import PricingPlans, Subscription
from Booking.models import Booking
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .serializers import PricingSerializer
from Helper.utils import EmailUser
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from Authentication.models import User
import json
from datetime import timedelta
from django.utils import timezone

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

    # permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Create a Stripe one-time checkout session for a booking payment and generate an invoice.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'plan_id': openapi.Schema(type=openapi.TYPE_STRING, description='The title of the plan being purchased'),
                'booking_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='The ID of the booking related to the payment')
            },
            required=['plan_id', 'booking_id'],
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
        
        try:
            # Retrieve payment details from the request
            booking_id = request.data.get('booking_id')

            if not (booking_id):
                return Response(
                    {'error': 'Missing required fields: plan_id and booking_id'},
                    status=status.HTTP_400_BAD_REQUEST
                )   

            try:
                booking = Booking.objects.get(id=int(booking_id))
                
            except Booking.DoesNotExist:
                return Response(
                    {'error': 'Invalid booking_id'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Create a Stripe checkout session
            checkout_session = stripe.checkout.Session.create(
                line_items=[
                    {
                        'price_data': {
                            'currency': 'usd',
                            'unit_amount': (booking.price * 100),  # Convert amount to cents
                            'product_data': {
                                'name': 'Visitor',
                                'images': ['https://res.cloudinary.com/dqathrf7e/image/upload/v1728217409/logo.0430ece9704bdaedc044_xoulcl.png']
                            },
                        },
                        'quantity': 1,
                    },
                ],
                metadata = {'booking_id': booking_id,
                },
                payment_method_types=['card'],
                mode='payment',
                success_url=settings.SITE_PURCHASE_SUCCESS_URL + '&?success=true&session_id={CHECKOUT_SESSION_ID}',
                cancel_url=settings.SITE_PURCHASE_CANCEL_URL,
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
        
class StripeSubscriptionView(APIView):

    @swagger_auto_schema(
        operation_description="Create a Stripe subscription checkout session for a recurring payment plan.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'plan_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='The ID of the pricing plan for the subscription'),
            },
            required=['plan_id'],
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
                description="Missing required fields in the request or invalid plan ID.",
                examples={
                    "application/json": {
                        "error": "Missing required field: plan_id"
                    }
                }
            ),
            500: openapi.Response(
                description="Error occurred during checkout session creation.",
                examples={
                    "application/json": {
                        "error": "Something went wrong when creating the Stripe checkout session: <error message>"
                    }
                }
            )
        },
        operation_summary="Create a recurring subscription payment session via Stripe"
    )
    def post(self, request):
        
        try:
            # Retrieve payment details from the request
            plan_id = request.data.get('plan_id')

            if not (plan_id):
                return Response(
                    {'error': 'Missing required fields: plan_id and booking_id'},
                    status=status.HTTP_400_BAD_REQUEST
                )   

            try:
                plan = PricingPlans.objects.get(id=int(plan_id))
                
            except Booking.DoesNotExist:
                return Response(
                    {'error': 'Invalid booking_id'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Create a Stripe checkout session
            checkout_session = stripe.checkout.Session.create(
                line_items=[
                    {
                        'price': plan.stripe_price_id,
                        'quantity': 1,
                    },
                ],
                metadata = {
                    'user_id': request.user.id,
                    'plan_name': plan.title
                },
                payment_method_types=['card'],
                mode='subscription',
                success_url=settings.SITE_PURCHASE_SUCCESS_URL + '&?subscription_payment=successe&session_id={CHECKOUT_SESSION_ID}',
                cancel_url=settings.SITE_PURCHASE_CANCEL_URL,
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
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE', None)
    event = None

    # Log the incoming payload and signature header

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        print(f"Invalid payload: {str(e)}")
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        print(f"Invalid signature: {str(e)}")
        return HttpResponse(status=400)

    # Log the event type for further debugging
    print(f"Event type: {event['type']}")

    if event['type'] == 'checkout.session.completed':
        # Process the session data
        session = event['data']['object']
        print(f"Session data: {json.dumps(session)}")

        booking_id = session['metadata']['booking_id']

        user = User.objects.get(email=user_email)

        # create a new booking object and save it to the database
        booking = Booking.objects.get(int(booking_id))
        booking.paid = True
        booking.save()

        # email user
        EmailUser(email=user.email, booking=booking)

    elif event['type'] == 'customer.subscription.created' or event['type'] == 'customer.subscription.updated':
        session = event['data']['object']

        user_id = session['metadata']['user_id']
        plan_name = session['metadata']['plan_name']

        user = User.objects.get(id=int(user_id))
        plan = PricingPlans.objects.get(title=plan_name)
        subscription_duration = 30

        # get or create subscription fore user
        subscription, created = Subscription.objects.get_or_create(user=user)

        if subscription.plan != plan:
            subscription.plan = plan

        subscription.status = 'Active'
        subscription.expires_at = timezone.now() + timedelta(days=subscription_duration)
        subscription.stripe_subscription_id = session['id']

        subscription.save()
        
        user.plan_type = plan_name
        user.save()

        # Sending a subscription renewal email
        EmailUser(email=user.email, subscription_renewed=True)

    elif event['type'] == 'customer.subscription.deleted':

        session = event['data']['object']
        user_id = session['metadata']['user_id']

        user = User.objects.get(id=int(user_id))
        subscription, created = Subscription.objects.get_or_create(user=user)
        subscription.status = 'Canceled'

        subscription.save()

        # Sending a subscription cancellation email
        EmailUser(email=user.email, subscription_canceled=True)

    elif event['type'] == 'checkout.session.async_payment_failed':
        session = event['data']['object']

        user_email = session['metadata']['user_email']

        EmailUser(email=user_email, failed=True)

    # Passed signature verification
    return HttpResponse(status=200)

class CancelSubscriptionView(APIView):
    
    @swagger_auto_schema(
        operation_description="Cancel a user's subscription.",
        responses={
            200: openapi.Response(
                description="Subscription canceled successfully.",
                examples={"message": "Subscription canceled successfully."}
            ),
            404: openapi.Response(
                description="No active subscription found.",
                examples={"error": "No active subscription found."}
            ),
            400: openapi.Response(
                description="Failed to cancel subscription.",
                examples={"error": "Failed to cancel subscription: {error_message}"}
            ),
            500: openapi.Response(
                description="Something went wrong.",
                examples={"error": "Something went wrong: {error_message}"}
            ),
        }
    )
    def post(self, request):
        user = request.user  # Get the current authenticated user

        try:
            # Get the user's subscription
            subscription = Subscription.objects.get(user=user)

            # Cancel the subscription on Stripe
            stripe.Subscription.delete(subscription.stripe_subscription_id)

            # Update the subscription status in your database
            subscription.status = 'canceled'
            subscription.save()

            return Response({'message': 'Subscription canceled successfully.'}, status=status.HTTP_200_OK)

        except Subscription.DoesNotExist:
            return Response({'error': 'No active subscription found.'}, status=status.HTTP_404_NOT_FOUND)
        except stripe.error.StripeError as e:
            return Response({'error': f'Failed to cancel subscription: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': f'Something went wrong: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
