'use client';

import { cn } from '@/lib/utils';
import { Dna } from 'lucide-react';

interface LoadingProps {
  size?: 'sm' | 'md' | 'lg';
  text?: string;
  fullScreen?: boolean;
}

export function Loading({ size = 'md', text, fullScreen = false }: LoadingProps) {
  const sizes = {
    sm: 'w-6 h-6',
    md: 'w-10 h-10',
    lg: 'w-16 h-16',
  };

  const content = (
    <div className="flex flex-col items-center gap-4">
      <div className={cn('relative', sizes[size])}>
        <Dna className={cn('animate-spin text-primary-400', sizes[size])} />
      </div>
      {text && (
        <p className="text-white/60 text-sm animate-pulse">{text}</p>
      )}
    </div>
  );

  if (fullScreen) {
    return (
      <div className="fixed inset-0 bg-slate-900/80 backdrop-blur-sm flex items-center justify-center z-50">
        {content}
      </div>
    );
  }

  return content;
}

export function LoadingSpinner({ className }: { className?: string }) {
  return (
    <div
      className={cn(
        'w-5 h-5 border-2 border-white/20 border-t-primary-500 rounded-full animate-spin',
        className
      )}
    />
  );
}

export function LoadingSkeleton({ className }: { className?: string }) {
  return (
    <div
      className={cn(
        'bg-white/10 rounded-lg animate-pulse',
        className
      )}
    />
  );
}

