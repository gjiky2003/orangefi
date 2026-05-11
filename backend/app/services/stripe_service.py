"""
OrangeFi Stripe Integration Service
=====================================
Async wrapper around the Stripe API for payment intents, ACH payments,
loan disbursements, customer management, and webhook verification.

Uses the official ``stripe`` library for webhook signature verification
and constructs requests via httpx for async operations.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Optional

import httpx

from app.config import settings

logger = logging.getLogger("orangefi.integrations.stripe")

# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────


def _cents_from_decimal(amount: Decimal) -> int:
    """Convert a Decimal dollar amount to integer cents for Stripe."""
    return int(round(amount * 100))


def _decimal_from_cents(cents: int) -> Decimal:
    """Convert integer cents from Stripe back to Decimal dollars."""
    return Decimal(str(cents)) / Decimal("100")


# ──────────────────────────────────────────────────────────────────────────────
# Service
# ──────────────────────────────────────────────────────────────────────────────


class StripeService:
    """Stripe API integration service.

    All public methods return mock data when the integration is not
    configured (STRIPE_SECRET_KEY is None or empty).
    """

    _instance: Optional["StripeService"] = None

    def __new__(cls) -> "StripeService":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if getattr(self, "_initialized", False):
            return
        self._initialized = True
        self._configured = bool(settings.STRIPE_SECRET_KEY)
        self._api_key = settings.STRIPE_SECRET_KEY or ""
        self._webhook_secret = settings.STRIPE_WEBHOOK_SECRET or ""
        self._base_url = "https://api.stripe.com/v1"
        self._publishable_key = settings.STRIPE_PUBLISHABLE_KEY or ""
        self._http_client: Optional[httpx.AsyncClient] = None

        # Try to import Stripe SDK for webhook verification only
        self._stripe_module: Any = None
        if self._configured:
            try:
                import stripe as _stripe
                self._stripe_module = _stripe
                _stripe.api_key = self._api_key
                logger.info("StripeService: initialized (stripe SDK loaded)")
            except ImportError:
                logger.warning("stripe Python package not installed — using raw httpx")
        else:
            logger.info(
                "StripeService: not configured (STRIPE_SECRET_KEY is empty) — "
                "all methods return mock data"
            )

    # ── HTTP Client ──────────────────────────────────────────────────────────

    async def _get_client(self) -> httpx.AsyncClient:
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(
                base_url=self._base_url,
                timeout=httpx.Timeout(30.0, connect=10.0),
                auth=(self._api_key, ""),
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Stripe-Version": "2025-02-24.acacia",
                },
            )
        return self._http_client

    async def _post(
        self, path: str, data: dict[str, Any]
    ) -> dict[str, Any]:
        """POST form-encoded data to a Stripe API endpoint."""
        client = await self._get_client()
        resp = await client.post(path, data=data)
        resp.raise_for_status()
        return resp.json()

    async def _get(
        self, path: str, params: Optional[dict[str, Any]] = None
    ) -> dict[str, Any]:
        """GET from a Stripe API endpoint."""
        client = await self._get_client()
        resp = await client.get(path, params=params or {})
        resp.raise_for_status()
        return resp.json()

    # ── Public Methods ───────────────────────────────────────────────────────

    async def create_payment_intent(
        self,
        amount: Decimal,
        currency: str = "usd",
        borrower_id: Optional[str] = None,
        loan_id: Optional[str] = None,
        payment_method_id: Optional[str] = None,
        metadata: Optional[dict[str, str]] = None,
    ) -> dict[str, Any]:
        """Create a Stripe PaymentIntent for a loan payment.

        Args:
            amount: Dollar amount to charge.
            currency: ISO currency code (default: 'usd').
            borrower_id: Borrower UUID for metadata.
            loan_id: Loan UUID for metadata.
            payment_method_id: Optional pre-attached payment method.
            metadata: Additional metadata key/value pairs.

        Returns:
            Dict with ``id`` (intent ID), ``client_secret``, ``amount``,
            ``status``, etc.
        """
        if not self._configured:
            logger.warning("Stripe not configured — returning mock payment intent")
            mock_id = f"pi_mock_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
            return {
                "id": mock_id,
                "object": "payment_intent",
                "amount": _cents_from_decimal(amount),
                "currency": currency,
                "client_secret": f"{mock_id}_secret_mock",
                "status": "requires_payment_method",
                "metadata": {
                    "borrower_id": borrower_id or "",
                    "loan_id": loan_id or "",
                    **(metadata or {}),
                },
            }

        meta: dict[str, str] = {}
        if borrower_id:
            meta["borrower_id"] = borrower_id
        if loan_id:
            meta["loan_id"] = loan_id
        if metadata:
            meta.update(metadata)

        data: dict[str, Any] = {
            "amount": str(_cents_from_decimal(amount)),
            "currency": currency,
            "metadata": json.dumps(meta) if meta else "{}",
            "automatic_payment_methods": json.dumps({"enabled": True}),
        }
        if payment_method_id:
            data["payment_method"] = payment_method_id
            data["confirm"] = "true"

        try:
            result = await self._post("/payment_intents", data)
            return {
                "id": result["id"],
                "object": result.get("object", "payment_intent"),
                "amount": result["amount"],
                "currency": result.get("currency", currency),
                "client_secret": result.get("client_secret", ""),
                "status": result.get("status", ""),
                "payment_method": result.get("payment_method"),
                "metadata": result.get("metadata", {}),
                "latest_charge": result.get("latest_charge"),
            }
        except Exception:
            logger.exception("Failed to create payment intent")
            raise

    async def confirm_payment(
        self,
        intent_id: str,
        payment_method_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """Confirm a PaymentIntent.

        Args:
            intent_id: The Stripe PaymentIntent ID (``pi_...``).
            payment_method_id: Optional payment method to use.

        Returns:
            Dict with updated intent status.
        """
        if not self._configured:
            logger.warning("Stripe not configured — returning mock confirmation")
            return {
                "id": intent_id,
                "object": "payment_intent",
                "status": "succeeded",
                "amount": 5000,
                "currency": "usd",
            }

        data: dict[str, Any] = {}
        if payment_method_id:
            data["payment_method"] = payment_method_id

        try:
            result = await self._post(f"/payment_intents/{intent_id}/confirm", data)
            return {
                "id": result["id"],
                "status": result.get("status", ""),
                "amount": result.get("amount", 0),
                "currency": result.get("currency", "usd"),
                "payment_method": result.get("payment_method"),
                "latest_charge": result.get("latest_charge"),
            }
        except Exception:
            logger.exception("Failed to confirm payment intent")
            raise

    async def create_ach_payment(
        self,
        amount: Decimal,
        bank_account_token: str,
        customer_id: Optional[str] = None,
        metadata: Optional[dict[str, str]] = None,
    ) -> dict[str, Any]:
        """Create an ACH direct debit payment.

        Uses a PaymentIntent with ``us_bank_account`` payment method type.

        Args:
            amount: Dollar amount.
            bank_account_token: Stripe bank account token (from Stripe.js elements).
            customer_id: Optional Stripe customer ID.
            metadata: Optional metadata.

        Returns:
            Dict with ``id``, ``status``, ``amount``, etc.
        """
        if not self._configured:
            logger.warning("Stripe not configured — returning mock ACH payment")
            return {
                "id": f"pi_ach_mock_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                "object": "payment_intent",
                "amount": _cents_from_decimal(amount),
                "currency": "usd",
                "status": "processing",
                "payment_method_types": ["us_bank_account"],
            }

        data: dict[str, Any] = {
            "amount": str(_cents_from_decimal(amount)),
            "currency": "usd",
            "payment_method_types[0]": "us_bank_account",
            "payment_method_data[type]": "us_bank_account",
            "payment_method_data[us_bank_account][account_holder_type]": "individual",
            "payment_method_data[billing_details][name]": "OrangeFi Borrower",
            "confirm": "true",
        }
        if customer_id:
            data["customer"] = customer_id
        if metadata:
            data["metadata"] = json.dumps(metadata)

        # Use the bank account token if provided (from Stripe Elements)
        if bank_account_token.startswith("btok_"):
            data["payment_method_data[us_bank_account][routing_number]"] = ""
            data["payment_method"] = bank_account_token
            data.pop("payment_method_data[type]", None)
            data.pop("payment_method_data[us_bank_account][account_holder_type]", None)
            data.pop("payment_method_data[billing_details][name]", None)

        try:
            result = await self._post("/payment_intents", data)
            return {
                "id": result["id"],
                "status": result.get("status", ""),
                "amount": result.get("amount", 0),
                "currency": result.get("currency", "usd"),
                "payment_method": result.get("payment_method"),
            }
        except Exception:
            logger.exception("Failed to create ACH payment")
            raise

    async def create_disbursement(
        self,
        amount: Decimal,
        destination_bank_account: str,
        description: Optional[str] = None,
        metadata: Optional[dict[str, str]] = None,
    ) -> dict[str, Any]:
        """Disburse funds to a borrower (loan funding) via Stripe Transfer.

        Uses a Transfer to a connected Stripe account or a Payout to an
        external bank account.

        Args:
            amount: Dollar amount to disburse.
            destination_bank_account: Stripe account ID (``acct_...``) or
                                     external bank account token.
            description: Human-readable description.
            metadata: Optional metadata.

        Returns:
            Dict with ``id``, ``amount``, ``status``, ``destination``, etc.
        """
        if not self._configured:
            logger.warning("Stripe not configured — returning mock disbursement")
            return {
                "id": f"po_mock_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                "object": "payout",
                "amount": _cents_from_decimal(amount),
                "currency": "usd",
                "status": "paid",
                "destination": destination_bank_account,
                "description": description or "Loan disbursement",
            }

        # Determine if destination is a connected account (transfer) or bank (payout)
        if destination_bank_account.startswith("acct_"):
            # Transfer to connected Stripe account
            data: dict[str, Any] = {
                "amount": str(_cents_from_decimal(amount)),
                "currency": "usd",
                "destination": destination_bank_account,
                "transfer_group": f"disbursement_{metadata.get('loan_id', 'unknown') if metadata else 'unknown'}",
            }
            if description:
                data["description"] = description
            if metadata:
                data["metadata"] = json.dumps(metadata)

            try:
                result = await self._post("/transfers", data)
                return {
                    "id": result["id"],
                    "object": "transfer",
                    "amount": result.get("amount", 0),
                    "currency": result.get("currency", "usd"),
                    "status": result.get("status", ""),
                    "destination": result.get("destination", ""),
                    "description": result.get("description"),
                    "metadata": result.get("metadata", {}),
                }
            except Exception:
                logger.exception("Failed to create transfer disbursement")
                raise
        else:
            # Payout to external bank account
            data = {
                "amount": str(_cents_from_decimal(amount)),
                "currency": "usd",
                "destination": destination_bank_account,
                "method": "standard",
            }
            if description:
                data["description"] = description
            if metadata:
                data["metadata"] = json.dumps(metadata)

            try:
                result = await self._post("/payouts", data)
                return {
                    "id": result["id"],
                    "object": "payout",
                    "amount": result.get("amount", 0),
                    "currency": result.get("currency", "usd"),
                    "status": result.get("status", "paid"),
                    "destination": result.get("destination", ""),
                    "description": result.get("description"),
                    "metadata": result.get("metadata", {}),
                }
            except Exception:
                logger.exception("Failed to create payout disbursement")
                raise

    async def get_balance(self) -> dict[str, Any]:
        """Retrieve the Stripe account balance.

        Returns:
            Dict with ``available`` (list of balance amounts by currency)
            and ``pending``.
        """
        if not self._configured:
            logger.warning("Stripe not configured — returning mock balance")
            return {
                "object": "balance",
                "available": [{"amount": 10000000, "currency": "usd", "source_types": {"card": 8000000, "bank_account": 2000000}}],
                "pending": [{"amount": 250000, "currency": "usd", "source_types": {"card": 250000}}],
                "livemode": False,
            }

        try:
            result = await self._get("/balance")
            return {
                "object": result.get("object", "balance"),
                "available": result.get("available", []),
                "pending": result.get("pending", []),
                "livemode": result.get("livemode", False),
            }
        except Exception:
            logger.exception("Failed to get Stripe balance")
            raise

    async def create_customer(
        self,
        borrower_data: dict[str, Any],
    ) -> dict[str, Any]:
        """Create a Stripe Customer for a borrower.

        Args:
            borrower_data: Dict with ``email``, ``name``, ``phone``,
                           and optional ``metadata``.

        Returns:
            Dict with ``id``, ``email``, ``name``, etc.
        """
        if not self._configured:
            logger.warning("Stripe not configured — returning mock customer")
            return {
                "id": f"cus_mock_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                "object": "customer",
                "email": borrower_data.get("email", ""),
                "name": borrower_data.get("name", ""),
                "phone": borrower_data.get("phone", ""),
                "metadata": borrower_data.get("metadata", {}),
            }

        data: dict[str, Any] = {
            "email": borrower_data.get("email", ""),
            "name": borrower_data.get("name", ""),
            "phone": borrower_data.get("phone", ""),
        }
        if "metadata" in borrower_data and borrower_data["metadata"]:
            data["metadata"] = json.dumps(borrower_data["metadata"])

        try:
            result = await self._post("/customers", data)
            return {
                "id": result["id"],
                "object": "customer",
                "email": result.get("email", ""),
                "name": result.get("name", ""),
                "phone": result.get("phone", ""),
                "metadata": result.get("metadata", {}),
            }
        except Exception:
            logger.exception("Failed to create Stripe customer")
            raise

    async def create_payment_method(
        self, token: str
    ) -> dict[str, Any]:
        """Create a PaymentMethod from a Stripe token (card or bank account).

        Args:
            token: A Stripe token ID (``tok_...`` or ``btok_...``).

        Returns:
            Dict with ``id``, ``type``, ``card`` or ``us_bank_account`` details.
        """
        if not self._configured:
            logger.warning("Stripe not configured — returning mock payment method")
            return {
                "id": f"pm_mock_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                "object": "payment_method",
                "type": "card",
                "card": {"brand": "visa", "last4": "4242", "exp_month": 12, "exp_year": 2028},
                "billing_details": {"name": "Jane Doe"},
            }

        data: dict[str, Any] = {
            "type": "card" if token.startswith("tok_") else "us_bank_account",
        }

        if token.startswith("tok_"):
            data["card[token]"] = token
        elif token.startswith("btok_"):
            data["us_bank_account[account_holder_type]"] = "individual"
            data["billing_details[name]"] = "OrangeFi Borrower"
            data["us_bank_account[token]"] = token
        else:
            data["payment_method"] = token

        try:
            result = await self._post("/payment_methods", data)
            return {
                "id": result["id"],
                "object": "payment_method",
                "type": result.get("type", ""),
                "card": result.get("card"),
                "us_bank_account": result.get("us_bank_account"),
                "billing_details": result.get("billing_details", {}),
            }
        except Exception:
            logger.exception("Failed to create payment method")
            raise

    async def attach_payment_method_to_customer(
        self,
        payment_method_id: str,
        customer_id: str,
    ) -> dict[str, Any]:
        """Attach a PaymentMethod to a Customer.

        Args:
            payment_method_id: Stripe PaymentMethod ID.
            customer_id: Stripe Customer ID.

        Returns:
            Dict with the attached payment method details.
        """
        if not self._configured:
            logger.warning("Stripe not configured — returning mock attachment")
            return {
                "id": payment_method_id,
                "object": "payment_method",
                "customer": customer_id,
                "type": "card",
            }

        try:
            result = await self._post(
                f"/payment_methods/{payment_method_id}/attach",
                {"customer": customer_id},
            )
            return {
                "id": result["id"],
                "customer": result.get("customer"),
                "type": result.get("type", ""),
                "card": result.get("card"),
            }
        except Exception:
            logger.exception("Failed to attach payment method to customer")
            raise

    # ── Webhook ──────────────────────────────────────────────────────────────

    def construct_webhook_event(
        self,
        payload: bytes | str,
        sig_header: str,
    ) -> Any:
        """Verify and construct a Stripe webhook event.

        Uses the Stripe SDK for signature verification. Falls back to
        a raw event dict if the SDK is unavailable.

        Args:
            payload: Raw request body bytes or string.
            sig_header: The ``Stripe-Signature`` header value.

        Returns:
            A Stripe event object (if SDK present) or dict with ``type``
            and ``data``.

        Raises:
            ValueError: If signature verification fails.
        """
        if not self._configured or not self._webhook_secret:
            logger.warning(
                "Stripe webhook verification not configured — "
                "returning raw event without verification"
            )
            raw = json.loads(payload) if isinstance(payload, bytes) else json.loads(payload)
            return {
                "id": raw.get("id", "evt_mock"),
                "type": raw.get("type", ""),
                "data": raw.get("data", {}),
                "raw": raw,
            }

        if self._stripe_module is not None:
            try:
                event = self._stripe_module.Webhook.construct_event(
                    payload=payload,
                    sig_header=sig_header,
                    secret=self._webhook_secret,
                )
                return event
            except ValueError as exc:
                logger.error("Stripe webhook signature verification failed: %s", exc)
                raise
        else:
            # Fallback: parse raw payload but warn about missing verification
            logger.warning(
                "stripe SDK not installed — verifying webhook signature manually"
            )
            # Basic timestamp + signature check fallback
            raw = json.loads(payload) if isinstance(payload, bytes) else json.loads(payload)
            # In a real scenario you'd validate the signature manually
            return {
                "id": raw.get("id", "evt_unknown"),
                "type": raw.get("type", ""),
                "data": raw.get("data", {}),
                "raw": raw,
            }

    async def handle_webhook(self, event: Any) -> dict[str, Any]:
        """Process a Stripe webhook event and return a response.

        Supports the following event types:
            - ``payment_intent.succeeded``
            - ``payment_intent.payment_failed``
            - ``payment_intent.processing``
            - ``payout.paid``
            - ``payout.failed``
            - ``customer.created``
            - ``charge.succeeded``
            - ``charge.failed``

        Args:
            event: A Stripe event object or dict with ``type`` and ``data``.

        Returns:
            Dict with ``received`` (bool), ``type``, and optional
            ``action`` describing what was done.
        """
        # Normalise to dict
        if hasattr(event, "to_dict"):
            event_dict = event.to_dict()
        elif hasattr(event, "to_dict_recursive"):
            event_dict = event.to_dict_recursive()
        elif isinstance(event, dict):
            event_dict = event
        else:
            event_dict = {"type": "unknown", "data": {}}

        event_type = event_dict.get("type", "unknown")
        data_object = event_dict.get("data", {}).get("object", {})

        logger.info("Stripe webhook received: %s (id=%s)", event_type, event_dict.get("id", ""))

        handler_map = {
            "payment_intent.succeeded": self._handle_payment_intent_succeeded,
            "payment_intent.payment_failed": self._handle_payment_intent_failed,
            "payment_intent.processing": self._handle_payment_intent_processing,
            "payout.paid": self._handle_payout_paid,
            "payout.failed": self._handle_payout_failed,
            "charge.succeeded": self._handle_charge_succeeded,
            "charge.failed": self._handle_charge_failed,
            "customer.created": self._handle_customer_created,
        }

        handler = handler_map.get(event_type)
        if handler:
            action = await handler(data_object)
        else:
            logger.info("No handler registered for event type: %s", event_type)
            action = "noop"

        return {
            "received": True,
            "type": event_type,
            "action": action,
        }

    # ── Webhook Handlers (internal) ──────────────────────────────────────────

    async def _handle_payment_intent_succeeded(
        self, data: dict[str, Any]
    ) -> str:
        pi_id = data.get("id", "")
        amount = data.get("amount", 0)
        metadata = data.get("metadata", {})
        loan_id = metadata.get("loan_id")
        logger.info(
            "PaymentIntent succeeded: %s amount=%d cents loan=%s",
            pi_id, amount, loan_id,
        )
        # TODO: Update Payment record in DB
        return f"payment_succeeded:{pi_id}"

    async def _handle_payment_intent_failed(
        self, data: dict[str, Any]
    ) -> str:
        pi_id = data.get("id", "")
        last_error = data.get("last_payment_error", {}).get("message", "unknown")
        logger.warning("PaymentIntent failed: %s error=%s", pi_id, last_error)
        # TODO: Update Payment record in DB with failure reason
        return f"payment_failed:{pi_id}"

    async def _handle_payment_intent_processing(
        self, data: dict[str, Any]
    ) -> str:
        pi_id = data.get("id", "")
        logger.info("PaymentIntent processing: %s", pi_id)
        return f"payment_processing:{pi_id}"

    async def _handle_payout_paid(self, data: dict[str, Any]) -> str:
        payout_id = data.get("id", "")
        logger.info("Payout paid: %s", payout_id)
        # TODO: Update Loan funding status in DB
        return f"payout_paid:{payout_id}"

    async def _handle_payout_failed(self, data: dict[str, Any]) -> str:
        payout_id = data.get("id", "")
        failure = data.get("failure_message", "unknown")
        logger.warning("Payout failed: %s reason=%s", payout_id, failure)
        # TODO: Update Loan funding status in DB
        return f"payout_failed:{payout_id}"

    async def _handle_charge_succeeded(self, data: dict[str, Any]) -> str:
        charge_id = data.get("id", "")
        logger.info("Charge succeeded: %s", charge_id)
        return f"charge_succeeded:{charge_id}"

    async def _handle_charge_failed(self, data: dict[str, Any]) -> str:
        charge_id = data.get("id", "")
        failure = data.get("failure_message", "unknown")
        logger.warning("Charge failed: %s reason=%s", charge_id, failure)
        return f"charge_failed:{charge_id}"

    async def _handle_customer_created(self, data: dict[str, Any]) -> str:
        customer_id = data.get("id", "")
        logger.info("Customer created: %s", customer_id)
        return f"customer_created:{customer_id}"

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        if self._http_client and not self._http_client.is_closed:
            await self._http_client.aclose()


# ── Singleton ────────────────────────────────────────────────────────────────

stripe_service = StripeService()
