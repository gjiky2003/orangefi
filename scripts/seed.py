#!/usr/bin/env python3
"""
OrangeFi Seed Script — Comprehensive Development Data Generator
================================================================

Generates realistic synthetic data for local development and testing:

  - 1 admin user
  - 50 borrowers with real-name generation, credit profiles, and Plaid connections
  - 100+ loan applications across all statuses (draft → submitted → approved → funded → declined → cancelled)
  - 30 funded loans with amortization schedules (6 months of payment history)
  - Underwriting results (AI scores, tiers, decisions) for every application
  - Audit log entries for all major actions
  - Compliance events (adverse action notices, ECOA disclosures, consent records)

Usage:
    cd ~/orangefi
    python scripts/seed.py                      # seed with defaults
    python scripts/seed.py --count 100          # override borrower count
    python scripts/seed.py --applications 200   # override application count
    python scripts/seed.py --truncate           # wipe all data before seeding

Requires:
    - Running PostgreSQL with asyncpg
    - DATABASE_URL env var or default local config
"""

from __future__ import annotations

import argparse
import asyncio
import enum
import hashlib
import json
import math
import os
import random
import string
import sys
import uuid
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Optional

# ═══════════════════════════════════════════════════════════════════════════════
# Path setup — allow running from project root or scripts/ directory
# ═══════════════════════════════════════════════════════════════════════════════

_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://orangefi:orangefi@localhost:5432/orangefi",
)

# ═══════════════════════════════════════════════════════════════════════════════
# SQLAlchemy imports
# ═══════════════════════════════════════════════════════════════════════════════

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.database import Base
from app.models import (
    AdminRole,
    AdminUser,
    Application,
    ApplicationStatus,
    AuditAction,
    AuditLog,
    Borrower,
    ComplianceEvent,
    ComplianceEventType,
    CreditPull,
    CreditPullType,
    Document,
    DocumentStatus,
    DocumentType,
    Loan,
    LoanStatus,
    Payment,
    PaymentStatus,
    PlaidConnection,
    PlaidConnectionStatus,
    UnderwritingDecision,
    UnderwritingResult,
)
from app.utils.security import hash_password

# ═══════════════════════════════════════════════════════════════════════════════
# Realistic Name & Data Generation (no external faker dependency)
# ═══════════════════════════════════════════════════════════════════════════════

FIRST_NAMES: list[str] = [
    "James", "Mary", "Robert", "Patricia", "John", "Jennifer", "Michael", "Linda",
    "David", "Elizabeth", "William", "Barbara", "Richard", "Susan", "Joseph", "Jessica",
    "Thomas", "Sarah", "Christopher", "Karen", "Charles", "Lisa", "Daniel", "Nancy",
    "Matthew", "Betty", "Anthony", "Margaret", "Mark", "Sandra", "Donald", "Ashley",
    "Steven", "Kimberly", "Paul", "Emily", "Andrew", "Donna", "Joshua", "Michelle",
    "Kenneth", "Carol", "Kevin", "Amanda", "Brian", "Dorothy", "George", "Melissa",
    "Timothy", "Deborah", "Ronald", "Stephanie", "Edward", "Rebecca", "Jason", "Sharon",
    "Jeffrey", "Laura", "Ryan", "Cynthia", "Jacob", "Kathleen", "Gary", "Amy",
    "Nicholas", "Angela", "Eric", "Shirley", "Jonathan", "Anna", "Stephen", "Brenda",
    "Larry", "Pamela", "Justin", "Emma", "Scott", "Nicole", "Brandon", "Helen",
    "Benjamin", "Samantha", "Samuel", "Katherine", "Raymond", "Christine", "Gregory",
    "Deanna", "Frank", "Maria", "Alexander", "Heather", "Patrick", "Diane", "Jack",
    "Ruth", "Dennis", "Julie", "Jerry", "Olivia",
]

LAST_NAMES: list[str] = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
    "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
    "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson",
    "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson", "Walker",
    "Young", "Allen", "King", "Wright", "Scott", "Torres", "Nguyen", "Hill", "Flores",
    "Green", "Adams", "Nelson", "Baker", "Hall", "Rivera", "Campbell", "Mitchell",
    "Carter", "Roberts", "Gomez", "Phillips", "Evans", "Turner", "Diaz", "Parker",
    "Cruz", "Edwards", "Collins", "Reyes", "Stewart", "Morris", "Morales", "Murphy",
    "Cook", "Rogers", "Gutierrez", "Ortiz", "Morgan", "Cooper", "Peterson", "Bailey",
    "Reed", "Kelly", "Howard", "Ramos", "Kim", "Cox", "Ward", "Richardson", "Watson",
    "Brooks", "Chavez", "Wood", "James", "Bennett", "Gray", "Mendoza", "Ruiz",
    "Hughes", "Price", "Alvarez", "Castillo", "Sanders", "Patel", "Myers", "Long",
    "Ross", "Foster", "Jimenez",
]

EMPLOYERS: list[str] = [
    "Acme Corporation", "GlobalTech Solutions", "Meridian Health Systems",
    "Peak Financial Group", "Summit Construction Co.", "Horizon Media Group",
    "Crestline Manufacturing", "Apex Logistics Inc.", "Sterling Education Services",
    "Northside Medical Center", "Prime Retail Partners", "Vanguard Energy Corp",
    "Allied Insurance Brokers", "Pacific Rim Trading", "Metro City School District",
    "Pinnacle Engineering", "Heritage Automotive Group", "Federal Administrative Services",
    "Bayview Hospitality", "Transcontinental Shipping", "Silver Oak Properties",
    "Innovatech Solutions", "Broadleaf Consulting", "Liberty Mutual Services",
    "Cedar Creek Healthcare", "Main Street Diner", "Eastside Community College",
    "United Parcel Logistics", "Capitol Building Supplies", "Coastal Financial Advisors",
    "BrightPath Technologies", "Redwood Senior Living", "Gateway Credit Union",
    "Pioneer Environmental Services", "Maplewood School District", "Ironclad Security Inc.",
    "Golden State Distributors", "Crescent Manufacturing", "Three Rivers Construction",
    "Self-Employed", "Self-Employed", "Self-Employed",
]

LOAN_PURPOSES: list[str] = [
    "debt_consolidation", "home_improvement", "major_purchase",
    "medical_expenses", "business_startup", "education",
    "auto_financing", "vacation", "wedding",
    "moving_relocation", "emergency_expenses", "tax_payment",
]

