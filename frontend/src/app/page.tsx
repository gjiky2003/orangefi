'use client';

import React, { useState, useMemo } from 'react';
import Link from 'next/link';
import {
  ArrowRight,
  Shield,
  Zap,
  DollarSign,
  CheckCircle,
  ChevronDown,
  Star,
  BarChart3,
  Sparkles,
  PiggyBank,
  FileText,
} from 'lucide-react';
// ── Synthetic testimonials ────────────────────────────────────────────────────

const testimonials = [
  {
    name: 'Sarah M.',
    location: 'Austin, TX',
    text: 'OrangeFi helped me consolidate $18,000 in credit card debt. My APR went from 24% to 9.99%. Saving over $200/month!',
    rating: 5,
    initials: 'SM',
  },
  {
    name: 'James L.',
    location: 'Denver, CO',
    text: 'The whole process took less than 24 hours. Applied online, got approved, and funds were in my account the next morning.',
    rating: 5,
    initials: 'JL',
  },
  {
    name: 'Maria G.',
    location: 'Miami, FL',
    text: 'I was nervous about my credit score, but OrangeFi&apos;s AI underwriting looked at my whole financial picture. Got a fair rate!',
    rating: 5,
    initials: 'MG',
  },
];

// ── FAQ data ──────────────────────────────────────────────────────────────────

const faqs = [
  {
    q: 'How does OrangeFi determine my rate?',
    a: 'Our AI-powered underwriting analyzes multiple factors including your income, credit history, debt-to-income ratio, and employment stability. This gives us a comprehensive view beyond just your credit score.',
  },
  {
    q: 'Will checking my rate hurt my credit score?',
    a: 'No! Our initial rate check uses a soft credit pull that does not affect your credit score. Only when you accept an offer and proceed to final approval will a hard pull occur.',
  },
  {
    q: 'How fast can I get funded?',
    a: 'Most borrowers receive funds within 24 hours of accepting an offer. Once you complete the full application and verification, we can often disburse funds the same business day.',
  },
  {
    q: 'What can I use an OrangeFi loan for?',
    a: 'OrangeFi loans are designed for debt consolidation and credit card refinancing. You can also use them for home improvements, major purchases, medical expenses, or other personal financial needs.',
  },
  {
    q: 'Are there any prepayment penalties?',
    a: 'No. OrangeFi does not charge prepayment penalties. You can pay off your loan early at any time with no additional fees, saving you money on interest.',
  },
  {
    q: 'What if I have questions during the process?',
    a: 'Our support team is available 7 days a week via chat, email, and phone. You can also manage everything through your online dashboard.',
  },
];

// ── Loan Calculator ──────────────────────────────────────────────────────────

