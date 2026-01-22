'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useState, useEffect } from 'react';
import { 
  Home, 
  Upload, 
  Database, 
  Activity, 
  MessageSquare, 
  History,
  Menu,
  X,
  LogIn,
  LogOut,
  User,
  Dna,
  MapPin,
  BarChart3
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { ThemeToggle } from '@/components/ui/ThemeToggle';
import { NotificationDropdown } from '@/components/ui/NotificationDropdown';

const navLinks = [
  { href: '/', label: 'Home', icon: Home },
  { href: '/dashboard', label: 'Dashboard', icon: BarChart3 },
  { href: '/ancestry-map', label: 'Ancestry Map', icon: MapPin },
  { href: '/upload', label: 'Upload', icon: Upload },
  { href: '/snp-query', label: 'SNP Query', icon: Database },
  { href: '/snp-database', label: 'SNP Database', icon: Database },
  { href: '/risk-calculator', label: 'Risk Calculator', icon: Activity },
  { href: '/chat', label: 'AI Assistant', icon: MessageSquare },
];

interface NavbarProps {
  user?: {
    username: string;
    email: string;
  } | null;
}

export function Navbar({ user }: NavbarProps) {
  const pathname = usePathname();
  const [isOpen, setIsOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);
  const [userMenuOpen, setUserMenuOpen] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 50);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (userMenuOpen) {
        const target = event.target as Node;
        if (!document.querySelector('.user-menu-container')?.contains(target)) {
          setUserMenuOpen(false);
        }
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [userMenuOpen]);

  return (
    <nav
      className={cn(
        'fixed top-0 left-0 right-0 z-50 backdrop-blur-xl border-b transition-all duration-300',
        scrolled
          ? 'bg-slate-900/95 border-white/20 shadow-lg py-2'
          : 'bg-slate-900/80 border-white/10 py-3'
      )}
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-14">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-3 group">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary-500 to-accent-500 flex items-center justify-center shadow-lg shadow-primary-500/25 group-hover:shadow-primary-500/40 transition-all group-hover:scale-105">
              <Dna className="w-6 h-6 text-white animate-spin-slow" />
            </div>
            <span className="text-xl font-bold text-white hidden sm:block">
              Genova<span className="text-gradient"> AI</span>
            </span>
          </Link>

          {/* Desktop Navigation */}
          <div className="hidden lg:flex items-center gap-1 flex-1 justify-center">
            {navLinks.map((link) => {
              const Icon = link.icon;
              const isActive = pathname === link.href;
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  className={cn(
                    'nav-link relative',
                    isActive && 'nav-link-active'
                  )}
                >
                  <Icon className="w-4 h-4" />
                  <span>{link.label}</span>
                  {link.href === '/chat' && (
                    <span className="pulse-dot ml-1"></span>
                  )}
                </Link>
              );
            })}
          </div>

          {/* Right Side Actions */}
          <div className="hidden lg:flex items-center gap-2">
            {/* Notifications */}
            <NotificationDropdown />

            {/* Theme Toggle */}
            <ThemeToggle />

            {/* Auth Buttons / User Menu */}
            {user ? (
              <div className="relative user-menu-container">
                <button
                  onClick={() => setUserMenuOpen(!userMenuOpen)}
                  className="flex items-center gap-2 px-3 py-2 rounded-lg bg-primary-500/20 hover:bg-primary-500/30 border border-primary-500/30 transition-colors text-white text-sm"
                >
                  <div className="w-8 h-8 rounded-full bg-gradient-to-br from-primary-500 to-accent-500 flex items-center justify-center text-white text-xs font-semibold">
                    {user.username.charAt(0).toUpperCase()}
                  </div>
                  <span className="hidden sm:inline">{user.username}</span>
                </button>
                {userMenuOpen && (
                  <div className="absolute right-0 mt-2 w-48 bg-slate-900/95 backdrop-blur-xl border border-white/10 rounded-lg shadow-xl py-2 z-50">
                    <Link
                      href="/profile"
                      onClick={() => setUserMenuOpen(false)}
                      className="block px-4 py-2 text-white/80 hover:bg-white/5 hover:text-white transition-colors flex items-center gap-2"
                    >
                      <User className="w-4 h-4" />
                      Profile
                    </Link>
                    <Link
                      href="/history"
                      onClick={() => setUserMenuOpen(false)}
                      className="block px-4 py-2 text-white/80 hover:bg-white/5 hover:text-white transition-colors flex items-center gap-2"
                    >
                      <History className="w-4 h-4" />
                      My History
                    </Link>
                    <hr className="my-2 border-white/10" />
                    <Link
                      href="/logout"
                      onClick={() => setUserMenuOpen(false)}
                      className="block px-4 py-2 text-red-400 hover:bg-red-500/10 transition-colors flex items-center gap-2"
                    >
                      <LogOut className="w-4 h-4" />
                      Logout
                    </Link>
                  </div>
                )}
              </div>
            ) : (
              <Link href="/auth/login" className="btn-secondary py-2 px-4 text-sm flex items-center gap-2">
                <LogIn className="w-4 h-4" />
                Login
              </Link>
            )}
          </div>

          {/* Mobile Menu Button */}
          <button
            onClick={() => setIsOpen(!isOpen)}
            className="lg:hidden p-2 rounded-lg hover:bg-white/10 transition-colors"
          >
            {isOpen ? (
              <X className="w-6 h-6 text-white" />
            ) : (
              <Menu className="w-6 h-6 text-white" />
            )}
          </button>
        </div>
      </div>

      {/* Mobile Menu */}
      {isOpen && (
        <div className="lg:hidden border-t border-white/10 bg-slate-900/95 backdrop-blur-xl">
          <div className="px-4 py-4 space-y-1">
            {navLinks.map((link) => {
              const Icon = link.icon;
              const isActive = pathname === link.href;
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  onClick={() => setIsOpen(false)}
                  className={cn(
                    'flex items-center gap-3 px-4 py-3 rounded-lg text-white/70 hover:text-white hover:bg-white/5 transition-colors',
                    isActive && 'text-white bg-white/10'
                  )}
                >
                  <Icon className="w-5 h-5" />
                  <span>{link.label}</span>
                  {link.href === '/chat' && (
                    <span className="pulse-dot ml-auto"></span>
                  )}
                </Link>
              );
            })}
            
            <hr className="border-white/10 my-4" />
            
            {/* Mobile Notifications & Theme */}
            <div className="flex items-center gap-2 px-4 py-2">
              <NotificationDropdown />
              <ThemeToggle />
            </div>
            
            <hr className="border-white/10 my-4" />
            
            {user ? (
              <div className="space-y-2">
                <Link
                  href="/profile"
                  onClick={() => setIsOpen(false)}
                  className="flex items-center gap-3 px-4 py-3 rounded-lg text-white/70 hover:text-white hover:bg-white/5"
                >
                  <User className="w-5 h-5" />
                  <span>Profile</span>
                </Link>
                <Link
                  href="/history"
                  onClick={() => setIsOpen(false)}
                  className="flex items-center gap-3 px-4 py-3 rounded-lg text-white/70 hover:text-white hover:bg-white/5"
                >
                  <History className="w-5 h-5" />
                  <span>My History</span>
                </Link>
                <button className="w-full flex items-center gap-3 px-4 py-3 rounded-lg text-red-400 hover:bg-red-500/10">
                  <LogOut className="w-5 h-5" />
                  <span>Logout</span>
                </button>
              </div>
            ) : (
              <div className="flex gap-3">
                <Link href="/auth/login" className="btn-secondary flex-1 text-center py-3">
                  Login
                </Link>
                <Link href="/auth/register" className="btn-primary flex-1 text-center py-3">
                  Register
                </Link>
              </div>
            )}
          </div>
        </div>
      )}
    </nav>
  );
}


