"""Stripe webhook handler."""

import stripe
from fastapi import APIRouter, Request, HTTPException

from app.config import settings

router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])


@router.post("/stripe")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    if not sig_header:
        raise HTTPException(status_code=400, detail="Missing signature")

    try:
        stripe.api_key = settings.stripe_secret_key
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.stripe_webhook_secret
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        # Handle successful payment — scan is already created via frontend flow
        # The payment_intent_id links the payment to the scan record
        pass

    elif event["type"] == "customer.subscription.created":
        # Handle new subscription
        pass

    elif event["type"] == "customer.subscription.deleted":
        # Handle subscription cancellation
        pass

    return {"status": "ok"}
