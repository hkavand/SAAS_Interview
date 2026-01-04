from django.urls import path
from .views import MeView, SubscribeView, StripeWebhookView

urlpatterns = [
    path("me/", MeView.as_view(), name="me"),
    path("subscribe/", SubscribeView.as_view(), name="subscribe"),
    path("stripe/webhook/", StripeWebhookView.as_view(), name="stripe-webhook"),
]
