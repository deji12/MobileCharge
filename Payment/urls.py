from django.urls import path
from . import views

urlpatterns = [
    path('pricing-plans/', views.get_pricing_plans),
    path('stripe/create-checkout-session/', views.StripeOneTimeCheckoutView.as_view()),
    path('webhooks/stripe/', views.stripe_webhook, name='stripe-webhook'),
]