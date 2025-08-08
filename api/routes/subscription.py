# api/routes/subscription.py
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
import stripe, os, json, datetime
from api.auth.deps import get_current_user
from api.db.database import db

router = APIRouter(prefix="/subscription", tags=["Subscription"])

# --- Stripe config ---
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
PRICE_ID = os.getenv("STRIPE_PRICE_ID")
SUCCESS_URL = os.getenv("STRIPE_SUCCESS_URL", "http://localhost:8000/success")
CANCEL_URL = os.getenv("STRIPE_CANCEL_URL", "http://localhost:8000/cancel")
WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")

if not stripe.api_key or not PRICE_ID:
    raise RuntimeError("Missing STRIPE_SECRET_KEY or STRIPE_PRICE_ID")

def _is_admin_or_subscribed(role: str) -> bool:
    return role in ("admin", "subscriber")

async def _ensure_customer_for_user(user) -> str:
    """
    Ensure the app user has a Stripe customer; store id on user doc.
    """
    if cid := user.get("stripe_customer_id"):
        return cid
    customer = stripe.Customer.create(email=user.get("email"))
    await db.users.update_one(
        {"_id": user["_id"]},
        {"$set": {"stripe_customer_id": customer.id, "updated_at": datetime.datetime.utcnow()}}
    )
    return customer.id

async def _active_subscription_for_customer(stripe_customer_id: str):
    """
    Return the first 'live' subscription for a Stripe customer, or None.
    """
    subs = stripe.Subscription.list(
        customer=stripe_customer_id,
        status="all",
        expand=["data.default_payment_method"]
    )
    for s in subs.auto_paging_iter():
        if s["status"] in ("trialing", "active", "past_due"):
            return s
    return None

