import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import { Navbar } from '@/components/layout/Navbar';
import { Footer } from '@/components/layout/Footer';

const inter = Inter({
  variable: '--font-inter',
  subsets: ['latin'],
});

export const metadata: Metadata = {
  title: 'GenovaAI - Advanced DNA Genetic Prediction System',
  description: 'AI-powered genetic analysis platform for ancestry, traits, and health insights from your DNA.',
  keywords: ['DNA', 'genetic analysis', 'ancestry', 'SNP', 'health', 'AI', 'machine learning'],
  authors: [{ name: 'GenovaAI Team' }],
  themeColor: '#6366f1',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body
        className={`${inter.variable} font-sans antialiased min-h-screen flex flex-col`}
      >
        {/* Animated background */}
        <div className="animated-bg" />
        
        {/* Navigation */}
        <Navbar />
        
        {/* Main content with padding for fixed navbar */}
        <main className="flex-1 pt-20">
          {children}
        </main>
        
        {/* Footer */}
        <Footer />
      </body>
    </html>
  );
}
