"""Stripe payment API — checkout, webhook, customer portal."""

import stripe
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.config import settings
from app.database import get_db

router = APIRouter(prefix="/api/stripe", tags=["stripe"])

stripe.api_key = settings.stripe_secret_key

PLAN_PRICES = {
    "lite": settings.stripe_price_lite,
    "pro": settings.stripe_price_pro,
}


class CheckoutRequest(BaseModel):
    user_id: str
    plan: str


@router.post("/checkout")
async def create_checkout(body: CheckoutRequest):
    if body.plan not in PLAN_PRICES:
        raise HTTPException(status_code=400, detail="無効なプランです")

    price_id = PLAN_PRICES[body.plan]
    if not price_id:
        raise HTTPException(status_code=500, detail="Price IDが未設定です")

    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT email, stripe_customer_id FROM users WHERE id = ?",
            (body.user_id,),
        )
        user = await cursor.fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="ユーザーが見つかりません")

        # Reuse existing Stripe customer or create new
        customer_id = user["stripe_customer_id"]
        if not customer_id:
            customer = stripe.Customer.create(
                email=user["email"],
                metadata={"user_id": body.user_id},
            )
            customer_id = customer.id
            await db.execute(
                "UPDATE users SET stripe_customer_id = ? WHERE id = ?",
                (customer_id, body.user_id),
            )
            await db.commit()

        session = stripe.checkout.Session.create(
            customer=customer_id,
            mode="subscription",
            line_items=[{"price": price_id, "quantity": 1}],
            success_url=f"{settings.app_url}/chat?payment=success",
            cancel_url=f"{settings.app_url}/chat?payment=cancel",
            metadata={"user_id": body.user_id, "plan": body.plan},
        )

        return {"url": session.url}
    finally:
        await db.close()


@router.post("/webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig = request.headers.get("stripe-signature", "")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig, settings.stripe_webhook_secret,
        )
    except stripe.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        user_id = session.get("metadata", {}).get("user_id")
        plan = session.get("metadata", {}).get("plan")
        customer_id = session.get("customer")

        if user_id and plan:
            db = await get_db()
            try:
                await db.execute(
                    "UPDATE users SET plan = ?, stripe_customer_id = ? WHERE id = ?",
                    (plan, customer_id, user_id),
                )
                await db.commit()
            finally:
                await db.close()

    elif event["type"] == "customer.subscription.deleted":
        subscription = event["data"]["object"]
        customer_id = subscription.get("customer")

        if customer_id:
            db = await get_db()
            try:
                await db.execute(
                    "UPDATE users SET plan = 'free' WHERE stripe_customer_id = ?",
                    (customer_id,),
                )
                await db.commit()
            finally:
                await db.close()

    elif event["type"] == "invoice.payment_failed":
        invoice = event["data"]["object"]
        customer_id = invoice.get("customer")

        if customer_id:
            db = await get_db()
            try:
                await db.execute(
                    "UPDATE users SET plan = 'free' WHERE stripe_customer_id = ?",
                    (customer_id,),
                )
                await db.commit()
            finally:
                await db.close()

    return JSONResponse(content={"received": True})


class PortalRequest(BaseModel):
    user_id: str


@router.post("/portal")
async def create_portal(body: PortalRequest):
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT stripe_customer_id FROM users WHERE id = ?",
            (body.user_id,),
        )
        user = await cursor.fetchone()
        if not user or not user["stripe_customer_id"]:
            raise HTTPException(status_code=400, detail="サブスクリプション情報がありません")

        session = stripe.billing_portal.Session.create(
            customer=user["stripe_customer_id"],
            return_url=f"{settings.app_url}/chat",
        )

        return {"url": session.url}
    finally:
        await db.close()
