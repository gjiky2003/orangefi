import React from 'react';
import Link from 'next/link';
import { Sparkles } from 'lucide-react';

export default function Footer() {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="bg-gray-900 text-gray-300">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          {/* Brand */}
          <div className="md:col-span-1">
            <Link href="/" className="flex items-center gap-2 mb-3">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-orange-500 to-orange-700 flex items-center justify-center">
                <span className="text-white font-bold text-sm">O</span>
              </div>
              <span className="text-xl font-bold text-white">
                Orange<span className="text-orange-500">Fi</span>
              </span>
            </Link>
            <p className="text-sm text-gray-400 leading-relaxed">
              Lower your rates, consolidate debt, and save money with AI-powered lending.
            </p>
          </div>

          {/* Quick Links */}
          <div>
            <h3 className="text-white font-semibold mb-3 text-sm uppercase tracking-wider">Quick Links</h3>
            <ul className="space-y-2">
              <li><Link href="/" className="text-sm hover:text-orange-400 transition-colors">Home</Link></li>
              <li><Link href="/pre-qualify" className="text-sm hover:text-orange-400 transition-colors">Check Your Rate</Link></li>
              <li><Link href="/register" className="text-sm hover:text-orange-400 transition-colors">Get Started</Link></li>
              <li><Link href="/login" className="text-sm hover:text-orange-400 transition-colors">Sign In</Link></li>
            </ul>
          </div>

          {/* Company */}
          <div>
            <h3 className="text-white font-semibold mb-3 text-sm uppercase tracking-wider">Company</h3>
            <ul className="space-y-2">
              <li><Link href="/about" className="text-sm hover:text-orange-400 transition-colors">About Us</Link></li>
              <li><span className="text-sm text-gray-500">Careers</span></li>
              <li><span className="text-sm text-gray-500">Blog</span></li>
              <li><span className="text-sm text-gray-500">Press</span></li>
            </ul>
          </div>

          {/* Legal */}
          <div>
            <h3 className="text-white font-semibold mb-3 text-sm uppercase tracking-wider">Legal</h3>
            <ul className="space-y-2">
              <li><span className="text-sm text-gray-500">Terms of Service</span></li>
              <li><span className="text-sm text-gray-500">Privacy Policy</span></li>
              <li><span className="text-sm text-gray-500">Accessibility</span></li>
              <li><span className="text-sm text-gray-500">Disclosures</span></li>
            </ul>
          </div>
        </div>

        <div className="mt-10 pt-8 border-t border-gray-800 flex flex-col sm:flex-row items-center justify-between gap-4">
          <p className="text-sm text-gray-500">
            &copy; {currentYear} OrangeFi. All rights reserved.
          </p>
          <div className="flex items-center gap-2 text-sm text-gray-500">
            <Sparkles className="w-4 h-4 text-orange-400" />
            <span>Made with AI</span>
          </div>
        </div>
      </div>
    </footer>
  );
}
