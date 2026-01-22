'use client';

import { cn } from '@/lib/utils';
import { ReactNode } from 'react';

interface BadgeProps {
  children: ReactNode;
  variant?: 'default' | 'primary' | 'success' | 'warning' | 'danger' | 'benign' | 'risk' | 'protective' | 'drug';
  className?: string;
}

export function Badge({ children, variant = 'default', className }: BadgeProps) {
  const variants = {
    default: 'bg-white/10 text-white/80',
    primary: 'bg-primary-500/20 text-primary-300',
    success: 'bg-green-500/20 text-green-300',
    warning: 'bg-yellow-500/20 text-yellow-300',
    danger: 'bg-red-500/20 text-red-300',
    benign: 'bg-blue-500/20 text-blue-300',
    risk: 'bg-red-500/20 text-red-300',
    protective: 'bg-emerald-500/20 text-emerald-300',
    drug: 'bg-purple-500/20 text-purple-300',
  };

  return (
    <span
      className={cn(
        'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium',
        variants[variant],
        className
      )}
    >
      {children}
    </span>
  );
}


