import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import { AuthProvider } from '@/src/lib/auth-context';
import Navbar from '@/src/components/Navbar';
import Footer from '@/src/components/Footer';

const inter = Inter({ subsets: ['latin'], display: 'swap' });

export const metadata: Metadata = {
  title: 'OrangeFi — Lower Your Rate, Consolidate Debt, Save Money',
  description:
    'OrangeFi uses AI-powered underwriting to offer fast, fair personal loans for debt consolidation and credit card refinancing. Check your rate in minutes.',
  keywords: [
    'personal loans',
    'debt consolidation',
    'credit card refinancing',
    'AI underwriting',
    'low APR loans',
    'OrangeFi',
  ],
  openGraph: {
    title: 'OrangeFi — Smart Lending, Powered by AI',
    description: 'Lower your credit card rate. Consolidate debt. Save money with OrangeFi.',
    type: 'website',
    siteName: 'OrangeFi',
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={inter.className}>
      <body className="min-h-screen flex flex-col">
        <AuthProvider>
          <Navbar />
          <main className="flex-1">{children}</main>
          <Footer />
        </AuthProvider>
      </body>
    </html>
  );
}
