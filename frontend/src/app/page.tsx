'use client';

import Link from 'next/link';
import { 
  Dna, 
  Upload, 
  Database, 
  Activity, 
  MessageSquare, 
  ChevronRight,
  Sparkles,
  Shield,
  Zap,
  Globe
} from 'lucide-react';
import { Card, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';

const stats = [
  { value: '11', label: 'Populations' },
  { value: '29', label: 'SNP Variants' },
  { value: '95%', label: 'Accuracy' },
  { value: '1000+', label: 'Analyses' },
];

const features = [
  {
    icon: Upload,
    title: 'Easy Upload',
    description: 'Upload your genetic data in CSV or VCF format. We support multiple file types.',
    href: '/upload',
    color: 'from-blue-500 to-cyan-500',
  },
  {
    icon: Database,
    title: 'SNP Database',
    description: 'Explore our comprehensive database of genetic variants and their associations.',
    href: '/snp-database',
    color: 'from-purple-500 to-pink-500',
  },
  {
    icon: Activity,
    title: 'Risk Calculator',
    description: 'Calculate genetic risk scores for various health conditions.',
    href: '/risk-calculator',
    color: 'from-orange-500 to-red-500',
  },
  {
    icon: MessageSquare,
    title: 'AI Assistant',
    description: 'Chat with our AI to get personalized insights about your genetic data.',
    href: '/chat',
    color: 'from-green-500 to-emerald-500',
  },
];

const benefits = [
  {
    icon: Sparkles,
    title: 'AI-Powered Analysis',
    description: 'State-of-the-art machine learning models trained on diverse genetic datasets.',
  },
  {
    icon: Shield,
    title: 'Privacy First',
    description: 'Your genetic data never leaves your browser. All processing happens locally.',
  },
  {
    icon: Zap,
    title: 'Instant Results',
    description: 'Get ancestry predictions and health insights in seconds.',
  },
  {
    icon: Globe,
    title: 'Global Coverage',
    description: 'Supporting 11 populations from around the world.',
  },
];

export default function HomePage() {
  return (
    <div className="min-h-screen">
      {/* Hero Section */}
      <section className="relative py-20 overflow-hidden">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <div className="animate-fade-in">
              <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary-500/20 text-primary-300 text-sm font-medium mb-6">
                <Sparkles className="w-4 h-4" />
                AI-Powered Genetic Analysis
              </div>
              
              <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold text-white mb-6 leading-tight">
                Unlock the Secrets of Your{' '}
                <span className="text-gradient">DNA</span>
              </h1>
              
              <p className="text-lg text-white/60 mb-8 max-w-lg">
                Advanced machine learning algorithms analyze genetic markers to predict ancestry, 
                biological traits, and provide insights into your unique genetic makeup.
              </p>
              
              <div className="flex flex-wrap gap-4">
                <Link href="/upload">
                  <Button size="lg" icon={<Upload className="w-5 h-5" />}>
                    Get Started
                  </Button>
                </Link>
                <Link href="/dashboard">
                  <Button variant="secondary" size="lg">
                    View Dashboard
                    <ChevronRight className="w-5 h-5" />
                  </Button>
                </Link>
              </div>
            </div>
            
            {/* DNA Helix Animation */}
            <div className="hidden lg:flex items-center justify-center animate-float">
              <div className="relative">
                <div className="absolute inset-0 bg-gradient-to-r from-primary-500/30 to-accent-500/30 blur-3xl rounded-full" />
                <Dna className="w-64 h-64 text-white/20 animate-spin-slow" />
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {stats.map((stat, index) => (
              <Card key={index} className="text-center p-6">
                <div className="text-4xl font-bold text-gradient mb-2">
                  {stat.value}
                </div>
                <div className="text-sm text-white/60 uppercase tracking-wider">
                  {stat.label}
                </div>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4">
              Powerful Features
            </h2>
            <p className="text-white/60 max-w-2xl mx-auto">
              Everything you need to explore and understand your genetic data
            </p>
          </div>
          
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {features.map((feature, index) => {
              const Icon = feature.icon;
              return (
                <Link key={index} href={feature.href}>
                  <Card hover className="h-full p-6">
                    <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${feature.color} bg-opacity-20 flex items-center justify-center mb-4`}>
                      <Icon className="w-6 h-6 text-white" />
                    </div>
                    <h3 className="text-lg font-semibold text-white mb-2">
                      {feature.title}
                    </h3>
                    <p className="text-sm text-white/60">
                      {feature.description}
                    </p>
                  </Card>
                </Link>
              );
            })}
          </div>
        </div>
      </section>

      {/* Benefits Section */}
      <section className="py-20 bg-white/5">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid lg:grid-cols-2 gap-16 items-center">
            <div>
              <h2 className="text-3xl sm:text-4xl font-bold text-white mb-6">
                Why Choose <span className="text-gradient">GenovaAI</span>?
              </h2>
              <p className="text-white/60 mb-8">
                Our platform combines cutting-edge AI technology with a deep understanding 
                of human genetics to deliver accurate, actionable insights.
              </p>
              
              <div className="space-y-6">
                {benefits.map((benefit, index) => {
                  const Icon = benefit.icon;
                  return (
                    <div key={index} className="flex gap-4">
                      <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-primary-500/20 to-accent-500/20 flex items-center justify-center shrink-0">
                        <Icon className="w-6 h-6 text-primary-400" />
                      </div>
                      <div>
                        <h3 className="text-lg font-semibold text-white mb-1">
                          {benefit.title}
                        </h3>
                        <p className="text-sm text-white/60">
                          {benefit.description}
                        </p>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
            
            <div className="relative">
              <Card className="p-8">
                <CardContent className="space-y-6 p-0">
                  <div className="text-center">
                    <div className="w-20 h-20 rounded-full bg-gradient-to-br from-primary-500 to-accent-500 flex items-center justify-center mx-auto mb-4">
                      <Dna className="w-10 h-10 text-white" />
                    </div>
                    <h3 className="text-xl font-semibold text-white mb-2">
                      Ready to explore?
                    </h3>
                    <p className="text-white/60 text-sm mb-6">
                      Upload your genetic data and get instant insights
                    </p>
                    <Link href="/upload">
                      <Button className="w-full">
                        Start Analysis
                        <ChevronRight className="w-5 h-5" />
                      </Button>
                    </Link>
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4">
            Start Your Genetic Journey Today
          </h2>
          <p className="text-white/60 mb-8 max-w-2xl mx-auto">
            Join thousands of users who have discovered insights about their ancestry 
            and health through our AI-powered analysis.
          </p>
          <div className="flex flex-wrap justify-center gap-4">
            <Link href="/auth/register">
              <Button size="lg">
                Create Free Account
              </Button>
            </Link>
            <Link href="/samples">
              <Button variant="secondary" size="lg">
                Try with Sample Data
              </Button>
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
