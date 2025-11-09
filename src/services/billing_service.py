"""
Billing Service - Stripe Integration

Handles subscription management, billing, and invoicing for SaaS platform.
"""

import os
from datetime import datetime, timedelta
from typing import Dict, Optional

import stripe

from src.models.saas_models import Invoice, PlanTier, SubscriptionStatus, Tenant

# Configure Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "sk_test_placeholder")


class BillingService:
    """
    Billing service with Stripe integration

    Features:
    - Create Stripe customers
    - Manage subscriptions
    - Handle webhooks
    - Generate invoices
    - Usage-based billing
    """

    # Price IDs (set in Stripe Dashboard)
    PRICE_IDS = {
        PlanTier.FREE: None,  # Free tier has no price
        PlanTier.PRO: {
            "monthly": os.getenv("STRIPE_PRO_MONTHLY_PRICE_ID", "price_pro_monthly"),
            "yearly": os.getenv("STRIPE_PRO_YEARLY_PRICE_ID", "price_pro_yearly"),
        },
        PlanTier.ENTERPRISE: {
            "monthly": os.getenv("STRIPE_ENTERPRISE_MONTHLY_PRICE_ID", "price_ent_monthly"),
            "yearly": os.getenv("STRIPE_ENTERPRISE_YEARLY_PRICE_ID", "price_ent_yearly"),
        },
    }

    def create_customer(self, tenant_id: str, email: str, company_name: str) -> str:
        """
        Create Stripe customer

        Args:
            tenant_id: Tenant UUID
            email: Customer email
            company_name: Company name

        Returns:
            Stripe customer ID
        """
        customer = stripe.Customer.create(
            email=email, name=company_name, metadata={"tenant_id": tenant_id}
        )

        return customer.id

    def create_subscription(
        self,
        customer_id: str,
        plan_tier: PlanTier,
        billing_period: str = "monthly",  # monthly, yearly
    ) -> Dict:
        """
        Create subscription for customer

        Args:
            customer_id: Stripe customer ID
            plan_tier: Subscription plan tier
            billing_period: monthly or yearly

        Returns:
            dict with subscription_id and client_secret
        """
        if plan_tier == PlanTier.FREE:
            raise ValueError("Cannot create subscription for free tier")

        # Get price ID
        price_id = self.PRICE_IDS[plan_tier][billing_period]

        # Create subscription
        subscription = stripe.Subscription.create(
            customer=customer_id,
            items=[{"price": price_id}],
            payment_behavior="default_incomplete",
            payment_settings={"save_default_payment_method": "on_subscription"},
            expand=["latest_invoice.payment_intent"],
        )

        return {
            "subscription_id": subscription.id,
            "client_secret": subscription.latest_invoice.payment_intent.client_secret,
            "status": subscription.status,
        }

    def upgrade_subscription(
        self, subscription_id: str, new_plan_tier: PlanTier, billing_period: str = "monthly"
    ) -> Dict:
        """
        Upgrade subscription to new plan

        Args:
            subscription_id: Current subscription ID
            new_plan_tier: New plan tier
            billing_period: monthly or yearly

        Returns:
            Updated subscription info
        """
        # Get new price ID
        new_price_id = self.PRICE_IDS[new_plan_tier][billing_period]

        # Retrieve current subscription
        subscription = stripe.Subscription.retrieve(subscription_id)

        # Update subscription
        updated_subscription = stripe.Subscription.modify(
            subscription_id,
            items=[{"id": subscription["items"]["data"][0].id, "price": new_price_id}],
            proration_behavior="always_invoice",  # Prorate and invoice immediately
        )

        return {
            "subscription_id": updated_subscription.id,
            "status": updated_subscription.status,
            "current_period_end": datetime.fromtimestamp(updated_subscription.current_period_end),
        }

    def cancel_subscription(self, subscription_id: str, immediately: bool = False) -> Dict:
        """
        Cancel subscription

        Args:
            subscription_id: Subscription ID
            immediately: Cancel immediately vs at period end

        Returns:
            Cancellation info
        """
        if immediately:
            # Cancel immediately
            subscription = stripe.Subscription.delete(subscription_id)
        else:
            # Cancel at period end
            subscription = stripe.Subscription.modify(subscription_id, cancel_at_period_end=True)

        return {
            "subscription_id": subscription.id,
            "status": subscription.status,
            "canceled_at": (
                datetime.fromtimestamp(subscription.canceled_at)
                if subscription.canceled_at
                else None
            ),
        }

    def get_usage_record(
        self, subscription_item_id: str, quantity: int, timestamp: Optional[int] = None
    ):
        """
        Report usage for usage-based billing

        Args:
            subscription_item_id: Subscription item ID
            quantity: Usage quantity (e.g., API calls)
            timestamp: Unix timestamp (defaults to now)
        """
        if timestamp is None:
            timestamp = int(datetime.utcnow().timestamp())

        usage_record = stripe.SubscriptionItem.create_usage_record(
            subscription_item_id,
            quantity=quantity,
            timestamp=timestamp,
            action="set",  # set, increment
        )

        return usage_record

    def create_invoice(self, customer_id: str, amount: float, description: str) -> str:
        """
        Create one-time invoice

        Args:
            customer_id: Stripe customer ID
            amount: Amount in dollars
            description: Invoice description

        Returns:
            Invoice ID
        """
        # Create invoice item
        stripe.InvoiceItem.create(
            customer=customer_id,
            amount=int(amount * 100),  # Convert to cents
            currency="usd",
            description=description,
        )

        # Create and finalize invoice
        invoice = stripe.Invoice.create(customer=customer_id, auto_advance=True)  # Auto-finalize

        finalized_invoice = stripe.Invoice.finalize_invoice(invoice.id)

        return finalized_invoice.id

    def handle_webhook(self, payload: bytes, sig_header: str) -> Dict:
        """
        Handle Stripe webhook

        Args:
            payload: Request body
            sig_header: Stripe-Signature header

        Returns:
            Event data
        """
        webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")

        try:
            event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
        except ValueError:
            raise ValueError("Invalid payload")
        except stripe.error.SignatureVerificationError:
            raise ValueError("Invalid signature")

        # Handle event
        event_type = event["type"]
        event_data = event["data"]["object"]

        handlers = {
            "customer.subscription.created": self._handle_subscription_created,
            "customer.subscription.updated": self._handle_subscription_updated,
            "customer.subscription.deleted": self._handle_subscription_deleted,
            "invoice.payment_succeeded": self._handle_payment_succeeded,
            "invoice.payment_failed": self._handle_payment_failed,
            "customer.subscription.trial_will_end": self._handle_trial_ending,
        }

        handler = handlers.get(event_type)
        if handler:
            return handler(event_data)

        return {"status": "unhandled", "type": event_type}

    def _handle_subscription_created(self, subscription: Dict) -> Dict:
        """Handle subscription created event"""
        # Update tenant in database
        from src.db.session import SessionLocal

        db = SessionLocal()
        try:
            tenant_id = subscription["metadata"].get("tenant_id")
            if tenant_id:
                tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
                if tenant:
                    tenant.stripe_subscription_id = subscription["id"]
                    tenant.subscription_status = SubscriptionStatus(subscription["status"])
                    tenant.current_period_start = datetime.fromtimestamp(
                        subscription["current_period_start"]
                    )
                    tenant.current_period_end = datetime.fromtimestamp(
                        subscription["current_period_end"]
                    )
                    db.commit()

            return {"status": "processed", "tenant_id": tenant_id}
        finally:
            db.close()

    def _handle_subscription_updated(self, subscription: Dict) -> Dict:
        """Handle subscription updated event"""
        from src.db.session import SessionLocal

        db = SessionLocal()
        try:
            tenant_id = subscription["metadata"].get("tenant_id")
            if tenant_id:
                tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
                if tenant:
                    tenant.subscription_status = SubscriptionStatus(subscription["status"])
                    tenant.current_period_end = datetime.fromtimestamp(
                        subscription["current_period_end"]
                    )
                    db.commit()

            return {"status": "processed", "tenant_id": tenant_id}
        finally:
            db.close()

    def _handle_subscription_deleted(self, subscription: Dict) -> Dict:
        """Handle subscription deleted (canceled) event"""
        from src.db.session import SessionLocal

        from src.models.saas_models import TenantStatus

        db = SessionLocal()
        try:
            tenant_id = subscription["metadata"].get("tenant_id")
            if tenant_id:
                tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
                if tenant:
                    tenant.subscription_status = SubscriptionStatus.CANCELED
                    tenant.status = TenantStatus.SUSPENDED
                    db.commit()

            return {"status": "processed", "tenant_id": tenant_id}
        finally:
            db.close()

    def _handle_payment_succeeded(self, invoice: Dict) -> Dict:
        """Handle successful payment"""
        from src.db.session import SessionLocal

        db = SessionLocal()
        try:
            customer_id = invoice["customer"]
            customer = stripe.Customer.retrieve(customer_id)
            tenant_id = customer["metadata"].get("tenant_id")

            if tenant_id:
                # Create invoice record
                db_invoice = Invoice(
                    tenant_id=tenant_id,
                    invoice_number=invoice["number"],
                    stripe_invoice_id=invoice["id"],
                    subtotal=invoice["subtotal"] / 100,
                    tax=invoice["tax"] / 100 if invoice.get("tax") else 0,
                    total=invoice["total"] / 100,
                    currency=invoice["currency"].upper(),
                    period_start=datetime.fromtimestamp(invoice["period_start"]),
                    period_end=datetime.fromtimestamp(invoice["period_end"]),
                    status="paid",
                    paid_at=datetime.fromtimestamp(invoice["status_transitions"]["paid_at"]),
                    invoice_pdf_url=invoice.get("invoice_pdf"),
                    hosted_invoice_url=invoice.get("hosted_invoice_url"),
                )
                db.add(db_invoice)
                db.commit()

            return {"status": "processed", "tenant_id": tenant_id}
        finally:
            db.close()

    def _handle_payment_failed(self, invoice: Dict) -> Dict:
        """Handle failed payment"""
        from src.db.session import SessionLocal

        from src.models.saas_models import TenantStatus

        db = SessionLocal()
        try:
            customer_id = invoice["customer"]
            customer = stripe.Customer.retrieve(customer_id)
            tenant_id = customer["metadata"].get("tenant_id")

            if tenant_id:
                # Update tenant status
                tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
                if tenant:
                    tenant.subscription_status = SubscriptionStatus.PAST_DUE
                    db.commit()

                # Send alert email
                self._send_payment_failed_alert(tenant_id, invoice["id"])

            return {"status": "processed", "tenant_id": tenant_id}
        finally:
            db.close()

    def _handle_trial_ending(self, subscription: Dict) -> Dict:
        """Handle trial ending soon"""
        tenant_id = subscription["metadata"].get("tenant_id")

        # Send email notification
        # (Implementation depends on email service)
        print(f"Trial ending soon for tenant: {tenant_id}")

        return {"status": "processed", "tenant_id": tenant_id}

    def _send_payment_failed_alert(self, tenant_id: str, invoice_id: str):
        """Send payment failed alert"""
        # TODO: Implement email/notification service
        print(f"Payment failed for tenant {tenant_id}, invoice {invoice_id}")


# Convenience functions
billing_service = BillingService()
