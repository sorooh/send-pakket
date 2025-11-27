"""
Stripe Webhook Handler for Send-Pakket Platform
"""

import json
import stripe
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response

from core.models import Company
from .models import Subscription, Payment, Invoice
from .stripe_service import StripePaymentService


@csrf_exempt
@require_POST
def stripe_webhook(request):
    """
    Handle Stripe webhook events
    """
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')

    try:
        # Verify webhook signature
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )

    except ValueError as e:
        # Invalid payload
        return HttpResponse(status=400)

    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        return HttpResponse(status=400)

    # Handle the event
    try:
        if event.type == 'customer.subscription.created':
            handle_subscription_created(event.data.object)

        elif event.type == 'customer.subscription.updated':
            handle_subscription_updated(event.data.object)

        elif event.type == 'customer.subscription.deleted':
            handle_subscription_cancelled(event.data.object)

        elif event.type == 'invoice.payment_succeeded':
            handle_invoice_payment_succeeded(event.data.object)

        elif event.type == 'invoice.payment_failed':
            handle_invoice_payment_failed(event.data.object)

        elif event.type == 'payment_intent.succeeded':
            handle_payment_intent_succeeded(event.data.object)

        elif event.type == 'payment_intent.payment_failed':
            handle_payment_intent_failed(event.data.object)

        else:
            # Unexpected event type
            print(f'Unhandled event type: {event.type}')

    except Exception as e:
        print(f'Error processing webhook: {str(e)}')
        return HttpResponse(status=500)

    return HttpResponse(status=200)


def handle_subscription_created(stripe_subscription):
    """Handle subscription creation"""
    try:
        company = Company.objects.get(stripe_customer_id=stripe_subscription.customer)

        subscription, created = Subscription.objects.get_or_create(
            stripe_subscription_id=stripe_subscription.id,
            defaults={
                'company': company,
                'status': 'active',
                'plan_type': stripe_subscription.items.data[0].price.lookup_key or 'standard',
                'billing_cycle': 'monthly' if stripe_subscription.items.data[0].price.recurring.interval == 'month' else 'yearly',
                'unit_price': stripe_subscription.items.data[0].price.unit_amount / 100,  # Convert from cents
                'current_period_start': timezone.datetime.fromtimestamp(stripe_subscription.current_period_start),
                'current_period_end': timezone.datetime.fromtimestamp(stripe_subscription.current_period_end),
            }
        )

        if not created:
            # Update existing subscription
            subscription.status = 'active'
            subscription.current_period_start = timezone.datetime.fromtimestamp(stripe_subscription.current_period_start)
            subscription.current_period_end = timezone.datetime.fromtimestamp(stripe_subscription.current_period_end)
            subscription.save()

    except Company.DoesNotExist:
        print(f'Company not found for Stripe customer: {stripe_subscription.customer}')
    except Exception as e:
        print(f'Error handling subscription created: {str(e)}')


def handle_subscription_updated(stripe_subscription):
    """Handle subscription updates"""
    try:
        subscription = Subscription.objects.get(stripe_subscription_id=stripe_subscription.id)

        subscription.status = 'active' if stripe_subscription.status == 'active' else 'cancelled'
        subscription.current_period_start = timezone.datetime.fromtimestamp(stripe_subscription.current_period_start)
        subscription.current_period_end = timezone.datetime.fromtimestamp(stripe_subscription.current_period_end)
        subscription.save()

    except Subscription.DoesNotExist:
        print(f'Subscription not found: {stripe_subscription.id}')
    except Exception as e:
        print(f'Error handling subscription updated: {str(e)}')


def handle_subscription_cancelled(stripe_subscription):
    """Handle subscription cancellation"""
    try:
        subscription = Subscription.objects.get(stripe_subscription_id=stripe_subscription.id)

        subscription.status = 'cancelled'
        subscription.cancelled_at = timezone.now()
        subscription.save()

    except Subscription.DoesNotExist:
        print(f'Subscription not found: {stripe_subscription.id}')
    except Exception as e:
        print(f'Error handling subscription cancelled: {str(e)}')


def handle_invoice_payment_succeeded(stripe_invoice):
    """Handle successful invoice payment"""
    try:
        # Find or create invoice
        invoice, created = Invoice.objects.get_or_create(
            stripe_invoice_id=stripe_invoice.id,
            defaults={
                'company': Company.objects.get(stripe_customer_id=stripe_invoice.customer),
                'status': 'paid',
                'total_amount': stripe_invoice.amount_due / 100,  # Convert from cents
                'currency': stripe_invoice.currency.upper(),
                'due_date': timezone.datetime.fromtimestamp(stripe_invoice.due_date) if stripe_invoice.due_date else None,
                'paid_at': timezone.now(),
            }
        )

        if not created:
            invoice.status = 'paid'
            invoice.paid_at = timezone.now()
            invoice.save()

        # Update subscription if this is a subscription invoice
        if stripe_invoice.subscription:
            try:
                subscription = Subscription.objects.get(stripe_subscription_id=stripe_invoice.subscription)
                subscription.current_period_shipments = 0  # Reset usage
                subscription.save()
            except Subscription.DoesNotExist:
                pass

    except Company.DoesNotExist:
        print(f'Company not found for Stripe customer: {stripe_invoice.customer}')
    except Exception as e:
        print(f'Error handling invoice payment succeeded: {str(e)}')


def handle_invoice_payment_failed(stripe_invoice):
    """Handle failed invoice payment"""
    try:
        invoice = Invoice.objects.get(stripe_invoice_id=stripe_invoice.id)
        invoice.status = 'overdue'
        invoice.save()

    except Invoice.DoesNotExist:
        print(f'Invoice not found: {stripe_invoice.id}')
    except Exception as e:
        print(f'Error handling invoice payment failed: {str(e)}')


def handle_payment_intent_succeeded(stripe_payment_intent):
    """Handle successful payment intent"""
    try:
        payment = Payment.objects.get(stripe_payment_intent_id=stripe_payment_intent.id)

        payment.status = 'succeeded'
        payment.processed_at = timezone.now()
        payment.gateway_transaction_id = stripe_payment_intent.id
        payment.save()

        # Update related invoice
        if payment.invoice:
            payment.invoice.status = 'paid'
            payment.invoice.paid_at = timezone.now()
            payment.invoice.save()

    except Payment.DoesNotExist:
        print(f'Payment not found for intent: {stripe_payment_intent.id}')
    except Exception as e:
        print(f'Error handling payment intent succeeded: {str(e)}')


def handle_payment_intent_failed(stripe_payment_intent):
    """Handle failed payment intent"""
    try:
        payment = Payment.objects.get(stripe_payment_intent_id=stripe_payment_intent.id)

        payment.status = 'failed'
        payment.failure_reason = stripe_payment_intent.last_payment_error.message if stripe_payment_intent.last_payment_error else 'Payment failed'
        payment.save()

    except Payment.DoesNotExist:
        print(f'Payment not found for intent: {stripe_payment_intent.id}')
    except Exception as e:
        print(f'Error handling payment intent failed: {str(e)}')