function LoanCalculator() {
  const [amount, setAmount] = useState(15000);
  const [months, setMonths] = useState(36);

  const APR = 9.99; // estimated APR for display

  const monthlyPayment = useMemo(() => {
    const monthlyRate = APR / 100 / 12;
    return (
      (amount * monthlyRate * Math.pow(1 + monthlyRate, months)) /
      (Math.pow(1 + monthlyRate, months) - 1)
    );
  }, [amount, months, APR]);

  const totalInterest = monthlyPayment * months - amount;

  return (
    <div className="bg-white rounded-2xl shadow-xl border border-gray-100 p-6 sm:p-8">
      <h3 className="text-lg font-semibold text-gray-900 mb-6">Estimate Your Payment</h3>

      {/* Amount slider */}
      <div className="mb-6">
        <div className="flex justify-between items-center mb-2">
          <label className="text-sm font-medium text-gray-700">Loan Amount</label>
          <span className="text-2xl font-bold text-orange-600">${amount.toLocaleString()}</span>
        </div>
        <input
          type="range"
          min={5000}
          max={35000}
          step={500}
          value={amount}
          onChange={(e) => setAmount(Number(e.target.value))}
          className="w-full"
        />
        <div className="flex justify-between text-xs text-gray-400 mt-1">
          <span>$5,000</span>
          <span>$35,000</span>
        </div>
      </div>

      {/* Term selector */}
      <div className="mb-6">
        <label className="text-sm font-medium text-gray-700 mb-2 block">Term Length</label>
        <div className="grid grid-cols-3 gap-2">
          {[24, 36, 48].map((t) => (
            <button
              key={t}
              onClick={() => setMonths(t)}
              className={`py-2.5 px-4 rounded-lg text-sm font-medium transition-all ${
                months === t
                  ? 'bg-orange-600 text-white shadow-sm'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              {t} mo
            </button>
          ))}
        </div>
      </div>

      {/* Results */}
      <div className="bg-orange-50 rounded-xl p-5 space-y-3">
        <div className="flex justify-between items-center">
          <span className="text-sm text-gray-600">Monthly Payment</span>
          <span className="text-xl font-bold text-gray-900">
            ${Math.round(monthlyPayment).toLocaleString()}/mo
          </span>
        </div>
        <div className="flex justify-between items-center">
          <span className="text-sm text-gray-600">Estimated APR</span>
          <span className="text-sm font-semibold text-orange-600">{APR}% APR</span>
        </div>
        <div className="flex justify-between items-center">
          <span className="text-sm text-gray-600">Total Interest</span>
          <span className="text-sm font-semibold text-gray-700">
            ${Math.round(totalInterest).toLocaleString()}
          </span>
        </div>
      </div>

      <Link
        href="/pre-qualify"
        className="mt-6 w-full flex items-center justify-center gap-2 px-6 py-3.5 bg-orange-600 text-white rounded-xl font-semibold hover:bg-orange-700 transition-colors shadow-sm"
      >
        Check Your Rate
        <ArrowRight className="w-4 h-4" />
      </Link>

      <p className="text-xs text-gray-400 text-center mt-3">
        Checking your rate won&apos;t affect your credit score
      </p>
    </div>
  );
}

// ── How It Works ──────────────────────────────────────────────────────────────

const steps = [
  {
    icon: BarChart3,
    title: 'Check Your Rate',
    description: 'Fill out a quick form. Get your personalized rate in minutes with a soft credit check — no impact to your score.',
    color: 'from-orange-400 to-orange-600',
  },
  {
    icon: FileText,
    title: 'Apply Online',
    description: 'Complete the full application with your details. Our AI analyzes your financial profile in real-time.',
    color: 'from-orange-500 to-orange-700',
  },
  {
    icon: PiggyBank,
    title: 'Get Funded',
    description: 'Accept your offer and funds are deposited into your account — often within 24 hours.',
    color: 'from-orange-600 to-orange-800',
  },
];

// ── Features ──────────────────────────────────────────────────────────────────

const features = [
  {
    icon: Sparkles,
    title: 'AI-Powered Underwriting',
    description: 'Our machine learning model evaluates your full financial picture, not just your credit score.',
  },
  {
    icon: Zap,
    title: 'Fast Funding',
    description: 'Get approved and funded in as little as 24 hours. No paperwork, no hassle.',
  },
  {
    icon: DollarSign,
    title: 'Flexible Payments',
    description: 'Choose terms from 12 to 60 months. No prepayment penalties — pay off early anytime.',
  },
  {
    icon: Shield,
    title: 'No Hidden Fees',
    description: 'Transparent rates, no origination fees on select tiers. What you see is what you get.',
  },
];

// ── FAQ Component ─────────────────────────────────────────────────────────────

function FAQItem({ q, a }: { q: string; a: string }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="border border-gray-200 rounded-xl overflow-hidden">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between px-5 py-4 text-left hover:bg-gray-50 transition-colors"
      >
        <span className="font-medium text-gray-900 pr-4">{q}</span>
        <ChevronDown
          className={`w-5 h-5 text-gray-400 flex-shrink-0 transition-transform ${
            open ? 'rotate-180' : ''
          }`}
        />
      </button>
      {open && (
        <div className="px-5 pb-4 text-sm text-gray-600 leading-relaxed">{a}</div>
      )}
    </div>
  );
}

// ── Testimonial Card ──────────────────────────────────────────────────────────

function TestimonialCard({ name, location, text, rating, initials }: (typeof testimonials)[0]) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm hover:shadow-md transition-shadow">
      <div className="flex items-center gap-1 mb-3">
        {Array.from({ length: rating }).map((_, i) => (
          <Star key={i} className="w-4 h-4 fill-orange-400 text-orange-400" />
        ))}
      </div>
      <p className="text-gray-700 text-sm leading-relaxed mb-4">&ldquo;{text}&rdquo;</p>
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-full bg-orange-100 flex items-center justify-center">
          <span className="text-sm font-semibold text-orange-600">{initials}</span>
        </div>
        <div>
          <p className="text-sm font-semibold text-gray-900">{name}</p>
          <p className="text-xs text-gray-500">{location}</p>
        </div>
      </div>
    </div>
  );
}

// ── Comparison Table ──────────────────────────────────────────────────────────

const comparisonData = [
  { feature: 'Average APR', orangefi: '7.99% – 24.99%', cards: '22.8% avg' },
  { feature: 'Credit Check', orangefi: 'Soft pull to start', cards: 'Hard pull' },
  { feature: 'Funding Speed', orangefi: '24 hours', cards: 'N/A' },
  { feature: 'Prepayment Penalty', orangefi: 'None', cards: 'N/A' },
  { feature: 'Origination Fee', orangefi: '0% – 5%', cards: 'N/A' },
];

// ═══════════════════════════════════════════════════════════════════════════════
// Landing Page
// ═══════════════════════════════════════════════════════════════════════════════

export default function LandingPage() {
  return (
    <div className="overflow-hidden">
      {/* ── Hero Section ──────────────────────────────────────────────────── */}
      <section className="relative bg-gradient-to-br from-orange-50 via-white to-orange-50">
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <div className="absolute -top-40 -right-40 w-96 h-96 bg-orange-200/30 rounded-full blur-3xl" />
          <div className="absolute -bottom-40 -left-40 w-96 h-96 bg-orange-300/20 rounded-full blur-3xl" />
        </div>

        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-16 pb-20 lg:pt-24 lg:pb-28">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            {/* Left: Copy */}
            <div>
              <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-orange-100 text-orange-700 text-sm font-medium mb-6">
                <Sparkles className="w-4 h-4" />
                AI-Powered Lending
              </div>
              <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold text-gray-900 leading-tight mb-6">
                Lower Your Credit Card Rate.
                <br />
                <span className="text-orange-600">Consolidate Debt.</span>
                <br />
                Save Money.
              </h1>
              <p className="text-lg sm:text-xl text-gray-600 mb-8 max-w-lg">
                OrangeFi uses AI to offer fair, personalized rates. Get funded in
                as fast as 24 hours with no hidden fees.
              </p>
              <div className="flex flex-col sm:flex-row gap-4">
                <Link
                  href="/pre-qualify"
                  className="inline-flex items-center justify-center gap-2 px-8 py-4 bg-orange-600 text-white rounded-xl font-semibold text-lg hover:bg-orange-700 transition-colors shadow-lg shadow-orange-200"
                >
                  Check Your Rate
                  <ArrowRight className="w-5 h-5" />
                </Link>
                <Link
                  href="#how-it-works"
                  className="inline-flex items-center justify-center gap-2 px-8 py-4 bg-white text-gray-700 rounded-xl font-semibold text-lg border border-gray-300 hover:border-orange-300 hover:text-orange-600 transition-colors"
                >
                  How It Works
                </Link>
              </div>
              <div className="flex items-center gap-6 mt-8 text-sm text-gray-500">
                <div className="flex items-center gap-1.5">
                  <CheckCircle className="w-4 h-4 text-green-500" />
                  No impact to credit
                </div>
                <div className="flex items-center gap-1.5">
                  <CheckCircle className="w-4 h-4 text-green-500" />
                  <span>24-hour funding</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <CheckCircle className="w-4 h-4 text-green-500" />
                  No prepayment fees
                </div>
              </div>
            </div>

            {/* Right: Calculator */}
            <div className="relative">
              <div className="absolute -inset-4 bg-gradient-to-r from-orange-200 to-orange-100 rounded-3xl blur-xl opacity-60" />
              <div className="relative">
                <LoanCalculator />
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── Comparison Section ────────────────────────────────────────────── */}
      <section className="py-16 bg-white">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-10">
            <h2 className="text-3xl font-bold text-gray-900 mb-3">
              Why Switch to OrangeFi?
            </h2>
            <p className="text-gray-600">
              The average credit card APR is <span className="font-semibold text-red-600">22.8%</span>.
              OrangeFi offers rates as low as <span className="font-semibold text-green-600">7.99% APR</span>.
            </p>
          </div>
          <div className="bg-gray-50 rounded-2xl overflow-hidden border border-gray-200">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-100">
                  <th className="text-left px-6 py-4 font-semibold text-gray-900">Feature</th>
                  <th className="text-left px-6 py-4 font-semibold text-orange-600">OrangeFi</th>
                  <th className="text-left px-6 py-4 font-semibold text-gray-500">Credit Cards</th>
                </tr>
              </thead>
              <tbody>
                {comparisonData.map((row, i) => (
                  <tr key={i} className="border-t border-gray-200">
                    <td className="px-6 py-4 text-gray-700">{row.feature}</td>
                    <td className="px-6 py-4 font-medium text-orange-600">{row.orangefi}</td>
                    <td className="px-6 py-4 text-gray-500">{row.cards}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>

      {/* ── How It Works ──────────────────────────────────────────────────── */}
      <section id="how-it-works" className="py-20 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-14">
            <h2 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-3">
              How It Works
            </h2>
            <p className="text-gray-600 max-w-2xl mx-auto">
              Three simple steps to get the funds you need — no paperwork, no branches, no waiting.
            </p>
          </div>
          <div className="grid md:grid-cols-3 gap-8">
            {steps.map((step, i) => {
              const IconComponent = step.icon;
              return (
                <div key={i} className="relative bg-white rounded-2xl p-8 border border-gray-200 shadow-sm">
                  {/* Step number */}
                  <div className="absolute -top-4 -left-4 w-10 h-10 rounded-xl bg-gradient-to-br from-orange-500 to-orange-700 text-white flex items-center justify-center font-bold shadow-lg">
                    {i + 1}
                  </div>
                  <div
                    className={`w-14 h-14 rounded-xl bg-gradient-to-br ${step.color} flex items-center justify-center mb-5 mt-2`}
                  >
                    <IconComponent className="w-7 h-7 text-white" />
                  </div>
                  <h3 className="text-xl font-semibold text-gray-900 mb-2">{step.title}</h3>
                  <p className="text-gray-600 text-sm leading-relaxed">{step.description}</p>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* ── Features ──────────────────────────────────────────────────────── */}
      <section className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-14">
            <h2 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-3">
              Why Choose OrangeFi?
            </h2>
            <p className="text-gray-600 max-w-2xl mx-auto">
              We combine cutting-edge AI with transparent lending to give you a better borrowing experience.
            </p>
          </div>
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {features.map((feat, i) => {
              const IconComponent = feat.icon;
              return (
                <div key={i} className="bg-white rounded-xl p-6 border border-gray-200 hover:border-orange-200 hover:shadow-md transition-all">
                  <div className="w-12 h-12 rounded-lg bg-orange-100 flex items-center justify-center mb-4">
                    <IconComponent className="w-6 h-6 text-orange-600" />
                  </div>
                  <h3 className="font-semibold text-gray-900 mb-2">{feat.title}</h3>
                  <p className="text-sm text-gray-600 leading-relaxed">{feat.description}</p>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* ── Testimonials ──────────────────────────────────────────────────── */}
      <section className="py-20 bg-orange-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-14">
            <h2 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-3">
              What Our Borrowers Say
            </h2>
            <p className="text-gray-600 max-w-2xl mx-auto">
              Join thousands of satisfied customers who found a better way to borrow.
            </p>
          </div>
          <div className="grid md:grid-cols-3 gap-6">
            {testimonials.map((t, i) => (
              <TestimonialCard key={i} {...t} />
            ))}
          </div>
        </div>
      </section>

      {/* ── FAQ ────────────────────────────────────────────────────────────── */}
      <section className="py-20 bg-white">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-3">
              Frequently Asked Questions
            </h2>
            <p className="text-gray-600">Everything you need to know about OrangeFi.</p>
          </div>
          <div className="space-y-3">
            {faqs.map((faq, i) => (
              <FAQItem key={i} q={faq.q} a={faq.a} />
            ))}
          </div>
        </div>
      </section>

      {/* ── Final CTA ──────────────────────────────────────────────────────── */}
      <section className="py-20 bg-gradient-to-br from-orange-600 to-orange-800">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4">
            Ready to Start Saving?
          </h2>
          <p className="text-lg text-orange-100 mb-8 max-w-2xl mx-auto">
            Join thousands of borrowers who have lowered their rates and simplified their finances with OrangeFi.
          </p>
          <Link
            href="/pre-qualify"
            className="inline-flex items-center gap-2 px-8 py-4 bg-white text-orange-700 rounded-xl font-semibold text-lg hover:bg-orange-50 transition-colors shadow-xl"
          >
            Check Your Rate — It&apos;s Free
            <ArrowRight className="w-5 h-5" />
          </Link>
          <p className="text-orange-200 text-sm mt-4">
            Checking won&apos;t affect your credit score
          </p>
        </div>
      </section>
    </div>
  );
}
