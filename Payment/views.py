from django.shortcuts import render, redirect
import stripe
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import Invoice
from Booking.models import Booking
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .serializers import InvoiceSerializer
from Helper.utils import EmailUser

# This is your test secret API key.
stripe.api_key = settings.STRIPE_SECRET_KEY

class StripeOneTimeCheckoutView(APIView):

    """
    Handles the creation of a Stripe one-time payment session and generates an invoice.
    """

    @swagger_auto_schema(
        operation_description="Create a Stripe one-time checkout session for a booking payment and generate an invoice.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'amount': openapi.Schema(type=openapi.TYPE_NUMBER, description='Amount to be paid in USD'),
                'plan_title': openapi.Schema(type=openapi.TYPE_STRING, description='The title of the plan being purchased'),
                'booking_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='The ID of the booking related to the payment')
            },
            required=['amount', 'plan_title', 'booking_id'],
        ),
        responses={
            302: openapi.Response(
                description="Redirects to the Stripe checkout session URL. The `invoice_id` is included in the success URL.",
                examples={
                    "application/json": {
                        "url": "https://checkout.stripe.com/pay/cs_test_a1b2c3d4e5?success=true&session_id=cs_test_a1b2c3d4e5&invoice_id=1234"
                    }
                }
            ),
            500: openapi.Response(description="Error occurred during checkout session creation.")
        },
        # tags=["Payments"],
        operation_summary="Create a one-time payment session via Stripe and generate an invoice"
    )
    def post(self, request):
        try:

            amount = request.data.get('amount')
            plan_title = request.data.get('plan_title')
            booking_id = request.data.get('booking_id')

            if not (amount and plan_title and booking_id):
                return Response(
                    {'error': 'Missing required fields: amount, plan_title, booking_id'},
                    status = status.HTTP_400_BAD_REQUEST
                )

                        # create invoice
            invoice = Invoice(
                booking = Booking.objects.get(id=booking_id),
                amount = float(amount),
            )

            invoice.save()

            checkout_session = stripe.checkout.Session.create(
                line_items=[
                    {
                        # Provide the exact Price ID (for example, pr_1234) of the product you want to sell
                        'price_data': {
                            'currency': 'usd',
                            'unit_amount': (int(amount) * 100),
                            'product_data': {
                                'name': plan_title,
                                'images': ['https://res.cloudinary.com/dqathrf7e/image/upload/v1728217409/logo.0430ece9704bdaedc044_xoulcl.png']
                            },
                        },
                        'quantity': 1,
                    },
                ],
                payment_method_types = [ 'card'],
                mode='payment',
                success_url=settings.SITE_PURCHASE_SUCCESS_URL + '/?success=true&session_id={CHECKOUT_SESSION_ID}&' + f'invoice_id={invoice.invoice_id}',
                cancel_url=settings.SITE_PURCHASE_FAILED_URL + '/canceled=true&' + f'invoice_id={invoice.invoice_id}',
            )
            print(checkout_session.url)
            return Response({'checkout_url': checkout_session.url}, status=status.HTTP_200_OK)
        
        except:
            return Response(
                {'errror': 'Something went wrong when creating stripe checkout session'},
                status = status.HTTP_500_INTERNAL_SERVER_ERROR
            )