PURPOSE_DETAILS: dict[str, list[str]] = {
    "debt_consolidation": [
        "Consolidating 3 credit cards with high APR",
        "Paying off personal loan and credit card debt",
        "Refinancing multiple monthly payments into one",
    ],
    "home_improvement": [
        "Kitchen renovation and new appliances",
        "Bathroom remodel and flooring replacement",
        "New roof and solar panel installation",
        "Basement finishing and home office setup",
    ],
    "major_purchase": [
        "New HVAC system installation",
        "Furniture set for entire home",
        "High-end laptop and equipment",
    ],
    "medical_expenses": [
        "Dental surgery and implants",
        "Uncovered medical procedure costs",
        "Physical therapy and rehabilitation",
    ],
    "business_startup": [
        "Equipment purchase for new small business",
        "Inventory and supplies for retail store",
        "Website development and marketing",
    ],
    "education": [
        "Professional certification program",
        "Online bootcamp tuition",
        "Continuing education courses",
    ],
    "auto_financing": [
        "Used car purchase from private seller",
        "Vehicle repair and maintenance",
        "Down payment on certified pre-owned vehicle",
    ],
    "vacation": [
        "Family trip to national parks",
        "International travel expenses",
        "Extended stay vacation rental",
    ],
    "wedding": [
        "Venue deposit and catering",
        "Wedding photography and attire",
        "Honeymoon travel package",
    ],
    "moving_relocation": [
        "Cross-country moving expenses",
        "Security deposit and first month rent",
        "Moving truck and storage costs",
    ],
    "emergency_expenses": [
        "Emergency home plumbing repair",
        "Unexpected vehicle transmission repair",
        "Emergency veterinary care",
    ],
    "tax_payment": [
        "Annual property tax payment",
        "Estimated quarterly tax payment",
        "Back tax payment plan",
    ],
}

BANKS: list[tuple[str, str, str]] = [
    ("Chase Bank", "Chase", "checking"),
    ("Bank of America", "BofA", "checking"),
    ("Wells Fargo", "Wells Fargo", "checking"),
    ("US Bank", "US Bank", "savings"),
    ("Citibank", "Citi", "checking"),
    ("PNC Bank", "PNC", "checking"),
    ("TD Bank", "TD", "savings"),
    ("Capital One", "Capital One", "checking"),
    ("Ally Bank", "Ally", "savings"),
    ("Charles Schwab", "Schwab", "checking"),
]

# ═══════════════════════════════════════════════════════════════════════════════
# Credit profile templates
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class CreditProfile:
    """A borrower's creditworthiness profile used for generating underwriting data."""

    credit_score: int
    credit_tier: str          # prime, near_prime, subprime
    score_range: str          # e.g. "720-779"
    monthly_income_range: tuple[int, int]
    dti_range: tuple[float, float]        # debt-to-income ratio range
    employment_stability: str  # stable, moderate, unstable
    ai_tier: str              # A+, A, B, C, D, F
    ai_score_range: tuple[float, float]


CREDIT_PROFILES: list[CreditProfile] = [
    CreditProfile(780, "prime", "780-850", (8000, 25000), (0.10, 0.25), "stable", "A+", (0.85, 0.99)),
    CreditProfile(740, "prime", "720-779", (6000, 18000), (0.15, 0.30), "stable", "A", (0.75, 0.88)),
    CreditProfile(700, "near_prime", "680-719", (4500, 12000), (0.20, 0.36), "stable", "B", (0.60, 0.78)),
    CreditProfile(660, "near_prime", "640-679", (3500, 9000), (0.25, 0.40), "moderate", "C", (0.45, 0.63)),
    CreditProfile(620, "subprime", "600-639", (2500, 7000), (0.30, 0.50), "moderate", "D", (0.30, 0.48)),
    CreditProfile(560, "subprime", "500-599", (1800, 5000), (0.35, 0.60), "unstable", "F", (0.10, 0.32)),
]

# ── Weights: higher index = more common for diversity ──
CREDIT_PROFILE_WEIGHTS = [15, 25, 25, 20, 10, 5]


def pick_credit_profile() -> CreditProfile:
    return random.choices(CREDIT_PROFILES, weights=CREDIT_PROFILE_WEIGHTS, k=1)[0]


def generate_phone() -> str:
    return f"+1{random.randint(200, 999)}{random.randint(200, 999)}-{random.randint(1000, 9999)}"


def generate_email(first: str, last: str, idx: int) -> str:
    domains = ["gmail.com", "yahoo.com", "outlook.com", "protonmail.com",
               "icloud.com", "orange.com", "fastmail.com"]
    variants = [
        f"{first.lower()}.{last.lower()}",
        f"{first.lower()[0]}{last.lower()}",
        f"{first.lower()}{last.lower()}",
        f"{first.lower()}.{last.lower()}.{idx}",
    ]
    return f"{random.choice(variants)}{idx if idx % 5 == 0 else ''}@{random.choice(domains)}"


def generate_ssn_encrypted() -> bytes:
    """Generate a fake SSN-like encrypted blob (just for seeding — not real PII)."""
    fake_ssn = f"{random.randint(100, 999)}-{random.randint(10, 99)}-{random.randint(1000, 9999)}"
    # In a real scenario this would use AES-256; we just store a hash for seed data
    return hashlib.sha256(fake_ssn.encode()).digest()


def generate_address() -> dict[str, str]:
    streets = ["Oak", "Maple", "Cedar", "Pine", "Elm", "Birch", "Walnut", "Cherry",
               "Main", "First", "Second", "Park", "Highland", "Lake", "River",
               "Sunset", "Washington", "Lincoln", "Jefferson", "Madison"]
    street_types = ["St", "Ave", "Blvd", "Dr", "Ln", "Ct", "Way", "Pl", "Rd"]

    cities_states: list[tuple[str, str, str]] = [
        ("New York", "NY", "10001"), ("Los Angeles", "CA", "90001"),
        ("Chicago", "IL", "60601"), ("Houston", "TX", "77001"),
        ("Phoenix", "AZ", "85001"), ("Philadelphia", "PA", "19101"),
        ("San Antonio", "TX", "78201"), ("San Diego", "CA", "92101"),
        ("Dallas", "TX", "75201"), ("Austin", "TX", "73301"),
        ("Portland", "OR", "97201"), ("Seattle", "WA", "98101"),
        ("Denver", "CO", "80201"), ("Atlanta", "GA", "30301"),
        ("Miami", "FL", "33101"), ("Boston", "MA", "02101"),
        ("Nashville", "TN", "37201"), ("Charlotte", "NC", "28201"),
        ("Minneapolis", "MN", "55401"), ("Tampa", "FL", "33601"),
    ]

    city, state, zip_base = random.choice(cities_states)
    zip_code = f"{zip_base[:5]}{random.randint(1000, 9999)}"[:5] if random.random() > 0.5 else zip_base[:5]

    return {
        "line1": f"{random.randint(100, 9999)} {random.choice(streets)} {random.choice(street_types)}",
        "line2": f"" if random.random() > 0.3 else f"Unit {random.randint(1, 300)}",
        "city": city,
        "state": state,
        "zip": zip_code,
    }


