'use client';

import Link from 'next/link';
import { useState, useEffect } from 'react';
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
  Globe,
  MapPin,
  Search,
  FileText,
  CheckCircle,
  AlertCircle,
  User,
  Globe2
} from 'lucide-react';
import { Card, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';

const stats = [
  { value: '11', label: 'Populations' },
  { value: '1M+', label: 'SNP Markers' },
  { value: '97%', label: 'Accuracy' },
  { value: '24/7', label: 'AI Support' },
];

const features = [
  {
    icon: Database,
    title: 'SNP Database',
    description: 'Browse and explore our comprehensive SNP database with detailed genetic variant information and associations.',
    href: '/snp-database',
    color: 'from-purple-500 to-pink-500',
  },
  {
    icon: Activity,
    title: 'Visual Analytics',
    description: 'Interactive visualizations and detailed accuracy statistics for prediction analysis.',
    href: '/visualizations',
    color: 'from-blue-500 to-cyan-500',
  },
  {
    icon: MapPin,
    title: 'Ancestry Map',
    description: 'Explore genetic ancestral populations and their geographic distribution with interactive visualizations.',
    href: '/ancestry-map',
    color: 'from-green-500 to-emerald-500',
  },
  {
    icon: Upload,
    title: 'Upload & Analyze',
    description: 'Upload your own SNP data files and get instant predictions with our AI models.',
    href: '/upload',
    color: 'from-orange-500 to-red-500',
  },
  {
    icon: Search,
    title: 'SNP Query',
    description: 'Search and explore specific SNP markers in our database with detailed information.',
    href: '/snp-query',
    color: 'from-cyan-500 to-blue-500',
  },
  {
    icon: MessageSquare,
    title: 'AI Assistant',
    description: 'Chat with our AI assistant for help with genetic analysis and interpretation.',
    href: '/chat',
    color: 'from-violet-500 to-purple-500',
  },
];

interface ModelStatus {
  gender_loaded: boolean;
  ancestry_loaded: boolean;
  gender_model_dir?: string;
  ancestry_model_dir?: string;
}

export default function HomePage() {
  const [modelStatus, setModelStatus] = useState<ModelStatus>({
    gender_loaded: false,
    ancestry_loaded: false,
  });

  useEffect(() => {
    // Check model status - this would need an API endpoint
    // For now, we'll assume models are loaded
    setModelStatus({
      gender_loaded: true,
      ancestry_loaded: true,
    });
  }, []);

  return (
    <div className="min-h-screen">
      {/* Hero Section */}
      <section className="hero-section mb-8">
        <div className="container mx-auto px-4">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <div className="animate-fade-in">
              <div className="hero-badge inline-flex items-center gap-2 mb-6">
                <Sparkles className="w-4 h-4" />
                <span>AI-Powered Genetic Analysis</span>
              </div>
              
              <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold text-white mb-6 leading-tight">
                Unlock the Secrets of Your{' '}
                <span className="text-gradient-light">DNA</span>
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
                  <Button variant="secondary" size="lg" icon={<ChevronRight className="w-5 h-5" />}>
                    View Dashboard
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
      <section className="py-12 mb-8">
        <div className="container mx-auto px-4">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {stats.map((stat, index) => (
              <div key={index} className="stat-card" data-aos="fade-up" data-aos-delay={index * 100}>
                <div className="stat-number counter" data-count={stat.value.replace(/[^0-9]/g, '')}>
                  {stat.value}
                </div>
                <div className="stat-label">{stat.label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* System Status */}
      <section className="mb-8">
        <div className="container mx-auto px-4">
          <div className="grid md:grid-cols-2 gap-6">
            <Card className="h-full" data-aos="fade-right">
              <CardContent className="p-6">
                <div className="flex items-center mb-4">
                  <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-primary-500/20 to-accent-500/20 flex items-center justify-center mr-4">
                    <User className="w-6 h-6 text-primary-400" />
                  </div>
                  <div>
                    <h5 className="font-bold text-white mb-1">Gender Prediction Model</h5>
                    {modelStatus.gender_loaded ? (
                      <Badge variant="success">
                        <CheckCircle className="w-3 h-3 mr-1" />
                        Online
                      </Badge>
                    ) : (
                      <Badge variant="warning">
                        <AlertCircle className="w-3 h-3 mr-1" />
                        Offline
                      </Badge>
                    )}
                  </div>
                </div>
                {modelStatus.gender_loaded ? (
                  <>
                    <p className="text-white/60 mb-2 text-sm">
                      Model loaded successfully and ready for predictions.
                    </p>
                    <div className="flex items-center">
                      <span className="pulse-dot mr-2"></span>
                      <small className="text-white/40 text-xs">
                        {modelStatus.gender_model_dir || 'Model ready'}
                      </small>
                    </div>
                  </>
                ) : (
                  <p className="text-white/60 text-sm">
                    The Gender Prediction model needs to be loaded.
                  </p>
                )}
              </CardContent>
            </Card>

            <Card className="h-full" data-aos="fade-left">
              <CardContent className="p-6">
                <div className="flex items-center mb-4">
                  <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-primary-500/20 to-accent-500/20 flex items-center justify-center mr-4">
                    <Globe2 className="w-6 h-6 text-primary-400" />
                  </div>
                  <div>
                    <h5 className="font-bold text-white mb-1">Ancestry Prediction Model</h5>
                    {modelStatus.ancestry_loaded ? (
                      <Badge variant="success">
                        <CheckCircle className="w-3 h-3 mr-1" />
                        Online
                      </Badge>
                    ) : (
                      <Badge variant="warning">
                        <AlertCircle className="w-3 h-3 mr-1" />
                        Offline
                      </Badge>
                    )}
                  </div>
                </div>
                {modelStatus.ancestry_loaded ? (
                  <>
                    <p className="text-white/60 mb-2 text-sm">
                      Model loaded successfully and ready for predictions.
                    </p>
                    <div className="flex items-center">
                      <span className="pulse-dot mr-2"></span>
                      <small className="text-white/40 text-xs">
                        {modelStatus.ancestry_model_dir || 'Model ready'}
                      </small>
                    </div>
                  </>
                ) : (
                  <p className="text-white/60 text-sm">
                    The ancestry prediction model needs to be loaded.
                  </p>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* Model Upload Section - Only show if models not loaded */}
      {(!modelStatus.gender_loaded || !modelStatus.ancestry_loaded) && (
        <section className="mb-8" data-aos="fade-up">
          <div className="container mx-auto px-4">
            <Card className="border-2 border-primary-500/30">
              <CardContent className="p-6">
                <h4 className="text-gradient font-bold mb-4 flex items-center gap-2">
                  <FileText className="w-5 h-5" />
                  Configure Models
                </h4>
                <form className="space-y-4">
                  <div className="grid md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-white/80 mb-2">
                        <User className="w-4 h-4 inline mr-1" />
                        Gender Prediction Model Directory
                      </label>
                      <div className="flex gap-2">
                        <input
                          type="text"
                          className="input-field flex-1"
                          placeholder="./hapmap_data/gender_prediction_data"
                          defaultValue={modelStatus.gender_model_dir}
                          readOnly={modelStatus.gender_loaded}
                        />
                        <span className="input-group-text bg-white/5 border border-white/10 rounded-lg px-3 flex items-center text-white/60">
                          <FileText className="w-4 h-4" />
                        </span>
                      </div>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-white/80 mb-2">
                        <Globe2 className="w-4 h-4 inline mr-1" />
                        Ancestry Prediction Model Directory
                      </label>
                      <div className="flex gap-2">
                        <input
                          type="text"
                          className="input-field flex-1"
                          placeholder="./hapmap_data/Model_region"
                          defaultValue={modelStatus.ancestry_model_dir}
                          readOnly={modelStatus.ancestry_loaded}
                        />
                        <span className="input-group-text bg-white/5 border border-white/10 rounded-lg px-3 flex items-center text-white/60">
                          <FileText className="w-4 h-4" />
                        </span>
                      </div>
                    </div>
                  </div>
                  <Button type="submit" className="btn-glow">
                    <FileText className="w-4 h-4 mr-2" />
                    Load Models
                  </Button>
                </form>
              </CardContent>
            </Card>
          </div>
        </section>
      )}

      {/* Features Section */}
      <section className="mb-8">
        <div className="container mx-auto px-4">
          <div className="text-center mb-12" data-aos="fade-up">
            <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4">
              Powerful <span className="text-gradient">Features</span>
            </h2>
            <p className="text-white/60 max-w-2xl mx-auto">
              Explore our comprehensive suite of genetic analysis tools powered by cutting-edge machine learning.
            </p>
          </div>
          
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {features.map((feature, index) => {
              const Icon = feature.icon;
              return (
                <Link key={index} href={feature.href}>
                  <Card hover className="h-full" data-aos="fade-up" data-aos-delay={index * 100}>
                    <CardContent className="p-6">
                      <div className={`w-16 h-16 rounded-xl bg-gradient-to-br ${feature.color} bg-opacity-20 flex items-center justify-center mb-4`}>
                        <Icon className="w-8 h-8 text-white" />
                      </div>
                      <h5 className="text-lg font-semibold text-white mb-2">
                        {feature.title}
                      </h5>
                      <p className="text-sm text-white/60 mb-4">
                        {feature.description}
                      </p>
                      <Button variant="secondary" size="sm">
                        Explore
                        <ChevronRight className="w-4 h-4 ml-1" />
                      </Button>
                    </CardContent>
                  </Card>
                </Link>
              );
            })}
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="mb-8" data-aos="fade-up">
        <div className="container mx-auto px-4">
          <Card>
            <CardContent className="p-6">
              <h5 className="font-bold text-white mb-6 flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-primary-400" />
                How It Works
              </h5>
              <div className="grid md:grid-cols-4 gap-6">
                {[
                  { step: '1', title: 'Upload Data', desc: 'Submit your SNP data in CSV format' },
                  { step: '2', title: 'AI Analysis', desc: 'Our ML models process your genetic markers' },
                  { step: '3', title: 'Get Results', desc: 'Receive detailed predictions and insights' },
                  { step: '4', title: 'Explore More', desc: 'Visualize and analyze your genetic data' },
                ].map((item, index) => (
                  <div key={index} className="text-center">
                    <div className="w-16 h-16 rounded-full bg-gradient-primary flex items-center justify-center mx-auto mb-4 text-white font-bold text-xl">
                      {item.step}
                    </div>
                    <h6 className="font-bold text-white mb-2">{item.title}</h6>
                    <p className="text-white/60 text-sm">{item.desc}</p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      </section>

      {/* Benefits Section */}
      <section className="mb-8 bg-white/5 rounded-2xl p-8">
        <div className="container mx-auto px-4">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <div>
              <h2 className="text-3xl sm:text-4xl font-bold text-white mb-6">
                Why Choose <span className="text-gradient">GenovaAI</span>?
              </h2>
              <p className="text-white/60 mb-8">
                Our platform combines cutting-edge AI technology with a deep understanding 
                of human genetics to deliver accurate, actionable insights.
              </p>
              
              <div className="space-y-6">
                {[
                  { icon: Sparkles, title: 'AI-Powered Analysis', desc: 'State-of-the-art machine learning models trained on diverse genetic datasets.' },
                  { icon: Shield, title: 'Privacy First', desc: 'Your genetic data is processed securely with industry-standard encryption.' },
                  { icon: Zap, title: 'Instant Results', desc: 'Get ancestry predictions and health insights in seconds.' },
                  { icon: Globe, title: 'Global Coverage', desc: 'Supporting 11 populations from around the world.' },
                ].map((benefit, index) => {
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
                          {benefit.desc}
                        </p>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
            
            <div className="relative">
              <Card className="p-8">
                <CardContent className="space-y-6 p-0 text-center">
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
                </CardContent>
              </Card>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="mb-8">
        <div className="container mx-auto px-4 text-center">
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
