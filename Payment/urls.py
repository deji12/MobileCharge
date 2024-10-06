from django.urls import path
from . import views

urlpatterns = [
    path('stripe/create-checkout-session/', views.StripeOneTimeCheckoutView.as_view()),
    path('mark-invoice-as-successful/<str:invoice_id>/', views.mark_invoice_as_paid),
    path('invoice/<str:invoice_id>/', views.get_invoice),
    path('delete-invoice/<str:invoice_id>/', views.delete_invoice),
]