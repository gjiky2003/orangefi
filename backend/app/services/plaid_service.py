"""
OrangeFi Plaid Integration Service
====================================
Async HTTP client wrapper around Plaid's Link, Transactions, Identity,
Income, Asset Reports, and Credit APIs with graceful fallback when
Plaid is not configured.

Endpoints vary by environment:
  sandbox:    https://sandbox.plaid.com
  development: https://development.plaid.com
  production:  https://production.plaid.com
"""

from __future__ import annotations

import logging
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, Optional

import httpx

from app.config import settings

logger = logging.getLogger("orangefi.integrations.plaid")

# ──────────────────────────────────────────────────────────────────────────────
# Plaid API URLs per environment
# ──────────────────────────────────────────────────────────────────────────────

_PLAID_BASE_URLS = {
    "sandbox": "https://sandbox.plaid.com",
    "development": "https://development.plaid.com",
    "production": "https://production.plaid.com",
}

_MOCK_ACCESS_TOKEN = "access-sandbox-00000000000000000000000000000000"
_MOCK_ITEM_ID = "item-mock-00000000000000000"


# ──────────────────────────────────────────────────────────────────────────────
# Service
# ──────────────────────────────────────────────────────────────────────────────


class PlaidService:
    """Plaid API integration service.

    Wraps Plaid REST endpoints with async HTTP calls. All public methods
    return mock data when the integration is not configured (PLAID_CLIENT_ID
    is None or empty).
    """

    _instance: Optional["PlaidService"] = None

    def __new__(cls) -> "PlaidService":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if getattr(self, "_initialized", False):
            return
        self._initialized = True
        self._configured = bool(settings.PLAID_CLIENT_ID and settings.PLAID_SECRET)
        self._env = settings.PLAID_ENV or "sandbox"
        self._client_id = settings.PLAID_CLIENT_ID or ""
        self._secret = settings.PLAID_SECRET or ""
        self._base_url = _PLAID_BASE_URLS.get(self._env, _PLAID_BASE_URLS["sandbox"])
        self._http_client: Optional[httpx.AsyncClient] = None

        if not self._configured:
            logger.info(
                "PlaidService: not configured (PLAID_CLIENT_ID is empty) — "
                "all methods return mock data"
            )
        else:
            logger.info(
                "PlaidService: initialized for %s environment at %s",
                self._env,
                self._base_url,
            )

    # ── HTTP Client ──────────────────────────────────────────────────────────

    async def _get_client(self) -> httpx.AsyncClient:
        """Return a shared httpx AsyncClient (lazy initialised)."""
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(
                base_url=self._base_url,
                timeout=httpx.Timeout(30.0, connect=10.0),
            )
        return self._http_client

    async def _post(
        self, path: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        """POST to a Plaid API endpoint with client_id/secret attached."""
        payload["client_id"] = self._client_id
        payload["secret"] = self._secret
        client = await self._get_client()
        resp = await client.post(path, json=payload)
        resp.raise_for_status()
        return resp.json()

    def _mock_link_token(self) -> dict[str, Any]:
        return {
            "link_token": "link-sandbox-mock-link-token-string",
            "expiration": (datetime.utcnow() + timedelta(hours=4)).isoformat() + "Z",
            "request_id": "mock-request-id",
        }

    # ── Public Methods ───────────────────────────────────────────────────────

    async def create_link_token(
        self,
        borrower_id: str,
        user_data: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """Create a Plaid Link token for the given borrower.

        Args:
            borrower_id: UUID string of the borrower.
            user_data: Optional dict with keys like ``phone_number``,
                       ``email_address``, ``legal_name``.

        Returns:
            Dict with ``link_token``, ``expiration`` (ISO datetime),
            and ``request_id``.
        """
        if not self._configured:
            logger.warning("Plaid not configured — returning mock link token")
            return self._mock_link_token()

        user: dict[str, Any] = {
            "client_user_id": borrower_id,
        }
        if user_data:
            if "legal_name" in user_data:
                user["legal_name"] = user_data["legal_name"]
            if "phone_number" in user_data:
                user["phone_number"] = user_data["phone_number"]
            if "email_address" in user_data:
                user["email_address"] = user_data["email_address"]

        payload = {
            "user": user,
            "client_name": "OrangeFi",
            "products": ["transactions", "identity", "assets", "income_verification"],
            "country_codes": ["US"],
            "language": "en",
            "webhook": "https://api.orangefi.com/api/v1/integrations/plaid/webhook",
            "account_filters": {
                "depository": {"account_subtypes": ["checking", "savings"]},
            },
        }

        try:
            result = await self._post("/link/token/create", payload)
            return {
                "link_token": result["link_token"],
                "expiration": result["expiration"],
                "request_id": result.get("request_id", ""),
            }
        except Exception:
            logger.exception("Failed to create Plaid link token — falling back to mock")
            return self._mock_link_token()

    async def exchange_public_token(
        self, public_token: str
    ) -> dict[str, Any]:
        """Exchange a public token for an access token and item ID.

        Args:
            public_token: The public token from Plaid Link.

        Returns:
            Dict with ``access_token``, ``item_id``, and ``request_id``.
        """
        if not self._configured:
            logger.warning("Plaid not configured — returning mock token exchange")
            return {
                "access_token": _MOCK_ACCESS_TOKEN,
                "item_id": _MOCK_ITEM_ID,
                "request_id": "mock-request-id",
            }

        payload = {"public_token": public_token}
        try:
            result = await self._post("/item/public_token/exchange", payload)
            return {
                "access_token": result["access_token"],
                "item_id": result["item_id"],
                "request_id": result.get("request_id", ""),
            }
        except Exception:
            logger.exception("Failed to exchange public token")
            raise

    async def get_accounts(
        self, access_token: str
    ) -> list[dict[str, Any]]:
        """Retrieve accounts linked to the given access token.

        Args:
            access_token: Plaid access token.

        Returns:
            List of account dicts with ``account_id``, ``name``, ``balances``,
            ``type``, ``subtype``, ``mask``, etc.
        """
        if not self._configured:
            logger.warning("Plaid not configured — returning mock accounts")
            return [
                {
                    "account_id": "mock-account-001",
                    "name": "Mock Checking",
                    "official_name": "Mock Gold Checking",
                    "mask": "1234",
                    "type": "depository",
                    "subtype": "checking",
                    "balances": {
                        "current": 5420.33,
                        "available": 4892.10,
                        "limit": None,
                        "iso_currency_code": "USD",
                    },
                },
                {
                    "account_id": "mock-account-002",
                    "name": "Mock Savings",
                    "official_name": "Mock High-Yield Savings",
                    "mask": "5678",
                    "type": "depository",
                    "subtype": "savings",
                    "balances": {
                        "current": 12450.00,
                        "available": 12450.00,
                        "limit": None,
                        "iso_currency_code": "USD",
                    },
                },
            ]

        payload = {"access_token": access_token}
        try:
            result = await self._post("/accounts/get", payload)
            return result.get("accounts", [])
        except Exception:
            logger.exception("Failed to get Plaid accounts")
            raise

    async def get_transactions(
        self,
        access_token: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> list[dict[str, Any]]:
        """Retrieve transactions for linked accounts.

        Args:
            access_token: Plaid access token.
            start_date: Start of transaction range (default: 30 days ago).
            end_date: End of transaction range (default: today).

        Returns:
            List of transaction dicts with ``transaction_id``, ``amount``,
            ``date``, ``name``, ``category``, etc.
        """
        if not self._configured:
            logger.warning("Plaid not configured — returning mock transactions")
            today = date.today()
            return [
                {
                    "transaction_id": "mock-txn-001",
                    "account_id": "mock-account-001",
                    "amount": 89.50,
                    "date": (today - timedelta(days=2)).isoformat(),
                    "name": "WHOLE FOODS MARKET",
                    "merchant_name": "Whole Foods Market",
                    "category": ["Food and Drink", "Groceries"],
                    "category_id": "13005000",
                    "payment_channel": "in store",
                    "iso_currency_code": "USD",
                    "pending": False,
                },
                {
                    "transaction_id": "mock-txn-002",
                    "account_id": "mock-account-001",
                    "amount": 1200.00,
                    "date": (today - timedelta(days=5)).isoformat(),
                    "name": "RENT PAYMENT",
                    "merchant_name": "Landlord Services LLC",
                    "category": ["Payment", "Rent"],
                    "category_id": "16000000",
                    "payment_channel": "online",
                    "iso_currency_code": "USD",
                    "pending": False,
                },
                {
                    "transaction_id": "mock-txn-003",
                    "account_id": "mock-account-002",
                    "amount": 500.00,
                    "date": (today - timedelta(days=10)).isoformat(),
                    "name": "TRANSFER TO SAVINGS",
                    "merchant_name": None,
                    "category": ["Transfer", "Internal"],
                    "category_id": "21000000",
                    "payment_channel": "online",
                    "iso_currency_code": "USD",
                    "pending": False,
                },
            ]

        payload = {
            "access_token": access_token,
            "start_date": (start_date or (date.today() - timedelta(days=30))).isoformat(),
            "end_date": (end_date or date.today()).isoformat(),
        }
        try:
            result = await self._post("/transactions/get", payload)
            return result.get("transactions", [])
        except Exception:
            logger.exception("Failed to get Plaid transactions")
            raise

    async def get_identity(
        self, access_token: str
    ) -> dict[str, Any]:
        """Retrieve identity data (names, addresses, emails, phone numbers).

        Args:
            access_token: Plaid access token.

        Returns:
            Dict with ``names``, ``emails``, ``phone_numbers``, ``addresses``.
        """
        if not self._configured:
            logger.warning("Plaid not configured — returning mock identity")
            return {
                "names": ["Jane Doe"],
                "emails": [{"data": "jane.doe@example.com", "primary": True, "type": "primary"}],
                "phone_numbers": [
                    {"data": "+12025551234", "primary": True, "type": "mobile"}
                ],
                "addresses": [
                    {
                        "data": {
                            "city": "San Francisco",
                            "region": "CA",
                            "street": "123 Main St",
                            "postal_code": "94105",
                            "country": "US",
                        },
                        "primary": True,
                    }
                ],
            }

        payload = {"access_token": access_token}
        try:
            result = await self._post("/identity/get", payload)
            return {
                "names": result.get("accounts", [{}])[0].get("owners", [{}])[0].get("names", []),
                "emails": result.get("accounts", [{}])[0].get("owners", [{}])[0].get("emails", []),
                "phone_numbers": result.get("accounts", [{}])[0].get("owners", [{}])[0].get("phone_numbers", []),
                "addresses": result.get("accounts", [{}])[0].get("owners", [{}])[0].get("addresses", []),
            }
        except Exception:
            logger.exception("Failed to get Plaid identity")
            raise

    async def get_credit_report(
        self, access_token: str
    ) -> dict[str, Any]:
        """Retrieve credit report data (via Plaid Credit / Credit Insights).

        Args:
            access_token: Plaid access token.

        Returns:
            Dict with credit report summary or empty if unavailable.
        """
        if not self._configured:
            logger.warning("Plaid not configured — returning mock credit report")
            return {
                "credit_score": 720,
                "credit_score_provider": "plaid",
                "tradelines": [
                    {"name": "Mock Visa Card", "balance": 2500, "credit_limit": 10000, "payment_status": "current"},
                    {"name": "Mock Auto Loan", "balance": 15000, "original_amount": 25000, "payment_status": "current"},
                ],
                "inquiries": [{"date": "2025-10-01", "name": "Mock Lender"}],
                "summary": {
                    "total_credit_limit": 10000,
                    "total_balance": 2500,
                    "credit_utilization_pct": 25.0,
                    "open_accounts": 2,
                    "closed_accounts": 1,
                    "derogatory_marks": 0,
                },
            }

        # Try Plaid Credit Insights or Relay endpoints
        payload = {"access_token": access_token}
        for endpoint in ("/credit/relay/get", "/credit/employment/get"):
            try:
                result = await self._post(endpoint, payload)
                return result
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code == 400:
                    continue
                raise
        logger.warning("Credit report endpoint not available for this item")
        return {}

    async def get_income(self, access_token: str) -> dict[str, Any]:
        """Retrieve income data via Plaid Income / Employment endpoints.

        Args:
            access_token: Plaid access token.

        Returns:
            Dict with income streams, paystubs, or employment info.
        """
        if not self._configured:
            logger.warning("Plaid not configured — returning mock income")
            return {
                "income_streams": [
                    {
                        "name": "Main Salary",
                        "monthly_income": Decimal("6500.00"),
                        "confidence": 0.95,
                        "frequency": "monthly",
                    }
                ],
                "annual_income": Decimal("78000.00"),
                "employer": {"name": "Acme Corp"},
            }

        payload = {"access_token": access_token}
        try:
            # Try income/verification/paystubs/get first
            result = await self._post("/income/verification/paystubs/get", payload)
            return result
        except httpx.HTTPStatusError:
            try:
                result = await self._post("/employment/verification/get", payload)
                return result
            except Exception:
                logger.exception("Failed to get Plaid income data")
                raise
        except Exception:
            logger.exception("Failed to get Plaid income data")
            raise

    async def get_asset_report(
        self, access_token: str
    ) -> dict[str, Any]:
        """Generate / retrieve an asset report for the connected accounts.

        Args:
            access_token: Plaid access token.

        Returns:
            Dict with asset report details or mock fallback.
        """
        if not self._configured:
            logger.warning("Plaid not configured — returning mock asset report")
            return {
                "asset_report_id": "mock-asset-report-001",
                "report": {
                    "accounts": [
                        {
                            "account_id": "mock-account-001",
                            "name": "Mock Checking",
                            "balances": {"current": 5420.33, "available": 4892.10},
                            "transactions": 45,
                            "days_available": 90,
                        }
                    ],
                    "total_accounts": 1,
                    "total_transactions": 45,
                },
            }

        payload = {
            "access_token": [access_token],
            "days_requested": 90,
        }
        try:
            # Create the report
            result = await self._post("/asset_report/create", payload)
            asset_report_id = result.get("asset_report_id", "")
            # Poll for the report
            report_payload = {"asset_report_token": asset_report_id}
            report = await self._post("/asset_report/get", report_payload)
            return report
        except Exception:
            logger.exception("Failed to get Plaid asset report")
            raise

    async def get_investments(
        self, access_token: str
    ) -> dict[str, Any]:
        """Retrieve investment holdings and transactions.

        Args:
            access_token: Plaid access token.

        Returns:
            Dict with ``holdings`` and ``securities`` lists.
        """
        if not self._configured:
            logger.warning("Plaid not configured — returning mock investments")
            return {
                "holdings": [],
                "securities": [],
            }

        payload = {"access_token": access_token}
        try:
            result = await self._post("/investments/holdings/get", payload)
            return {
                "holdings": result.get("holdings", []),
                "securities": result.get("securities", []),
            }
        except Exception:
            logger.exception("Failed to get Plaid investments")
            raise

    async def exchange_token_and_store(
        self,
        public_token: str,
        borrower_id: str,
        institution_id: Optional[str] = None,
        institution_name: Optional[str] = None,
    ) -> dict[str, Any]:
        """Convenience: exchange public token and return full connection data.

        Args:
            public_token: The public token from Plaid Link.
            borrower_id: Borrower UUID string (for reference).
            institution_id: Optional Plaid institution ID.
            institution_name: Optional human-readable institution name.

        Returns:
            Dict with ``access_token``, ``item_id``, and ``accounts`` list.
        """
        exchange = await self.exchange_public_token(public_token)
        access_token = exchange["access_token"]
        item_id = exchange["item_id"]

        accounts = await self.get_accounts(access_token)
        identity = await self.get_identity(access_token)

        return {
            "access_token": access_token,
            "item_id": item_id,
            "institution_id": institution_id or "",
            "institution_name": institution_name or "",
            "accounts": accounts,
            "identity": identity,
        }

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        if self._http_client and not self._http_client.is_closed:
            await self._http_client.aclose()


# ── Singleton ────────────────────────────────────────────────────────────────

plaid_service = PlaidService()