def generate_employer() -> tuple[str, str]:
    employer = random.choice(EMPLOYERS)
    statuses = ["employed", "employed", "employed", "self_employed", "employed", "employed"]
    if employer == "Self-Employed":
        status = "self_employed"
    else:
        status = random.choice(statuses)
    return employer, status


def random_date(start_year: int, end_year: int) -> date:
    start = date(start_year, 1, 1)
    end = date(end_year, 12, 31)
    delta = (end - start).days
    return start + timedelta(days=random.randint(0, delta))


def random_datetime(start_year: int, end_year: int) -> datetime:
    d = random_date(start_year, end_year)
    t = timedelta(
        hours=random.randint(0, 23),
        minutes=random.randint(0, 59),
        seconds=random.randint(0, 59),
    )
    return datetime.combine(d, (datetime.min + t).time(), tzinfo=timezone.utc)


def generate_borrower_data(
    idx: int, first: str, last: str, email: str
) -> dict[str, Any]:
    """Generate a dict of borrower fields for insertion."""
    prof = pick_credit_profile()
    income = random.randint(*prof.monthly_income_range)
    dob = random_date(1965, 2000)
    addr = generate_address()
    employer, emp_status = generate_employer()

    return {
        "email": email,
        "phone": generate_phone(),
        "first_name": first,
        "middle_name": random.choice([None, None, None, random.choice(["A.", "M.", "L.", "J.", "D."])]),
        "last_name": last,
        "date_of_birth": dob,
        "ssn_encrypted": generate_ssn_encrypted(),
        "income_encrypted": None,  # simplified
        "address_line1": addr["line1"],
        "address_line2": addr["line2"] or None,
        "city": addr["city"],
        "state": addr["state"],
        "zip_code": addr["zip"],
        "employer": employer,
        "employment_status": emp_status,
        "monthly_income": Decimal(str(income)),
        "is_identity_verified": random.random() > 0.15,
        "kyc_completed_at": random_datetime(2023, 2024) if random.random() > 0.1 else None,
        "agreed_to_tos_at": random_datetime(2023, 2024),
        "agreed_to_privacy_at": random_datetime(2023, 2024),
        "credit_score_range": prof.score_range,
        "credit_tier": prof.credit_tier,
        "is_active": True,
        "is_deleted": False,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Amortization Calculation
# ═══════════════════════════════════════════════════════════════════════════════

def calculate_monthly_payment(
    principal: Decimal, annual_apr: Decimal, term_months: int
) -> Decimal:
    """Calculate the fixed monthly payment for an amortizing loan.

    Uses the standard amortization formula:
        M = P * [r(1+r)^n] / [(1+r)^n - 1]
    where r = monthly interest rate, n = number of payments.
    """
    if annual_apr == Decimal("0"):
        return principal / Decimal(str(term_months))

    r = (annual_apr / Decimal("100")) / Decimal("12")
    n = Decimal(str(term_months))
    factor = (Decimal("1") + r) ** n
    monthly = principal * (r * factor) / (factor - Decimal("1"))
    return monthly.quantize(Decimal("0.01"))


def generate_amortization_schedule(
    loan_id: uuid.UUID,
    borrower_id: uuid.UUID,
    principal: Decimal,
    apr: Decimal,
    term_months: int,
    first_payment_date: date,
    months_history: int = 6,
) -> list[dict[str, Any]]:
    """Generate an amortization schedule with up to `months_history` of payment history.

    Returns a list of Payment dicts ready for DB insertion.
    """
    monthly_payment = calculate_monthly_payment(principal, apr, term_months)
    r = (apr / Decimal("100")) / Decimal("12")
    balance = principal
    payments: list[dict[str, Any]] = []

    for i in range(term_months):
        scheduled = first_payment_date + timedelta(days=28 * i)
        interest = (balance * r).quantize(Decimal("0.01"))
        principal_part = monthly_payment - interest

        if principal_part > balance:
            principal_part = balance
            interest = Decimal("0.00")

        balance -= principal_part
        if balance < Decimal("0.01"):
            balance = Decimal("0.00")

        # Determine payment status based on history
        is_historic = i < months_history
        if is_historic:
            # 85% chance paid, 10% scheduled (future), 5% failed
            rand = random.random()
            if rand < 0.85:
                status = PaymentStatus.completed
                paid_date = scheduled + timedelta(days=random.randint(-3, 10))
                amount_paid = monthly_payment
            elif rand < 0.95:
                status = PaymentStatus.completed
                paid_date = scheduled + timedelta(days=random.randint(11, 25))
                amount_paid = monthly_payment + Decimal(random.choice([0, 15, 25, 35]))
            else:
                status = PaymentStatus.failed
                paid_date = scheduled + timedelta(days=random.randint(0, 5))
                amount_paid = Decimal("0.00")
        else:
            status = PaymentStatus.scheduled
            paid_date = None
            amount_paid = None

        payments.append({
            "loan_id": loan_id,
            "borrower_id": borrower_id,
            "status": status,
            "scheduled_date": scheduled,
            "paid_date": paid_date,
            "period_start": scheduled - timedelta(days=30),
            "period_end": scheduled,
            "total_amount": monthly_payment,
            "principal_amount": max(principal_part, Decimal("0.00")),
            "interest_amount": interest,
            "fees_amount": Decimal("0.00"),
            "late_fee": Decimal(str(random.choice([0, 0, 0, 15, 25]))) if status == PaymentStatus.completed and (paid_date and paid_date > scheduled + timedelta(days=10)) else Decimal("0.00"),
            "amount_paid": amount_paid,
            "payment_method": random.choice(["ach", "ach", "ach", "debit_card", "wire"]),
            "payment_source": f"acct_{random.randint(1000, 9999)}" if random.random() > 0.3 else None,
            "external_reference": f"ref_{uuid.uuid4().hex[:12]}" if status == PaymentStatus.completed else None,
            "external_status": "settled" if status == PaymentStatus.completed else ("failed" if status == PaymentStatus.failed else None),
            "failure_reason": "Insufficient funds" if status == PaymentStatus.failed else None,
            "retry_count": 0 if status == PaymentStatus.completed else random.randint(0, 3),
            "payment_number": i + 1,
        })

    return payments


# ═══════════════════════════════════════════════════════════════════════════════
# Main Seeder Class
# ═══════════════════════════════════════════════════════════════════════════════

class OrangeFiSeeder:
    """Orchestrates all seed data generation and DB insertion."""

    def __init__(
        self,
        session: AsyncSession,
        *,
        borrower_count: int = 50,
        application_count: int = 120,
        loan_count: int = 30,
        payment_months: int = 6,
    ):
        self.session = session
        self.borrower_count = borrower_count
        self.application_count = application_count
        self.loan_count = loan_count
        self.payment_months = payment_months

        # Stored IDs for cross-referencing
        self.admin_user_id: Optional[uuid.UUID] = None
        self.borrower_ids: list[uuid.UUID] = []
        self.application_ids: list[uuid.UUID] = []
        self.approved_app_ids: list[uuid.UUID] = []
        self.funded_app_ids: list[uuid.UUID] = []
        self.loan_ids: list[uuid.UUID] = []

        # Counters
        self.stats = {
            "borrowers": 0,
            "applications": 0,
            "loans": 0,
            "payments": 0,
            "underwriting_results": 0,
            "credit_pulls": 0,
            "documents": 0,
            "plaid_connections": 0,
            "audit_logs": 0,
            "compliance_events": 0,
        }

    # ═════════════════════════════════════════════════════════════════════════
    # Admin User
    # ═════════════════════════════════════════════════════════════════════════

    async def seed_admin(self) -> None:
        """Create or update the default admin user."""
        result = await self.session.execute(
            __import__("sqlalchemy").select(AdminUser).where(AdminUser.email == "admin@orangefi.com")
        )
        existing = result.scalar_one_or_none()

        if existing:
            print("  ✓ Admin user already exists: admin@orangefi.com")
            self.admin_user_id = existing.id
            return

        admin = AdminUser(
            email="admin@orangefi.com",
            display_name="System Administrator",
            hashed_password=hash_password("Admin123!"),
            role=AdminRole.super_admin,
            is_active=True,
            mfa_enabled=False,
        )
        self.session.add(admin)
        await self.session.flush()
        self.admin_user_id = admin.id
        self.stats["audit_logs"] += 1  # admin creation below
        print("  ✓ Admin user created: admin@orangefi.com / Admin123!")

    # ═════════════════════════════════════════════════════════════════════════
    # Borrowers
    # ═════════════════════════════════════════════════════════════════════════

    async def seed_borrowers(self) -> None:
        """Create synthetic borrowers."""
        used_emails: set[str] = set()

        for i in range(1, self.borrower_count + 1):
            # Pick unique names
            while True:
                first = random.choice(FIRST_NAMES)
                last = random.choice(LAST_NAMES)
                email = generate_email(first, last, i)
                if email not in used_emails:
                    used_emails.add(email)
                    break

            data = generate_borrower_data(i, first, last, email)
            borrower = Borrower(**data)
            self.session.add(borrower)
            await self.session.flush()
            self.borrower_ids.append(borrower.id)

        self.stats["borrowers"] = len(self.borrower_ids)
        print(f"  ✓ Created {len(self.borrower_ids)} borrowers")

    # ═════════════════════════════════════════════════════════════════════════
    # Plaid Connections
    # ═════════════════════════════════════════════════════════════════════════

    async def seed_plaid_connections(self) -> None:
        """Create Plaid bank connections for ~70% of borrowers."""
        count = 0
        for b_id in self.borrower_ids:
            if random.random() > 0.7:
                continue
            bank_name, short_name, acct_type = random.choice(BANKS)
            conn = PlaidConnection(
                borrower_id=b_id,
                plaid_access_token=hashlib.sha256(f"plaid_access_{b_id}".encode()).digest(),
                plaid_item_id=f"plaid_item_{uuid.uuid4().hex[:16]}",
                plaid_institution_id=f"ins_{random.randint(1000, 9999)}",
                institution_name=bank_name,
                account_name=f"{short_name} {acct_type.title()}",
                account_mask=str(random.randint(1000, 9999)),
                account_type=acct_type,
                account_subtype=random.choice(["checking", "savings", "money_market"]),
                status=PlaidConnectionStatus.active,
                last_sync_at=random_datetime(2024, 2024),
                account_balances={
                    "current": random.randint(500, 50000),
                    "available": random.randint(100, 45000),
                },
            )
            self.session.add(conn)
            count += 1

        self.stats["plaid_connections"] = count
        await self.session.flush()
        print(f"  ✓ Created {count} Plaid connections")

    # ═════════════════════════════════════════════════════════════════════════
    # Applications
    # ═════════════════════════════════════════════════════════════════════════

    async def seed_applications(self) -> None:
        """Create loan applications distributed across all statuses.

        Distribution (rough):
          - 10% draft
          - 10% prequal_submitted
          - 10% submitted
          - 10% processing
          - 5% manual_review
          - 20% approved
          - 10% declined
          - 5% docs_sent
          - 15% funded
          - 5% cancelled
        """
        status_choices: list[ApplicationStatus] = [
            ApplicationStatus.draft,
            ApplicationStatus.prequal_submitted,
            ApplicationStatus.submitted,
            ApplicationStatus.processing,
            ApplicationStatus.manual_review,
            ApplicationStatus.approved,
            ApplicationStatus.declined,
            ApplicationStatus.docs_sent,
            ApplicationStatus.funded,
            ApplicationStatus.cancelled,
        ]
        status_weights = [10, 10, 10, 10, 5, 20, 10, 5, 15, 5]

        for i in range(self.application_count):
            b_id = random.choice(self.borrower_ids)
            status = random.choices(status_choices, weights=status_weights, k=1)[0]
            purpose = random.choice(LOAN_PURPOSES)
            amount = random.choice([
                Decimal(str(random.randint(1000, 10000))),
                Decimal(str(random.randint(10000, 25000))),
                Decimal(str(random.randint(25000, 50000))),
            ])
            term = random.choice([12, 24, 36, 48, 60])
            prof = pick_credit_profile()
            income = Decimal(str(random.randint(*prof.monthly_income_range)))

            app_data: dict[str, Any] = {
                "borrower_id": b_id,
                "status": status,
                "requested_amount": amount,
                "requested_term_months": term,
                "loan_purpose": purpose,
                "loan_purpose_details": random.choice(PURPOSE_DETAILS.get(purpose, [""])),
                "total_existing_debt": Decimal(str(random.randint(0, 50000))),
                "monthly_debt_payments": Decimal(str(random.randint(0, 2000))),
                "creditor_details": [
                    {"name": "Visa", "balance": random.randint(1000, 15000), "apr": random.choice([18.99, 22.99, 24.99])}
                ] if random.random() > 0.5 else None,
                "application_monthly_income": income,
                "application_employer": random.choice(EMPLOYERS),
                "application_employment_status": random.choice(["employed", "self_employed"]),
                "years_at_current_job": Decimal(str(round(random.uniform(0.5, 15.0), 1))),
                "housing_status": random.choice(["own", "rent", "live_with_family"]),
                "monthly_housing_payment": Decimal(str(random.randint(500, 3000))),
                "ip_address": f"{random.randint(10, 223)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 254)}",
                "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
            }

            # Set decision-related fields for non-draft statuses
            if status in (ApplicationStatus.approved, ApplicationStatus.funded, ApplicationStatus.docs_sent, ApplicationStatus.declined):
                app_data["decisioned_at"] = random_datetime(2024, 2024)
                app_data["decisioned_by"] = self.admin_user_id

                if status == ApplicationStatus.declined:
                    decline_reasons = [
                        "Debt-to-income ratio exceeds maximum threshold",
                        "Insufficient credit history length",
                        "Recent delinquencies on credit report",
                        "Employment history does not meet minimum requirements",
                        "Credit score below minimum threshold for requested amount",
                        "Verification of income could not be completed",
                    ]
                    app_data["declined_reason"] = random.choice(decline_reasons)
                    app_data["declined_reason_codes"] = ["DTI_EXCEEDS_MAX", "CREDIT_HISTORY_SHORT", "RECENT_DELINQUENCIES"]

            if status == ApplicationStatus.funded:
                app_data["amount_funded"] = amount
                app_data["funded_at"] = random_datetime(2024, 2024)

            application = Application(**app_data)
            self.session.add(application)
            await self.session.flush()
            self.application_ids.append(application.id)

            if status in (ApplicationStatus.approved, ApplicationStatus.funded, ApplicationStatus.docs_sent):
                self.approved_app_ids.append(application.id)
            if status == ApplicationStatus.funded:
                self.funded_app_ids.append(application.id)

        self.stats["applications"] = len(self.application_ids)
        print(f"  ✓ Created {len(self.application_ids)} applications ({len(self.funded_app_ids)} funded, {len(self.approved_app_ids)} approved)")

    # ═════════════════════════════════════════════════════════════════════════
    # Underwriting Results
    # ═════════════════════════════════════════════════════════════════════════

    async def seed_underwriting_results(self) -> None:
        """Create underwriting results for every application."""
        count = 0
        for app_id in self.application_ids:
            # Fetch application to know its status and borrower
            result = await self.session.execute(
                __import__("sqlalchemy").select(Application).where(Application.id == app_id)
            )
            app = result.scalar_one()
            if app is None:
                continue

            prof = pick_credit_profile()
            ai_score = round(random.uniform(*prof.ai_score_range), 4)

            # Determine decision based on application status
            if app.status in (ApplicationStatus.funded, ApplicationStatus.docs_sent, ApplicationStatus.approved):
                decision = UnderwritingDecision.approved
            elif app.status == ApplicationStatus.declined:
                decision = UnderwritingDecision.declined
            elif app.status == ApplicationStatus.manual_review:
                decision = UnderwritingDecision.manual_review
            else:
                decision = UnderwritingDecision.pending

            apr_min = Decimal(str(round(random.uniform(5.99, 14.99), 3)))
            apr_max = Decimal(str(round(apr_min + Decimal(str(random.uniform(2.0, 6.0))), 3)))

            uw_result = UnderwritingResult(
                application_id=app_id,
                borrower_id=app.borrower_id,
                ai_score=ai_score,
                ai_tier=prof.ai_tier,
                ai_confidence=round(random.uniform(0.65, 0.98), 4),
                decision=decision,
                decision_reason="Approved by AI model" if decision == UnderwritingDecision.approved else
                               "Declined: insufficient credit profile" if decision == UnderwritingDecision.declined else
                               "Pending manual review" if decision == UnderwritingDecision.manual_review else
                               "Pending evaluation",
                decision_factors={
                    "income_stability": round(random.uniform(0.3, 1.0), 3),
                    "credit_history": round(random.uniform(0.3, 1.0), 3),
                    "dti_ratio": round(random.uniform(0.3, 1.0), 3),
                    "employment_score": round(random.uniform(0.3, 1.0), 3),
                },
                approved_amount_min=max(app.requested_amount * Decimal("0.8"), Decimal("1000")),
                approved_amount_max=app.requested_amount,
                approved_apr_min=apr_min,
                approved_apr_max=apr_max,
                approved_term_months=[t for t in [12, 24, 36, 48, 60] if t <= app.requested_term_months + 12],
                feature_flags={
                    "auto_pay_discount": random.random() > 0.3,
                    "rate_lower_available": random.random() > 0.6,
                    "skip_payment_option": random.random() > 0.7,
                },
                offer_terms={
                    "monthly_payment": float(calculate_monthly_payment(app.requested_amount, (apr_min + apr_max) / 2, app.requested_term_months)),
                    "total_interest": round(random.uniform(1000, 15000), 2),
                    "origination_fee_pct": random.choice([0, 0, 1, 2, 3, 5]),
                },
                model_version="1.2.0",
                model_name="OrangeRisk-v2",
                inference_time_ms=random.randint(45, 320),
                model_input_snapshot={
                    "credit_score_norm": round(random.uniform(0.3, 1.0), 4),
                    "income_norm": round(random.uniform(0.2, 1.0), 4),
                    "dti_norm": round(random.uniform(0.1, 0.9), 4),
                    "employment_months": random.randint(6, 240),
                },
            )
            self.session.add(uw_result)
            count += 1

        self.stats["underwriting_results"] = count
        await self.session.flush()
        print(f"  ✓ Created {count} underwriting results")

    # ═════════════════════════════════════════════════════════════════════════
    # Credit Pulls
    # ═════════════════════════════════════════════════════════════════════════

    async def seed_credit_pulls(self) -> None:
        """Create soft and hard credit pulls for applications."""
        count = 0
        for app_id in self.application_ids:
            # Only ~40% get credit pulls
            if random.random() > 0.4:
                continue

            result = await self.session.execute(
                __import__("sqlalchemy").select(Application).where(Application.id == app_id)
            )
            app = result.scalar()
            if app is None:
                continue

            # Soft pull for prequal, hard for submitted+
            pull_type = CreditPullType.soft if app.status in (ApplicationStatus.draft, ApplicationStatus.prequal_submitted) else CreditPullType.hard
            score = random.randint(580, 820) if pull_type == CreditPullType.soft else random.randint(550, 800)

            pull = CreditPull(
                borrower_id=app.borrower_id,
                application_id=app_id,
                pull_type=pull_type,
                bureau_name=random.choice(["experian", "transunion", "equifax", "mock"]),
                bureau_reference=f"bureau_ref_{uuid.uuid4().hex[:12]}",
                credit_score=score,
                credit_score_model="vantagescore_4.0" if random.random() > 0.5 else "fico_8",
                credit_summary={
                    "total_accounts": random.randint(3, 25),
                    "open_accounts": random.randint(1, 12),
                    "total_balance": float(Decimal(str(random.randint(0, 100000)))),
                    "credit_utilization_pct": round(random.uniform(0.05, 0.85), 2),
                    "payment_history_pct": round(random.uniform(0.85, 1.0), 2),
                    "length_of_credit_years": round(random.uniform(0.5, 25.0), 1),
                    "recent_inquiries": random.randint(0, 5),
                    "derogatory_marks": random.randint(0, 3),
                },
                consent_received_at=random_datetime(2024, 2024),
                consent_ip_address=f"{random.randint(10, 223)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 254)}",
                adverse_action_notice_sent=app.status == ApplicationStatus.declined,
            )
            self.session.add(pull)
            count += 1

        self.stats["credit_pulls"] = count
        await self.session.flush()
        print(f"  ✓ Created {count} credit pulls")

    # ═════════════════════════════════════════════════════════════════════════
    # Documents
    # ═════════════════════════════════════════════════════════════════════════

    async def seed_documents(self) -> None:
        """Create documents for applications with higher statuses."""
        doc_types = list(DocumentType)
        count = 0

        for app_id in self.application_ids:
            result = await self.session.execute(
                __import__("sqlalchemy").select(Application).where(Application.id == app_id)
            )
            app = result.scalar()
            if app is None:
                continue

            # Only non-draft applications typically have documents
            if app.status == ApplicationStatus.draft:
                continue

            # 1-3 random documents per eligible application
            doc_count = random.randint(1, 3)
            for _ in range(doc_count):
                doc_type = random.choice(doc_types)
                file_ext = {
                    DocumentType.paystub: "pdf",
                    DocumentType.tax_return: "pdf",
                    DocumentType.bank_statement: "pdf",
                    DocumentType.government_id: "png",
                    DocumentType.proof_of_address: "pdf",
                    DocumentType.credit_report: "pdf",
                    DocumentType.other: "pdf",
                }.get(doc_type, "pdf")

                file_key = f"documents/{app.borrower_id}/{app_id}/{uuid.uuid4()}.{file_ext}"
                doc = Document(
                    borrower_id=app.borrower_id,
                    application_id=app_id,
                    status=random.choices(
                        [DocumentStatus.verified, DocumentStatus.uploaded, DocumentStatus.pending],
                        weights=[50, 30, 20],
                        k=1,
                    )[0],
                    document_type=doc_type,
                    file_key=file_key,
                    file_bucket="orangefi-documents",
                    file_name=f"{doc_type.value}_{uuid.uuid4().hex[:8]}.{file_ext}",
                    file_size_bytes=random.randint(50000, 5000000),
                    mime_type=f"application/{file_ext}" if file_ext == "pdf" else f"image/{file_ext}",
                    file_hash=hashlib.sha256(file_key.encode()).hexdigest(),
                    verified_at=random_datetime(2024, 2024) if random.random() > 0.7 else None,
                )
                self.session.add(doc)
                count += 1

        self.stats["documents"] = count
        await self.session.flush()
        print(f"  ✓ Created {count} documents")

    # ═════════════════════════════════════════════════════════════════════════
    # Loans & Payments
    # ═════════════════════════════════════════════════════════════════════════

    async def seed_loans_and_payments(self) -> None:
        """Create funded loans with amortization schedules and payment history."""
        loan_count = min(self.loan_count, len(self.funded_app_ids))

        for app_id in self.funded_app_ids[:loan_count]:
            result = await self.session.execute(
                __import__("sqlalchemy").select(Application).where(Application.id == app_id)
            )
            app = result.scalar()
            if app is None:
                continue

            # Determine loan terms
            apr = Decimal(str(round(random.uniform(6.99, 24.99), 3)))
            term = app.requested_term_months
            amount = app.amount_funded or app.requested_amount
            monthly = calculate_monthly_payment(amount, apr, term)
            origination_fee = (amount * Decimal("0.02")).quantize(Decimal("0.01"))
            disbursement = amount - origination_fee
            origination_date = random_date(2024, 2024)
            first_payment = date(origination_date.year, origination_date.month, 1) + timedelta(days=30)
            if first_payment.month > 12:
                first_payment = date(first_payment.year + 1, 1, 1)

            # Determine loan status based on payment history possibility
            status_choices = [LoanStatus.active, LoanStatus.active, LoanStatus.active,
                              LoanStatus.delinquent, LoanStatus.paid_off]
            status_weights = [55, 20, 10, 10, 5]
            if term <= 6:
                status_weights = [70, 20, 5, 5, 0]
            status = random.choices(status_choices, weights=status_weights, k=1)[0]

            days_past_due = 0
            delinquency_date = None
            if status == LoanStatus.delinquent:
                days_past_due = random.randint(30, 90)
                delinquency_date = date.today() - timedelta(days=days_past_due)

            loan = Loan(
                application_id=app_id,
                borrower_id=app.borrower_id,
                status=status,
                loan_amount=amount,
                apr=apr,
                term_months=term,
                monthly_payment=monthly,
                origination_fee=origination_fee,
                disbursement_amount=disbursement,
                interest_rate_type="fixed",
                interest_accrued=Decimal("0.00"),
                origination_date=origination_date,
                first_payment_date=first_payment,
                maturity_date=date(
                    origination_date.year + (origination_date.month + term - 1) // 12,
                    ((origination_date.month + term - 1) % 12) + 1,
                    min(origination_date.day, 28),
                ),
                days_past_due=days_past_due,
                delinquency_started_at=delinquency_date,
                total_amount_due=(monthly * Decimal(str(max(days_past_due // 30, 1)))).quantize(Decimal("0.01")) if days_past_due > 0 else Decimal("0.00"),
                funding_reference=f"funding_ref_{uuid.uuid4().hex[:12]}",
                funding_metadata={"method": "ach", "source": "bank_transfer"},
            )
            self.session.add(loan)
            await self.session.flush()
            self.loan_ids.append(loan.id)

            # Generate payment schedule with history
            actual_history = min(self.payment_months, max(term // 2, 3))
            payments = generate_amortization_schedule(
                loan_id=loan.id,
                borrower_id=app.borrower_id,
                principal=amount,
                apr=apr,
                term_months=term,
                first_payment_date=first_payment,
                months_history=actual_history,
            )

            for pmt in payments:
                payment = Payment(**pmt)
                self.session.add(payment)

            self.stats["payments"] += len(payments)

        self.stats["loans"] = len(self.loan_ids)
        await self.session.flush()
        print(f"  ✓ Created {len(self.loan_ids)} loans with {self.stats['payments']} payment records")

    # ═════════════════════════════════════════════════════════════════════════
    # Audit Logs
    # ═════════════════════════════════════════════════════════════════════════

    async def seed_audit_logs(self) -> None:
        """Create audit log entries for major lifecycle events."""
        all_actions = list(AuditAction)
        count = 0

        # Audit log for every borrower creation
        for b_id in self.borrower_ids:
            audit = AuditLog(
                actor_id=b_id,
                actor_type="borrower",
                action=AuditAction.user_registered,
                resource_type="borrower",
                resource_id=str(b_id),
                description="Borrower registered via seed script",
                severity="info",
                ip_address=f"{random.randint(10, 223)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 254)}",
            )
            self.session.add(audit)
            count += 1

        # Audit logs for applications
        for app_id in self.application_ids:
            result = await self.session.execute(
                __import__("sqlalchemy").select(Application).where(Application.id == app_id)
            )
            app = result.scalar()
            if app is None:
                continue

            # Application created
            audit = AuditLog(
                actor_id=app.borrower_id,
                actor_type="borrower",
                action=AuditAction.application_created,
                resource_type="application",
                resource_id=str(app_id),
                details={"amount": float(app.requested_amount), "purpose": app.loan_purpose},
                description=f"Application created: ${float(app.requested_amount):.2f} for {app.loan_purpose}",
                severity="info",
                ip_address=app.ip_address,
            )
            self.session.add(audit)
            count += 1

            # Decision made for approved/declined
            if app.status in (ApplicationStatus.approved, ApplicationStatus.declined, ApplicationStatus.funded):
                audit = AuditLog(
                    actor_id=self.admin_user_id,
                    actor_type="admin",
                    admin_user_id=self.admin_user_id,
                    action=AuditAction.decision_made,
                    resource_type="application",
                    resource_id=str(app_id),
                    details={"decision": app.status.value, "amount": float(app.requested_amount)},
                    description=f"Decision made: {app.status.value} for application {str(app_id)[:8]}",
                    severity="info",
                )
                self.session.add(audit)
                count += 1

        # Audit logs for loans
        for loan_id in self.loan_ids:
            result = await self.session.execute(
                __import__("sqlalchemy").select(Loan).where(Loan.id == loan_id)
            )
            loan = result.scalar()
            if loan is None:
                continue

            audit = AuditLog(
                actor_id=self.admin_user_id,
                actor_type="admin",
                admin_user_id=self.admin_user_id,
                action=AuditAction.loan_funded,
                resource_type="loan",
                resource_id=str(loan_id),
                details={"amount": float(loan.loan_amount), "apr": float(loan.apr)},
                description=f"Loan funded: ${float(loan.loan_amount):.2f} at {float(loan.apr):.2f}% APR",
                severity="info",
            )
            self.session.add(audit)
            count += 1

        # Some random audit logs for variety
        for _ in range(50):
            action = random.choice(all_actions)
            audit = AuditLog(
                actor_id=self.admin_user_id,
                actor_type="admin",
                admin_user_id=self.admin_user_id,
                action=action,
                resource_type=random.choice(["application", "loan", "borrower", "document"]),
                resource_id=str(random.choice(self.application_ids if self.application_ids else [uuid.uuid4()])),
                description=f"Seed audit entry: {action.value}",
                severity=random.choice(["info", "info", "info", "warning", "error"]),
                ip_address=f"{random.randint(10, 223)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 254)}",
            )
            self.session.add(audit)
            count += 1

        self.stats["audit_logs"] = count
        await self.session.flush()
        print(f"  ✓ Created {count} audit log entries")

    # ═════════════════════════════════════════════════════════════════════════
    # Compliance Events
    # ═════════════════════════════════════════════════════════════════════════

    async def seed_compliance_events(self) -> None:
        """Create compliance events — adverse actions, ECOA notices, and consent records."""
        count = 0

        # Adverse actions for declined applications
        for app_id in self.application_ids:
            result = await self.session.execute(
                __import__("sqlalchemy").select(Application).where(Application.id == app_id)
            )
            app = result.scalar()
            if app is None or app.status != ApplicationStatus.declined:
                continue

            event = ComplianceEvent(
                application_id=app_id,
                borrower_id=app.borrower_id,
                event_type=ComplianceEventType.adverse_action,
                status=random.choice(["sent", "sent", "acknowledged"]),
                reason_codes=[
                    "DTI_EXCEEDS_MAX",
                    "CREDIT_HISTORY_SHORT",
                    "RECENT_DELINQUENCIES",
                    "INSUFFICIENT_INCOME",
                    "EMPLOYMENT_VERIFICATION_FAILED",
                ][:random.randint(1, 3)],
                reason_description=app.declined_reason or "Risk assessment did not meet minimum criteria",
                action_taken="declined",
                sent_at=random_datetime(2024, 2024),
                sent_via=random.choice(["email", "mail", "portal"]),
                sent_to_address=random.choice(["borrower@email.com", "borrower@outlook.com"]),
                delivery_status=random.choice(["delivered", "delivered", "delivered", "pending"]),
                delivered_at=random_datetime(2024, 2024) if random.random() > 0.2 else None,
                acknowledged_at=random_datetime(2024, 2024) if random.random() > 0.6 else None,
            )
            self.session.add(event)
            count += 1

        # ECOA notices for all funded loans
        for loan_id in self.loan_ids:
            result = await self.session.execute(
                __import__("sqlalchemy").select(Loan).where(Loan.id == loan_id)
            )
            loan = result.scalar()
            if loan is None:
                continue

            event = ComplianceEvent(
                application_id=loan.application_id,
                borrower_id=loan.borrower_id,
                event_type=ComplianceEventType.ecoa_notice,
                status="sent",
                reason_codes=None,
                reason_description=f"ECOA notice: Loan approved for ${float(loan.loan_amount):.2f} at {float(loan.apr):.2f}% APR",
                action_taken="approved",
                sent_at=loan.origination_date and datetime.combine(loan.origination_date, datetime.min.time(), tzinfo=timezone.utc),
                sent_via="portal",
                sent_to_address="borrower@email.com",
                delivery_status="delivered",
                delivered_at=loan.origination_date and datetime.combine(loan.origination_date, datetime.min.time(), tzinfo=timezone.utc),
            )
            self.session.add(event)
            count += 1

        # TILA disclosures for funded loans
        for loan_id in self.loan_ids:
            if random.random() > 0.3:  # Not all loans have full TILA in seed
                continue
            result = await self.session.execute(
                __import__("sqlalchemy").select(Loan).where(Loan.id == loan_id)
            )
            loan = result.scalar()
            if loan is None:
                continue

            event = ComplianceEvent(
                application_id=loan.application_id,
                borrower_id=loan.borrower_id,
                event_type=ComplianceEventType.tila_disclosure,
                status="sent",
                reason_description=f"TILA disclosure: {float(loan.apr):.2f}% APR, ${float(loan.monthly_payment):.2f}/month",
                action_taken="approved",
                sent_at=random_datetime(2024, 2024),
                sent_via="portal",
                delivery_status="delivered",
            )
            self.session.add(event)
            count += 1

        # Consent records for credit pulls
        for _ in range(30):
            event = ComplianceEvent(
                application_id=random.choice(self.application_ids),
                borrower_id=random.choice(self.borrower_ids),
                event_type=ComplianceEventType.fcra_dispute,
                status=random.choice(["pending", "resolved"]),
                reason_description="Consumer dispute regarding credit report accuracy",
                action_taken=None,
                sent_at=random_datetime(2024, 2024) if random.random() > 0.5 else None,
                acknowledged_at=random_datetime(2024, 2024) if random.random() > 0.7 else None,
                dispute_filed=random.random() > 0.5,
                dispute_resolved_at=random_datetime(2024, 2024) if random.random() > 0.6 else None,
            )
            self.session.add(event)
            count += 1

        self.stats["compliance_events"] = count
        await self.session.flush()
        print(f"  ✓ Created {count} compliance events")

    # ═════════════════════════════════════════════════════════════════════════
    # Run All
    # ═════════════════════════════════════════════════════════════════════════

    async def run(self) -> dict[str, int]:
        """Execute all seed phases in dependency order."""
        print(f"\n{'═' * 60}")
        print(f"  OrangeFi Seed Script")
        print(f"{'═' * 60}\n")

        await self.seed_admin()
        await self.seed_borrowers()
        await self.seed_plaid_connections()
        await self.seed_applications()
        await self.seed_underwriting_results()
        await self.seed_credit_pulls()
        await self.seed_documents()
        await self.seed_loans_and_payments()
        await self.seed_audit_logs()
        await self.seed_compliance_events()

        await self.session.commit()

        print(f"\n{'─' * 60}")
        print(f"  Seeding Complete!")
        print(f"{'─' * 60}")
        print(f"  Borrowers:          {self.stats['borrowers']}")
        print(f"  Plaid Connections:  {self.stats['plaid_connections']}")
        print(f"  Applications:       {self.stats['applications']}")
        print(f"  Underwriting Rslts: {self.stats['underwriting_results']}")
        print(f"  Credit Pulls:       {self.stats['credit_pulls']}")
        print(f"  Documents:          {self.stats['documents']}")
        print(f"  Loans:              {self.stats['loans']}")
        print(f"  Payment Records:    {self.stats['payments']}")
        print(f"  Audit Logs:         {self.stats['audit_logs']}")
        print(f"  Compliance Events:  {self.stats['compliance_events']}")
        print(f"{'─' * 60}")
        print(f"  Admin:              admin@orangefi.com / Admin123!")
        print(f"{'─' * 60}\n")

        return self.stats


# ═══════════════════════════════════════════════════════════════════════════════
# Truncate
# ═══════════════════════════════════════════════════════════════════════════════

TRUNCATE_ORDER = [
    "compliance_events",
    "audit_logs",
    "payments",
    "loans",
    "underwriting_results",
    "credit_pulls",
    "documents",
    "plaid_connections",
    "applications",
    "borrowers",
    "admin_users",
]


async def truncate_all(session: AsyncSession) -> None:
    """Truncate all OrangeFi tables in dependency order."""
    print("  Truncating existing data...")
    for table in TRUNCATE_ORDER:
        await session.execute(text(f"TRUNCATE TABLE {table} CASCADE"))
    await session.commit()
    print("  ✓ All tables truncated\n")


# ═══════════════════════════════════════════════════════════════════════════════
# CLI Entry Point
# ═══════════════════════════════════════════════════════════════════════════════

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="OrangeFi Seed Script — Generate synthetic development data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/seed.py                          # default: 50 borrowers, 120 apps, 30 loans
  python scripts/seed.py --count 100              # 100 borrowers
  python scripts/seed.py --applications 200       # 200 applications
  python scripts/seed.py --truncate               # wipe all data first
  python scripts/seed.py --loans 50               # 50 funded loans
        """,
    )
    parser.add_argument(
        "--count", "-c",
        type=int,
        default=50,
        help="Number of borrowers to create (default: 50)",
    )
    parser.add_argument(
        "--applications", "-a",
        type=int,
        default=120,
        help="Number of loan applications to create (default: 120)",
    )
    parser.add_argument(
        "--loans", "-l",
        type=int,
        default=30,
        help="Number of funded loans to create (default: 30)",
    )
    parser.add_argument(
        "--payment-months", "-p",
        type=int,
        default=6,
        help="Months of payment history per loan (default: 6)",
    )
    parser.add_argument(
        "--truncate", "-t",
        action="store_true",
        help="Truncate all tables before seeding",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print plan without executing",
    )
    return parser.parse_args()


async def main() -> None:
    args = parse_args()

    # ── Database Connection ──
    db_url = os.environ.get(
        "DATABASE_URL",
        "postgresql+asyncpg://orangefi:orangefi@localhost:5432/orangefi",
    )

    engine = create_async_engine(db_url, echo=False, pool_size=5)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    print(f"  Database: {db_url.split('@')[1] if '@' in db_url else db_url}")
    print(f"  Environment: {os.environ.get('ENVIRONMENT', 'development')}")

    if args.dry_run:
        print(f"\n{'─' * 50}")
        print(f"  DRY RUN — would create:")
        print(f"    - {args.count} borrowers")
        print(f"    - {args.applications} applications")
        print(f"    - {args.loans} loans")
        print(f"    - {args.payment_months} months payment history per loan")
        if args.truncate:
            print(f"    - Truncate all tables first")
        print(f"{'─' * 50}\n")
        return

    async with session_factory() as session:
        if args.truncate:
            await truncate_all(session)

        seeder = OrangeFiSeeder(
            session,
            borrower_count=args.count,
            application_count=args.applications,
            loan_count=args.loans,
            payment_months=args.payment_months,
        )
        await seeder.run()

    await engine.dispose()
    print("  Database connection closed.\n")


if __name__ == "__main__":
    asyncio.run(main())
