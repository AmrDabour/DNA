'use client';

import Link from 'next/link';
import { useState, useEffect } from 'react';
import { Dna, Github, Mail, Send, Shield, Lock, Award, Linkedin, MessageCircle } from 'lucide-react';
import { cn } from '@/lib/utils';

const teamMembers = [
  { name: 'Amr Dabour', initials: 'AD', linkedin: 'https://www.linkedin.com/in/amrdabour/' },
  { name: 'Abdalla Sheta', initials: 'AS', linkedin: 'https://www.linkedin.com/in/abdallasheta' },
  { name: 'Yousef Mohamed', initials: 'YM', linkedin: 'https://www.linkedin.com/in/yousef-mohamed-505b92278/' },
  { name: 'Ahmed Mohammed', initials: 'AM', linkedin: 'https://www.linkedin.com/in/ahmed-mohammed-478a15357' },
  { name: 'Ahmed Magdy', initials: 'AM', linkedin: 'https://www.linkedin.com/in/ahmedmagdyt122' },
];

export function Footer() {
  const [newsletterEmail, setNewsletterEmail] = useState('');
  const [subscribed, setSubscribed] = useState(false);

  const subscribeNewsletter = (e: React.FormEvent) => {
    e.preventDefault();
    if (newsletterEmail) {
      setSubscribed(true);
      setNewsletterEmail('');
      setTimeout(() => setSubscribed(false), 3000);
    }
  };

  useEffect(() => {
    // Create footer particles
    const container = document.getElementById('footer-particles');
    if (!container) return;

    const colors = ['#6366f1', '#8b5cf6', '#06b6d4', '#10b981'];
    
    for (let i = 0; i < 15; i++) {
      const particle = document.createElement('div');
      particle.className = 'footer-particle';
      particle.style.left = Math.random() * 100 + '%';
      particle.style.animationDelay = Math.random() * 5 + 's';
      particle.style.animationDuration = (3 + Math.random() * 4) + 's';
      particle.style.background = colors[Math.floor(Math.random() * colors.length)];
      particle.style.width = (3 + Math.random() * 4) + 'px';
      particle.style.height = particle.style.width;
      container.appendChild(particle);
    }

    return () => {
      container.innerHTML = '';
    };
  }, []);

  return (
    <footer className="relative border-t border-white/10 bg-slate-900/50 backdrop-blur-sm mt-auto overflow-hidden">
      {/* Footer Glow Effect */}
      <div className="footer-glow absolute -top-48 left-1/2 -translate-x-1/2 w-[600px] h-[400px] bg-gradient-radial from-primary-500/15 to-transparent pointer-events-none animate-footer-glow-pulse"></div>
      
      {/* Footer Particles */}
      <div id="footer-particles" className="footer-particles absolute inset-0 pointer-events-none"></div>

      <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8 pb-8">
          {/* Brand Column */}
          <div className="lg:col-span-1">
            <Link href="/" className="flex items-center gap-3 mb-4 group">
              <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-primary-500 to-accent-500 flex items-center justify-center shadow-lg shadow-primary-500/25 group-hover:shadow-primary-500/40 transition-all group-hover:rotate-12">
                <Dna className="w-6 h-6 text-white animate-spin-slow" />
              </div>
              <span className="text-xl font-bold text-white">
                Genova<span className="text-gradient"> AI</span>
              </span>
            </Link>
            <p className="text-white/60 text-sm mb-6 leading-relaxed">
              Unlocking the secrets of your DNA with advanced AI-powered genetic analysis. 
              Discover your ancestry, traits, and health insights.
            </p>
            <div className="flex gap-3">
              {/* LinkedIn Team Popup */}
              <div className="linkedin-team-wrapper relative">
                <a
                  href="#"
                  onClick={(e) => e.preventDefault()}
                  className="social-link linkedin-trigger relative w-11 h-11 rounded-lg bg-blue-600/25 border border-blue-500/50 flex items-center justify-center text-blue-400 hover:bg-blue-600 hover:text-white transition-all group"
                  title="Our Team on LinkedIn"
                >
                  <Linkedin className="w-5 h-5" />
                  <span className="team-badge absolute -top-2 -right-2 w-5 h-5 bg-gradient-to-br from-rose-500 to-pink-500 rounded-full flex items-center justify-center text-xs font-bold text-white border-2 border-slate-900">
                    5
                  </span>
                </a>
                <div className="linkedin-team-popup absolute bottom-full left-0 mb-2 w-64 bg-slate-900/98 backdrop-blur-xl border border-blue-500/30 rounded-xl shadow-2xl opacity-0 invisible transition-all duration-500 transform translate-y-2 scale-95 group-hover:opacity-100 group-hover:visible group-hover:translate-y-0 group-hover:scale-100 z-50">
                  <div className="popup-header bg-gradient-to-r from-primary-500 via-accent-500 to-violet-500 p-3 flex items-center gap-2 text-white font-bold text-sm rounded-t-xl">
                    <Linkedin className="w-5 h-5" />
                    <span>Meet Our Team</span>
                  </div>
                  <div className="popup-members p-2 max-h-72 overflow-y-auto">
                    {teamMembers.map((member, index) => (
                      <a
                        key={index}
                        href={member.linkedin}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="team-member flex items-center gap-3 p-2 rounded-lg hover:bg-primary-500/10 transition-all group/member"
                      >
                        <div className="member-avatar w-9 h-9 rounded-full bg-gradient-to-br from-primary-500 to-accent-500 flex items-center justify-center text-white text-xs font-bold">
                          {member.initials}
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="member-name text-white text-sm font-semibold truncate">
                            {member.name}
                          </div>
                          <div className="member-connect text-xs text-white/40 group-hover/member:text-primary-400 transition-colors flex items-center gap-1">
                            Connect
                            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                            </svg>
                          </div>
                        </div>
                      </a>
                    ))}
                  </div>
                  <div className="popup-footer p-3 bg-slate-900/50 border-t border-white/10 text-center">
                    <span className="text-xs text-white/60 flex items-center justify-center gap-2">
                      <Dna className="w-4 h-4 text-primary-400" />
                      Built with passion by our team
                    </span>
                  </div>
                </div>
              </div>

              <a
                href="https://github.com/AmrDabour"
                target="_blank"
                rel="noopener noreferrer"
                className="social-link w-11 h-11 rounded-lg bg-white/5 border border-white/10 flex items-center justify-center text-white/40 hover:text-white hover:bg-white/10 hover:border-white/20 transition-all"
                title="GitHub"
              >
                <Github className="w-5 h-5" />
              </a>
              <a
                href="https://www.facebook.com/amr.dabour.3/"
                target="_blank"
                rel="noopener noreferrer"
                className="social-link w-11 h-11 rounded-lg bg-white/5 border border-white/10 flex items-center justify-center text-white/40 hover:text-white hover:bg-white/10 hover:border-white/20 transition-all"
                title="Facebook"
              >
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/>
                </svg>
              </a>
              <a
                href="https://discord.gg/rWrzgzYe"
                target="_blank"
                rel="noopener noreferrer"
                className="social-link w-11 h-11 rounded-lg bg-white/5 border border-white/10 flex items-center justify-center text-white/40 hover:text-white hover:bg-white/10 hover:border-white/20 transition-all"
                title="Discord"
              >
                <MessageCircle className="w-5 h-5" />
              </a>
            </div>
          </div>

          {/* Quick Links */}
          <div>
            <h5 className="widget-title text-white font-bold mb-4 flex items-center gap-2">
              <span className="w-8 h-8 rounded-lg bg-primary-500/20 flex items-center justify-center">
                <svg className="w-4 h-4 text-primary-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
                </svg>
              </span>
              Quick Links
            </h5>
            <ul className="space-y-2">
              {[
                { href: '/', label: 'Home' },
                { href: '/dashboard', label: 'Dashboard' },
                { href: '/upload', label: 'Upload DNA' },
                { href: '/ancestry-map', label: 'Ancestry Map' },
              ].map((link) => (
                <li key={link.href}>
                  <Link
                    href={link.href}
                    className="text-white/60 hover:text-white transition-colors text-sm flex items-center gap-2 group"
                  >
                    <svg className="w-3 h-3 opacity-0 group-hover:opacity-100 transition-opacity text-primary-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Analysis Tools */}
          <div>
            <h5 className="widget-title text-white font-bold mb-4 flex items-center gap-2">
              <span className="w-8 h-8 rounded-lg bg-primary-500/20 flex items-center justify-center">
                <svg className="w-4 h-4 text-primary-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
                </svg>
              </span>
              Analysis
            </h5>
            <ul className="space-y-2">
              {[
                { href: '/snp-query', label: 'SNP Query' },
                { href: '/snp-database', label: 'SNP Database' },
                { href: '/risk-calculator', label: 'Risk Calculator' },
                { href: '/chat', label: 'AI Assistant' },
              ].map((link) => (
                <li key={link.href}>
                  <Link
                    href={link.href}
                    className="text-white/60 hover:text-white transition-colors text-sm flex items-center gap-2 group"
                  >
                    <svg className="w-3 h-3 opacity-0 group-hover:opacity-100 transition-opacity text-primary-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Newsletter / Contact */}
          <div>
            <h5 className="widget-title text-white font-bold mb-4 flex items-center gap-2">
              <span className="w-8 h-8 rounded-lg bg-primary-500/20 flex items-center justify-center">
                <Mail className="w-4 h-4 text-primary-400" />
              </span>
              Stay Updated
            </h5>
            <p className="text-white/60 text-sm mb-4">
              Subscribe to receive updates on new features and genetic research insights.
            </p>
            <form onSubmit={subscribeNewsletter} className="mb-4">
              <div className="flex gap-2">
                <input
                  type="email"
                  placeholder="Enter your email"
                  value={newsletterEmail}
                  onChange={(e) => setNewsletterEmail(e.target.value)}
                  className="flex-1 px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-white/40 focus:outline-none focus:border-primary-500 focus:ring-2 focus:ring-primary-500/20 transition-all"
                  required
                />
                <button
                  type="submit"
                  className="px-4 py-2 bg-gradient-to-r from-primary-500 to-accent-500 text-white rounded-lg hover:shadow-lg hover:shadow-primary-500/25 transition-all"
                >
                  <Send className="w-4 h-4" />
                </button>
              </div>
              {subscribed && (
                <p className="text-green-400 text-xs mt-2">Thanks for subscribing!</p>
              )}
            </form>
            <div className="flex flex-wrap gap-2">
              <span className="badge-item inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-primary-500/10 border border-primary-500/20 text-primary-300 text-xs font-medium">
                <Shield className="w-3 h-3" />
                Secure
              </span>
              <span className="badge-item inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-primary-500/10 border border-primary-500/20 text-primary-300 text-xs font-medium">
                <Lock className="w-3 h-3" />
                Private
              </span>
              <span className="badge-item inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-primary-500/10 border border-primary-500/20 text-primary-300 text-xs font-medium">
                <Award className="w-3 h-3" />
                Trusted
              </span>
            </div>
          </div>
        </div>

        {/* DNA Separator */}
        <div className="dna-separator flex justify-center py-8">
          <div className="dna-strand flex gap-2">
            {Array.from({ length: 10 }).map((_, i) => (
              <span
                key={i}
                className={cn(
                  'w-2 h-2 rounded-full',
                  i % 2 === 0 ? 'bg-primary-500' : 'bg-accent-500',
                  i % 4 === 0 && 'bg-tertiary-500'
                )}
                style={{
                  animation: `strandPulse 2s ease-in-out infinite`,
                  animationDelay: `${i * 0.1}s`,
                }}
              />
            ))}
          </div>
        </div>

        {/* Bottom Footer */}
        <div className="footer-bottom border-t border-white/10 pt-6 flex flex-col md:flex-row justify-between items-center gap-4">
          <p className="copyright text-white/60 text-sm text-center md:text-left">
            &copy; {new Date().getFullYear()} <strong className="text-gradient">Genova AI</strong>. 
            All rights reserved. Built with <span className="text-red-400 animate-pulse">♥</span> for science.
          </p>
          <div className="footer-bottom-links flex gap-6">
            <Link href="/privacy-policy" className="text-white/60 hover:text-white transition-colors text-sm relative group">
              Privacy Policy
              <span className="absolute bottom-0 left-0 w-0 h-0.5 bg-gradient-primary group-hover:w-full transition-all"></span>
            </Link>
            <Link href="/terms-of-use" className="text-white/60 hover:text-white transition-colors text-sm relative group">
              Terms of Use
              <span className="absolute bottom-0 left-0 w-0 h-0.5 bg-gradient-primary group-hover:w-full transition-all"></span>
            </Link>
            <Link href="/contact" className="text-white/60 hover:text-white transition-colors text-sm relative group">
              Contact
              <span className="absolute bottom-0 left-0 w-0 h-0.5 bg-gradient-primary group-hover:w-full transition-all"></span>
            </Link>
          </div>
        </div>
      </div>
    </footer>
  );
}