# ---------- New: subscribe now (no trial) ----------
@router.post("/subscribe-now")
async def subscribe_now(user=Depends(get_current_user)):
    """
    Create a subscription Checkout session that charges immediately (no trial).
    If the user is already subscribed, provide a Billing Portal link instead.
    """
    customer_id = await _ensure_customer_for_user(user)

    # If already subscribed, send them to the portal instead of creating another subscription
    if _is_admin_or_subscribed(user.get("role", "")):
        session = stripe.billing_portal.Session.create(customer=customer_id, return_url=SUCCESS_URL)
        return {"portal_url": session.url}

    # If they still have an active/trialing subscription record at Stripe, send portal
    existing = await _active_subscription_for_customer(customer_id)
    if existing:
        session = stripe.billing_portal.Session.create(customer=customer_id, return_url=SUCCESS_URL)
        return {"portal_url": session.url}

    try:
        session = stripe.checkout.Session.create(
            mode="subscription",
            customer=customer_id,
            line_items=[{"price": PRICE_ID, "quantity": 1}],
            # Force no trial: charge starts now
            subscription_data={"trial_end": "now"},
            success_url=SUCCESS_URL + "?session_id={CHECKOUT_SESSION_ID}",
            cancel_url=CANCEL_URL,
            allow_promotion_codes=True,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Don't flip role here; wait for webhook confirmation (customer.subscription.created/updated -> active)
    return {"checkout_url": session.url}

# ---------- Existing: start 7-day trial ----------
@router.post("/start-trial")
async def start_trial(user=Depends(get_current_user)):
    """
    Create a subscription Checkout session with a 7-day trial (if your app logic allows it).
    User adds a payment method now; billing starts automatically after the trial.
    """
    customer_id = await _ensure_customer_for_user(user)

    # If already subscribed, just send to portal
    if _is_admin_or_subscribed(user.get("role", "")):
        session = stripe.billing_portal.Session.create(customer=customer_id, return_url=SUCCESS_URL)
        return {"portal_url": session.url}

    # If they already have an active/trialing sub at Stripe, send portal
    existing = await _active_subscription_for_customer(customer_id)
    if existing:
        session = stripe.billing_portal.Session.create(customer=customer_id, return_url=SUCCESS_URL)
        return {"portal_url": session.url}

    try:
        session = stripe.checkout.Session.create(
            mode="subscription",
            customer=customer_id,
            line_items=[{"price": PRICE_ID, "quantity": 1}],
            subscription_data={
                "trial_period_days": 7,
                "payment_settings": {"save_default_payment_method": "on_subscription"},
            },
            success_url=SUCCESS_URL + "?session_id={CHECKOUT_SESSION_ID}",
            cancel_url=CANCEL_URL,
            allow_promotion_codes=True,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Optionally mark trial locally for UX, but the source of truth will be webhooks
    await db.users.update_one(
        {"_id": user["_id"]},
        {"$set": {
            "role": "trial" if user.get("role") != "admin" else "admin",
            "trial_start_date": datetime.datetime.utcnow(),
            "updated_at": datetime.datetime.utcnow()
        }}
    )

    return {"checkout_url": session.url}

# ---------- Cancel at period end ----------
@router.post("/cancel")
async def cancel_subscription(user=Depends(get_current_user)):
    """
    Cancels the active subscription at period end.
    """
    if not user.get("stripe_customer_id"):
        raise HTTPException(status_code=404, detail="No Stripe customer on file.")

    active = await _active_subscription_for_customer(user["stripe_customer_id"])
    if not active:
        raise HTTPException(status_code=404, detail="No active subscription found.")

    try:
        stripe.Subscription.modify(active.id, cancel_at_period_end=True)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Keep role as-is until the period actually lapses (webhook will flip)
    return {"message": "Subscription will cancel at period end.", "subscription_id": active.id}

# ---------- Billing portal ----------
@router.post("/portal")
async def create_billing_portal(user=Depends(get_current_user)):
    """
    Creates a Stripe Billing Portal session for user self-service.
    """
    cid = user.get("stripe_customer_id") or await _ensure_customer_for_user(user)
    try:
        session = stripe.billing_portal.Session.create(customer=cid, return_url=SUCCESS_URL)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"portal_url": session.url}

# ---------- Optional: current subscription status ----------
@router.get("/status")
async def subscription_status(user=Depends(get_current_user)):
    """
    Returns the current subscription status known to Stripe + local role.
    """
    status_payload = {"role": user.get("role"), "stripe_status": None, "stripe_subscription_id": None}
    if not user.get("stripe_customer_id"):
        return status_payload

    sub = await _active_subscription_for_customer(user["stripe_customer_id"])
    if sub:
        status_payload["stripe_status"] = sub["status"]
        status_payload["stripe_subscription_id"] = sub["id"]
    return status_payload

# ---------- Webhook ----------
@router.post("/webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        if WEBHOOK_SECRET:
            event = stripe.Webhook.construct_event(payload, sig_header, WEBHOOK_SECRET)
        else:
            # Dev mode fallback (not recommended for prod)
            event = json.loads(payload.decode("utf-8"))
    except Exception as e:
        return JSONResponse(status_code=400, content={"error": str(e)})

    type_ = event["type"]
    data = event["data"]["object"]

    # Checkout done: nothing to change locally besides ensuring customer link
    if type_ == "checkout.session.completed":
        customer_id = data.get("customer")
        if customer_id:
            await db.users.update_one(
                {"stripe_customer_id": customer_id},
                {"$set": {"updated_at": datetime.datetime.utcnow()}}
            )
        return {"received": True}

    # Subscription lifecycle
    if type_ in ("customer.subscription.created", "customer.subscription.updated"):
        sub = data
        customer_id = sub.get("customer")
        status_s = sub.get("status")  # trialing, active, past_due, canceled, unpaid

        user_doc = await db.users.find_one({"stripe_customer_id": customer_id})
        if user_doc:
            updates = {"updated_at": datetime.datetime.utcnow()}
            if status_s == "trialing" and user_doc.get("role") != "admin":
                updates["role"] = "trial"
                updates["trial_start_date"] = updates["updated_at"]
            elif status_s == "active" and user_doc.get("role") != "admin":
                updates["role"] = "subscriber"
            elif status_s in ("canceled", "unpaid") and user_doc.get("role") != "admin":
                updates["role"] = "unsubscribed"
            await db.users.update_one({"_id": user_doc["_id"]}, {"$set": updates})

        # Upsert a local subscription record
        await db.subscriptions.update_one(
            {"stripe_subscription_id": sub["id"]},
            {"$set": {
                "stripe_subscription_id": sub["id"],
                "stripe_customer_id": customer_id,
                "status": status_s,
                "current_period_end": datetime.datetime.fromtimestamp(sub["current_period_end"]),
                "cancel_at_period_end": sub.get("cancel_at_period_end", False),
                "plan_price_id": sub["items"]["data"][0]["price"]["id"] if sub.get("items") else None,
                "updated_at": datetime.datetime.utcnow(),
            },
             "$setOnInsert": {"created_at": datetime.datetime.utcnow()}},
            upsert=True
        )
        return {"received": True}

    if type_ == "customer.subscription.deleted":
        customer_id = data.get("customer")
        user_doc = await db.users.find_one({"stripe_customer_id": customer_id})
        if user_doc and user_doc.get("role") != "admin":
            await db.users.update_one(
                {"_id": user_doc["_id"]},
                {"$set": {"role": "unsubscribed", "updated_at": datetime.datetime.utcnow()}}
            )
        await db.subscriptions.update_one(
            {"stripe_subscription_id": data["id"]},
            {"$set": {"status": "canceled", "updated_at": datetime.datetime.utcnow()}}
        )
        return {"received": True}

    # Invoices / Payments
    if type_ == "invoice.payment_succeeded":
        inv = data
        await db.payments.insert_one({
            "stripe_invoice_id": inv["id"],
            "stripe_customer_id": inv.get("customer"),
            "amount_paid": inv["amount_paid"],
            "currency": inv["currency"],
            "paid": inv["paid"],
            "created_at": datetime.datetime.utcnow(),
            "lines": inv.get("lines", {}),
        })
        return {"received": True}

    if type_ == "invoice.payment_failed":
        inv = data
        await db.payments.insert_one({
            "stripe_invoice_id": inv["id"],
            "stripe_customer_id": inv.get("customer"),
            "amount_due": inv["amount_due"],
            "currency": inv["currency"],
            "paid": inv["paid"],
            "attempt_count": inv.get("attempt_count"),
            "created_at": datetime.datetime.utcnow(),
            "failure_code": inv.get("last_payment_error", {}).get("code") if inv.get("last_payment_error") else None,
            "failure_message": inv.get("last_payment_error", {}).get("message") if inv.get("last_payment_error") else None,
        })
        return {"received": True}

    # Optional: 3-day trial ending heads-up
    if type_ == "customer.subscription.trial_will_end":
        sub = data
        await db.events.insert_one({
            "type": type_,
            "stripe_subscription_id": sub["id"],
            "stripe_customer_id": sub.get("customer"),
            "created_at": datetime.datetime.utcnow(),
        })
        return {"received": True}

    # Log everything else
    await db.events.insert_one({"type": type_, "raw": event, "created_at": datetime.datetime.utcnow()})
    return {"received": True}
