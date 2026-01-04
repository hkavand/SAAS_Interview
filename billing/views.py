from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .stripe_client import PRICE_MAP
import stripe
import os

from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.http import JsonResponse
import json

from .models import User


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        return Response(
            {
                "subscription_status": user.subscription_status,
                "current_plan": user.current_plan,
                "lifetime_spend": user.total_amount_paid,
            }
        )


class SubscribeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        plan = request.data.get("plan")

        if plan not in PRICE_MAP:
            return Response(
                {"error": "Invalid plan"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        price_id = PRICE_MAP[plan]

        checkout_session = stripe.checkout.Session.create(
            mode="subscription",
            payment_method_types=["card"],
            customer_email=request.user.email,
            line_items=[
                {
                    "price": price_id,
                    "quantity": 1,
                }
            ],
            success_url=f"{os.getenv('FRONTEND_URL')}/dashboard?success=true",
            cancel_url=f"{os.getenv('FRONTEND_URL')}/dashboard?canceled=true",
            metadata={
                "user_id": request.user.id,
                "plan": plan,
            },
        )

        return Response(
            {"checkout_url": checkout_session.url},
            status=status.HTTP_200_OK,
        )



@method_decorator(csrf_exempt, name="dispatch")
class StripeWebhookView(APIView):
    def post(self, request):
        payload = request.body
        sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")
        endpoint_secret = os.getenv("STRIPE_WEBHOOK_SECRET")

        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, endpoint_secret
            )
        except ValueError as e:
            # Invalid payload
            return JsonResponse({"error": str(e)}, status=400)
        except stripe.error.SignatureVerificationError as e:
            # Invalid signature
            return JsonResponse({"error": str(e)}, status=400)

        if event["type"] == "invoice.payment_succeeded":
            invoice = event["data"]["object"]
            stripe_customer_id = invoice["customer"]
            metadata = invoice.get("metadata", {})
            user_id = metadata.get("user_id")
            plan = metadata.get("plan")
            amount_paid = invoice.get("amount_paid", 0)  # in cents

            try:
                user = User.objects.get(id=user_id)
                user.subscription_status = "active"
                user.current_plan = plan
                user.total_amount_paid += amount_paid
                user.save()
            except User.DoesNotExist:
                pass

        elif event["type"] == "customer.subscription.deleted":
            subscription = event["data"]["object"]
            metadata = subscription.get("metadata", {})
            user_id = metadata.get("user_id")
            try:
                user = User.objects.get(id=user_id)
                user.subscription_status = "inactive"
                user.current_plan = None
                user.save()
            except User.DoesNotExist:
                pass


        return JsonResponse({"status": "success"}, status=200)
