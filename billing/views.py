import os
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .stripe_client import PRICE_MAP
import stripe

from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from .models import User
import json
from rest_framework.permissions import AllowAny


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        print("USER:", request.user, request.user.is_authenticated)
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
    permission_classes = [AllowAny]  # Allow Stripe to call without authentication

    def post(self, request):
        payload = request.body
        sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")
        endpoint_secret = os.getenv("STRIPE_WEBHOOK_SECRET")

        try:
            event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
        except ValueError as e:
            return JsonResponse({"error": f"Invalid payload: {str(e)}"}, status=400)
        except stripe.error.SignatureVerificationError as e:
            return JsonResponse({"error": f"Invalid signature: {str(e)}"}, status=400)

        if event["type"] == "checkout.session.completed":
            session = event["data"]["object"]

            # Check that payment succeeded
            if session.get("payment_status") != "paid":
                return JsonResponse({"status": "payment not completed"}, status=200)

            # Retrieve metadata
            metadata = session.get("metadata", {})
            user_id = metadata.get("user_id")
            plan = metadata.get("plan")
            amount_total = session.get("amount_total", 0)

            if user_id and plan:
                try:
                    user = User.objects.get(id=user_id)
                    user.subscription_status = "active"
                    user.current_plan = plan
                    user.total_amount_paid += amount_total
                    user.save()
                    print(
                        f"Updated user {user.email}: plan={plan}, total={user.total_amount_paid}"
                    )
                except User.DoesNotExist:
                    print(f"User with id {user_id} does not exist")

        elif event["type"] == "customer.subscription.deleted":
            subscription = event["data"]["object"]
            metadata = subscription.get("metadata", {})
            user_id = metadata.get("user_id")
            if user_id:
                try:
                    user = User.objects.get(id=user_id)
                    user.subscription_status = "inactive"
                    user.current_plan = None
                    user.save()
                    print(f"User {user.email} subscription cancelled")
                except User.DoesNotExist:
                    print(f"User with id {user_id} does not exist")

        return JsonResponse({"status": "success"}, status=200)


@csrf_exempt  # Only for dev/testing; production should use CSRF tokens
def login_view(request):
    print(request)
    if request.method == "OPTIONS":
        return JsonResponse({"status": "ok"}, status=200)

    if request.method == "POST":
        data = json.loads(request.body)
        user = authenticate(
            request, username=data["username"], password=data["password"]
        )
        if user:
            print(user)
            login(request, user)
            return JsonResponse({"success": True})
        return JsonResponse({"success": False}, status=401)

    return JsonResponse({"detail": "Method not allowed"}, status=405)


@csrf_exempt
def logout_view(request):
    if request.method == "POST":
        logout(request)
        return JsonResponse({"success": True})
