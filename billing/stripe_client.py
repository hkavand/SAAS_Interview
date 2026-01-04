import os
import stripe

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

PRICE_MAP = {
    "basic": os.getenv("STRIPE_BASIC_PRICE_ID"),
    "pro": os.getenv("STRIPE_PRO_PRICE_ID"),
}