@swagger_auto_schema(
    method='patch',
    operation_description="Marks an invoice as paid.",
    responses={
        200: openapi.Response(
            description="Invoice successfully marked as paid.",
            examples={
                "application/json": {
                    "message": "Successful purchase for invoice with ID: 12345"
                }
            }
        ),
        404: openapi.Response(
            description="Invoice not found.",
            examples={
                "application/json": {
                    "error": "Invoice with ID: 12345 does not exist."
                }
            }
        ),
    },
    # tags=["Invoices"],
    operation_summary="Mark an invoice as paid"
)
@api_view(['PATCH'])
# @permission_classes([IsAuthenticated])
def mark_invoice_as_paid(request, invoice_id):

    """
    Marks an invoice as paid
    """

    try:
        invoice = Invoice.objects.get(invoice_id=invoice_id)
        if not invoice.paid:
            invoice.paid = True
            invoice.save()

            booking = invoice.booking
            booking.paid = True
            booking.save()

            # email the user
            EmailUser(email=invoice.booking.user.email, invoice=invoice).send()

            return Response({'message': f'Successful purchase for invoice with ID: {invoice_id}'} ,status=status.HTTP_200_OK)
        
        else:
            return Response({'message': f'Invoice with ID: {invoice_id} is already marked as paid.'}, status=status.HTTP_200_OK)
    
    except Invoice.DoesNotExist:
        return Response({'error': f'Invoice with ID: {invoice_id} does not exist.'}, status=status.HTTP_404_NOT_FOUND)
    
@swagger_auto_schema(
    method='get',
    operation_description="Retrieve an invoice by its ID, including booking and user information.",
    responses={
        200: openapi.Response(
            description="Invoice retrieved successfully.",
            examples={
                "application/json": {
                    "invoice_id": "12345",
                    "amount": 100.0,
                    "paid": False,
                    "created_at": "2024-10-03T12:00:00Z",
                    "booking": {
                        "id": 1,
                        "status": "Pending",
                        "user": {
                            "id": 1,
                            "username": "user1",
                            "email": "user1@example.com",
                            "first_name": "John",
                            "last_name": "Doe",
                            "phone": "1234567890",
                            "is_active": True,
                            "is_superuser": False,
                            "date_joined": "2023-01-01T12:00:00Z",
                            "profile_image": "http://example.com/profile_image.jpg"
                        },
                        "driver": {
                            "id": 2,
                            "username": "driver1",
                            "email": "driver1@example.com",
                            "first_name": "Jane",
                            "last_name": "Smith",
                            "phone": "0987654321",
                            "is_active": True,
                            "is_superuser": False,
                            "date_joined": "2023-02-01T15:00:00Z",
                            "profile_image": "http://example.com/driver_profile_image.jpg"
                        }
                    }
                }
            }
        ),
        404: openapi.Response(
            description="Invoice not found.",
            examples={
                "application/json": {
                    "error": "Invoice with ID: 12345 does not exist."
                }
            }
        ),
    },
    operation_summary="Retrieve an invoice by ID"
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_invoice(request, invoice_id):

    """
    Get an invoice by its ID
    """
    try:
        invoice = Invoice.objects.get(invoice_id=invoice_id)
        serializer = InvoiceSerializer(invoice)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    except Invoice.DoesNotExist:
        return Response({'error': f'Invoice with ID: {invoice_id} does not exist.'}, status=status.HTTP_404_NOT_FOUND)
    
@swagger_auto_schema(
    method='delete',
    operation_summary='Delete an Invoice',
    operation_description='Deletes an invoice identified by its unique ID.',
    responses={
        200: openapi.Response(
            description='Invoice deleted successfully',
            examples={
                'application/json': {
                    "message": "Invoice with ID: 12345 deleted successfully."
                }
            }
        ),
        404: openapi.Response(
            description='Invoice not found',
            examples={
                'application/json': {
                    "error": "Invoice with ID: 12345 does not exist."
                }
            }
        )
    },
    manual_parameters=[
        openapi.Parameter(
            'invoice_id',
            openapi.IN_PATH,
            description='The unique identifier of the invoice to be deleted',
            type=openapi.TYPE_INTEGER,
            required=True,
        )
    ]
)
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_invoice(request, invoice_id):

    """
    Delete an invoice by its ID
    """
    try:
        invoice = Invoice.objects.get(invoice_id=invoice_id)
        invoice.delete()

        booking = invoice.booking
        booking.delete()
        return Response({'message': f'Invoice with ID: {invoice_id} deleted successfully.'}, status=status.HTTP_200_OK)
    
    except Invoice.DoesNotExist:
        return Response({'error': f'Invoice with ID: {invoice_id} does not exist.'}, status=status.HTTP_404_NOT_FOUND)