from django.urls import path
from . import views

urlpatterns = [
    path('pricing-plans/', views.get_pricing_plans),
    path('stripe/create-checkout-session/', views.StripeOneTimeCheckoutView.as_view()),
    path('webhooks/stripe/', views.stripe_webhook),
    path('stripe/create-subscription/', views.StripeSubscriptionView.as_view()),
    path('cancel-subscription/', views.CancelSubscriptionView.as_view(), name='cancel-subscription'),
]