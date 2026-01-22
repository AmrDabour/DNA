import Link from 'next/link';
import { Dna, Github, Twitter, Mail } from 'lucide-react';

export function Footer() {
  return (
    <footer className="border-t border-white/10 bg-slate-900/50 backdrop-blur-sm mt-auto">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          {/* Brand */}
          <div className="col-span-1 md:col-span-2">
            <Link href="/" className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary-500 to-accent-500 flex items-center justify-center">
                <Dna className="w-6 h-6 text-white" />
              </div>
              <span className="text-xl font-bold text-white">
                Genova<span className="text-gradient">AI</span>
              </span>
            </Link>
            <p className="text-white/60 max-w-md">
              Advanced AI-powered genetic analysis platform. Unlock insights from your DNA 
              with cutting-edge machine learning algorithms.
            </p>
            <div className="flex gap-4 mt-6">
              <a href="#" className="text-white/40 hover:text-white transition-colors">
                <Github className="w-5 h-5" />
              </a>
              <a href="#" className="text-white/40 hover:text-white transition-colors">
                <Twitter className="w-5 h-5" />
              </a>
              <a href="#" className="text-white/40 hover:text-white transition-colors">
                <Mail className="w-5 h-5" />
              </a>
            </div>
          </div>

          {/* Quick Links */}
          <div>
            <h3 className="text-white font-semibold mb-4">Quick Links</h3>
            <ul className="space-y-2">
              <li>
                <Link href="/upload" className="text-white/60 hover:text-white transition-colors">
                  Upload Sample
                </Link>
              </li>
              <li>
                <Link href="/snp-database" className="text-white/60 hover:text-white transition-colors">
                  SNP Database
                </Link>
              </li>
              <li>
                <Link href="/risk-calculator" className="text-white/60 hover:text-white transition-colors">
                  Risk Calculator
                </Link>
              </li>
              <li>
                <Link href="/chat" className="text-white/60 hover:text-white transition-colors">
                  AI Assistant
                </Link>
              </li>
            </ul>
          </div>

          {/* Legal */}
          <div>
            <h3 className="text-white font-semibold mb-4">Legal</h3>
            <ul className="space-y-2">
              <li>
                <Link href="/privacy" className="text-white/60 hover:text-white transition-colors">
                  Privacy Policy
                </Link>
              </li>
              <li>
                <Link href="/terms" className="text-white/60 hover:text-white transition-colors">
                  Terms of Service
                </Link>
              </li>
              <li>
                <Link href="/contact" className="text-white/60 hover:text-white transition-colors">
                  Contact Us
                </Link>
              </li>
            </ul>
          </div>
        </div>

        <div className="border-t border-white/10 mt-8 pt-8 flex flex-col md:flex-row justify-between items-center gap-4">
          <p className="text-white/40 text-sm">
            © {new Date().getFullYear()} GenovaAI. All rights reserved.
          </p>
          <p className="text-white/40 text-sm">
            Powered by advanced machine learning
          </p>
        </div>
      </div>
    </footer>
  );
}

