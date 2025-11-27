"""
Stripe Payment Gateway Integration for Send-Pakket Platform
"""

import stripe
from decimal import Decimal
from django.conf import settings
from django.utils import timezone
from .models import Payment, Subscription, Invoice


class StripePaymentService:
    """Service for handling Stripe payment operations"""

    def __init__(self):
        stripe.api_key = settings.STRIPE_SECRET_KEY
        self.publishable_key = settings.STRIPE_PUBLISHABLE_KEY

    def create_customer(self, company):
        """Create a Stripe customer for the company"""
        try:
            customer = stripe.Customer.create(
                email=company.user.email,
                name=company.name,
                metadata={
                    'company_id': str(company.id),
                    'user_id': str(company.user.id),
                }
            )
            # Update company with Stripe customer ID
            company.stripe_customer_id = customer.id
            company.save()
            return customer
        except stripe.error.StripeError as e:
            raise Exception(f"Failed to create Stripe customer: {str(e)}")

    def get_or_create_customer(self, company):
        """Get existing Stripe customer or create new one"""
        if company.stripe_customer_id:
            try:
                return stripe.Customer.retrieve(company.stripe_customer_id)
            except stripe.error.StripeError:
                # Customer doesn't exist, create new one
                pass

        return self.create_customer(company)

    def create_subscription(self, subscription):
        """Create a Stripe subscription"""
        try:
            customer = self.get_or_create_customer(subscription.company)

            # Create subscription data
            subscription_data = {
                'customer': customer.id,
                'items': [{
                    'price_data': {
                        'currency': subscription.currency.lower(),
                        'product_data': {
                            'name': f'Send-Pakket {subscription.plan_type.title()} Plan',
                            'description': f'Monthly {subscription.plan_type} plan with {subscription.monthly_shipment_limit} shipments',
                        },
                        'unit_amount': int(subscription.monthly_price * 100),  # Convert to cents
                        'recurring': {
                            'interval': subscription.billing_cycle,
                        },
                    },
                }],
                'metadata': {
                    'subscription_id': str(subscription.id),
                    'company_id': str(subscription.company.id),
                },
            }

            # Add trial period if needed
            if subscription.trial_end:
                subscription_data['trial_end'] = int(subscription.trial_end.timestamp())

            stripe_subscription = stripe.Subscription.create(**subscription_data)

            # Update subscription with Stripe data
            subscription.stripe_subscription_id = stripe_subscription.id
            subscription.status = 'active'
            subscription.current_period_start = timezone.now()
            subscription.current_period_end = timezone.now() + timezone.timedelta(days=30)
            subscription.save()

            return stripe_subscription

        except stripe.error.StripeError as e:
            raise Exception(f"Failed to create Stripe subscription: {str(e)}")

    def cancel_subscription(self, subscription):
        """Cancel a Stripe subscription"""
        try:
            if not subscription.stripe_subscription_id:
                raise Exception("Subscription has no Stripe subscription ID")

            stripe_subscription = stripe.Subscription.modify(
                subscription.stripe_subscription_id,
                cancel_at_period_end=True
            )

            subscription.status = 'cancelled'
            subscription.cancelled_at = timezone.now()
            subscription.save()

            return stripe_subscription

        except stripe.error.StripeError as e:
            raise Exception(f"Failed to cancel Stripe subscription: {str(e)}")

    def reactivate_subscription(self, subscription):
        """Reactivate a cancelled Stripe subscription"""
        try:
            if not subscription.stripe_subscription_id:
                raise Exception("Subscription has no Stripe subscription ID")

            stripe_subscription = stripe.Subscription.modify(
                subscription.stripe_subscription_id,
                cancel_at_period_end=False
            )

            subscription.status = 'active'
            subscription.cancelled_at = None
            subscription.save()

            return stripe_subscription

        except stripe.error.StripeError as e:
            raise Exception(f"Failed to reactivate Stripe subscription: {str(e)}")

    def create_payment_intent(self, payment):
        """Create a Stripe payment intent"""
        try:
            customer = self.get_or_create_customer(payment.company)

            intent = stripe.PaymentIntent.create(
                amount=int(payment.amount * 100),  # Convert to cents
                currency=payment.currency.lower(),
                customer=customer.id,
                metadata={
                    'payment_id': str(payment.id),
                    'invoice_id': str(payment.invoice.id) if payment.invoice else '',
                    'company_id': str(payment.company.id),
                },
                description=f'Payment for {payment.invoice.invoice_number if payment.invoice else "subscription"}',
                automatic_payment_methods={
                    'enabled': True,
                },
            )

            # Update payment with client secret
            payment.stripe_payment_intent_id = intent.id
            payment.stripe_client_secret = intent.client_secret
            payment.save()

            return intent

        except stripe.error.StripeError as e:
            raise Exception(f"Failed to create payment intent: {str(e)}")

    def confirm_payment(self, payment_intent_id):
        """Confirm a payment intent"""
        try:
            intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            return intent
        except stripe.error.StripeError as e:
            raise Exception(f"Failed to confirm payment: {str(e)}")

    def create_refund(self, payment, amount=None):
        """Create a refund for a payment"""
        try:
            if not payment.stripe_payment_intent_id:
                raise Exception("Payment has no Stripe payment intent ID")

            refund_amount = amount or payment.amount

            refund = stripe.Refund.create(
                payment_intent=payment.stripe_payment_intent_id,
                amount=int(refund_amount * 100),  # Convert to cents
                metadata={
                    'payment_id': str(payment.id),
                    'company_id': str(payment.company.id),
                },
            )

            return refund

        except stripe.error.StripeError as e:
            raise Exception(f"Failed to create refund: {str(e)}")

    def handle_webhook_event(self, payload, sig_header):
        """Handle Stripe webhook events"""
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )

            # Handle different event types
            if event.type == 'payment_intent.succeeded':
                self._handle_payment_succeeded(event.data.object)
            elif event.type == 'payment_intent.payment_failed':
                self._handle_payment_failed(event.data.object)
            elif event.type == 'invoice.payment_succeeded':
                self._handle_invoice_payment_succeeded(event.data.object)
            elif event.type == 'customer.subscription.updated':
                self._handle_subscription_updated(event.data.object)
            elif event.type == 'customer.subscription.deleted':
                self._handle_subscription_cancelled(event.data.object)

            return event

        except stripe.error.SignatureVerificationError as e:
            raise Exception(f"Webhook signature verification failed: {str(e)}")

    def _handle_payment_succeeded(self, payment_intent):
        """Handle successful payment"""
        payment_id = payment_intent.metadata.get('payment_id')
        if payment_id:
            try:
                payment = Payment.objects.get(id=payment_id)
                payment.status = 'succeeded'
                payment.processed_at = timezone.now()
                payment.gateway_transaction_id = payment_intent.id
                payment.save()

                # Mark invoice as paid if applicable
                if payment.invoice:
                    payment.invoice.status = 'paid'
                    payment.invoice.paid_at = timezone.now()
                    payment.invoice.save()

            except Payment.DoesNotExist:
                pass  # Payment not found, ignore

    def _handle_payment_failed(self, payment_intent):
        """Handle failed payment"""
        payment_id = payment_intent.metadata.get('payment_id')
        if payment_id:
            try:
                payment = Payment.objects.get(id=payment_id)
                payment.status = 'failed'
                payment.failure_reason = payment_intent.last_payment_error.message if payment_intent.last_payment_error else 'Payment failed'
                payment.save()
            except Payment.DoesNotExist:
                pass

    def _handle_invoice_payment_succeeded(self, invoice):
        """Handle successful invoice payment"""
        # This is typically handled by payment intents, but included for completeness
        pass

    def _handle_subscription_updated(self, subscription):
        """Handle subscription updates"""
        subscription_id = subscription.metadata.get('subscription_id')
        if subscription_id:
            try:
                local_subscription = Subscription.objects.get(id=subscription_id)
                local_subscription.status = 'active' if subscription.status == 'active' else 'cancelled'
                local_subscription.current_period_start = timezone.now()
                local_subscription.current_period_end = timezone.now() + timezone.timedelta(days=30)
                local_subscription.save()
            except Subscription.DoesNotExist:
                pass

    def _handle_subscription_cancelled(self, subscription):
        """Handle subscription cancellation"""
        subscription_id = subscription.metadata.get('subscription_id')
        if subscription_id:
            try:
                local_subscription = Subscription.objects.get(id=subscription_id)
                local_subscription.status = 'cancelled'
                local_subscription.cancelled_at = timezone.now()
                local_subscription.save()
            except Subscription.DoesNotExist:
                pass