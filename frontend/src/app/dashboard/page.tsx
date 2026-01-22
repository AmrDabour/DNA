'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { 
  Activity, 
  Database, 
  Upload, 
  History, 
  TrendingUp,
  Users,
  Dna,
  ArrowRight,
  BarChart3,
  PieChart,
  LineChart
} from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { LoadingSkeleton } from '@/components/ui/Loading';
import { api } from '@/lib/api';
import { LineChart as RechartsLineChart, Line, PieChart as RechartsPieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

interface DashboardStats {
  total_analyses: number;
  success_rate: number;
  total_samples: number;
  populations: number;
  analysis_trends?: Array<{ date: string; count: number }>;
  population_distribution?: Array<{ name: string; value: number }>;
  gender_predictions?: { male: number; female: number };
}

const COLORS = ['#6366f1', '#8b5cf6', '#06b6d4', '#10b981', '#f59e0b', '#f43f5e', '#a78bfa', '#22d3ee', '#ec4899', '#14b8a6', '#f97316'];

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [dashboardRes] = await Promise.all([
          api.getDashboardStats().catch(() => ({ success: false, data: null })),
        ]);
        
        if (dashboardRes.success && dashboardRes.data) {
          setStats(dashboardRes.data as DashboardStats);
        } else {
          // Fallback mock data
          const mockTrends = Array.from({ length: 7 }, (_, i) => {
            const date = new Date();
            date.setDate(date.getDate() - (6 - i));
            return {
              date: date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
              count: Math.floor(Math.random() * 20) + 5,
            };
          });

          const mockPopulations = [
            { name: 'YRI', value: 23 },
            { name: 'CEU', value: 18 },
            { name: 'CHB', value: 15 },
            { name: 'GIH', value: 12 },
            { name: 'JPT', value: 10 },
            { name: 'MEX', value: 8 },
            { name: 'TSI', value: 7 },
            { name: 'LWK', value: 6 },
            { name: 'MKK', value: 5 },
            { name: 'ASW', value: 4 },
            { name: 'CHD', value: 3 },
          ];

          setStats({
            total_analyses: 127,
            success_rate: 94.5,
            total_samples: 45,
            populations: 11,
            analysis_trends: mockTrends,
            population_distribution: mockPopulations,
            gender_predictions: { male: 68, female: 59 },
          });
        }
      } catch (error) {
        console.error('Error fetching dashboard data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  const quickActions = [
    { href: '/upload', icon: Upload, label: 'Upload Sample', color: 'from-blue-500 to-cyan-500' },
    { href: '/snp-database', icon: Database, label: 'SNP Database', color: 'from-purple-500 to-pink-500' },
    { href: '/risk-calculator', icon: Activity, label: 'Risk Calculator', color: 'from-orange-500 to-red-500' },
    { href: '/history', icon: History, label: 'View History', color: 'from-green-500 to-emerald-500' },
  ];

  if (loading) {
    return (
      <div className="min-h-screen py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            {[1, 2, 3, 4].map((i) => (
              <LoadingSkeleton key={i} className="h-32" />
            ))}
          </div>
          <LoadingSkeleton className="h-96" />
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-white mb-2">Dashboard</h1>
          <p className="text-white/60">Welcome back! Here is an overview of your genetic analysis activity.</p>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <Card className="p-6 border-l-4 border-l-blue-500">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-500/20 to-cyan-500/20 flex items-center justify-center">
                <BarChart3 className="w-6 h-6 text-blue-400" />
              </div>
              <div>
                <div className="text-2xl font-bold text-white">{stats?.total_analyses || 0}</div>
                <div className="text-sm text-white/60">Total Analyses</div>
              </div>
            </div>
          </Card>

          <Card className="p-6 border-l-4 border-l-emerald-500">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-emerald-500/20 to-green-500/20 flex items-center justify-center">
                <TrendingUp className="w-6 h-6 text-emerald-400" />
              </div>
              <div>
                <div className="text-2xl font-bold text-white">{stats?.success_rate || 0}%</div>
                <div className="text-sm text-white/60">Success Rate</div>
              </div>
            </div>
          </Card>

          <Card className="p-6 border-l-4 border-l-purple-500">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-purple-500/20 to-pink-500/20 flex items-center justify-center">
                <Users className="w-6 h-6 text-purple-400" />
              </div>
              <div>
                <div className="text-2xl font-bold text-white">{stats?.total_samples || 0}</div>
                <div className="text-sm text-white/60">Available Samples</div>
              </div>
            </div>
          </Card>

          <Card className="p-6 border-l-4 border-l-cyan-500">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-cyan-500/20 to-blue-500/20 flex items-center justify-center">
                <Dna className="w-6 h-6 text-cyan-400" />
              </div>
              <div>
                <div className="text-2xl font-bold text-white">{stats?.populations || 0}</div>
                <div className="text-sm text-white/60">Populations</div>
              </div>
            </div>
          </Card>
        </div>

        {/* Charts Grid */}
        <div className="grid lg:grid-cols-2 gap-8 mb-8">
          {/* Analysis Trends */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <LineChart className="w-5 h-5 text-primary-400" />
                Analysis Trends
              </CardTitle>
            </CardHeader>
            <CardContent>
              {stats?.analysis_trends ? (
                <ResponsiveContainer width="100%" height={300}>
                  <RechartsLineChart data={stats.analysis_trends}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                    <XAxis dataKey="date" stroke="rgba(255,255,255,0.6)" />
                    <YAxis stroke="rgba(255,255,255,0.6)" />
                    <Tooltip 
                      contentStyle={{ 
                        backgroundColor: 'rgba(15, 23, 42, 0.95)', 
                        border: '1px solid rgba(255,255,255,0.1)',
                        borderRadius: '8px',
                        color: '#fff'
                      }} 
                    />
                    <Legend />
                    <Line 
                      type="monotone" 
                      dataKey="count" 
                      stroke="#6366f1" 
                      strokeWidth={2}
                      dot={{ fill: '#6366f1', r: 4 }}
                      activeDot={{ r: 6 }}
                    />
                  </RechartsLineChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-[300px] flex items-center justify-center text-white/40">
                  No trend data available
                </div>
              )}
            </CardContent>
          </Card>

          {/* Population Distribution */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <PieChart className="w-5 h-5 text-primary-400" />
                Population Distribution
              </CardTitle>
            </CardHeader>
            <CardContent>
              {stats?.population_distribution ? (
                <ResponsiveContainer width="100%" height={300}>
                  <RechartsPieChart>
                    <Pie
                      data={stats.population_distribution}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {stats.population_distribution.map((entry, idx) => (
                        <Cell key={`cell-${idx}`} fill={COLORS[idx % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip 
                      contentStyle={{ 
                        backgroundColor: 'rgba(15, 23, 42, 0.95)', 
                        border: '1px solid rgba(255,255,255,0.1)',
                        borderRadius: '8px',
                        color: '#fff'
                      }} 
                    />
                  </RechartsPieChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-[300px] flex items-center justify-center text-white/40">
                  No population data available
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Gender Prediction Stats */}
        {stats?.gender_predictions && (
          <Card className="mb-8">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Activity className="w-5 h-5 text-primary-400" />
                Gender Prediction Statistics
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid md:grid-cols-2 gap-6">
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-white/80">Male</span>
                    <span className="text-white font-semibold">{stats.gender_predictions.male}</span>
                  </div>
                  <div className="h-3 bg-white/10 rounded-full overflow-hidden">
                    <div 
                      className="h-full bg-gradient-to-r from-blue-500 to-cyan-500 rounded-full transition-all"
                      style={{ width: `${(stats.gender_predictions.male / (stats.gender_predictions.male + stats.gender_predictions.female)) * 100}%` }}
                    />
                  </div>
                </div>
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-white/80">Female</span>
                    <span className="text-white font-semibold">{stats.gender_predictions.female}</span>
                  </div>
                  <div className="h-3 bg-white/10 rounded-full overflow-hidden">
                    <div 
                      className="h-full bg-gradient-to-r from-pink-500 to-rose-500 rounded-full transition-all"
                      style={{ width: `${(stats.gender_predictions.female / (stats.gender_predictions.male + stats.gender_predictions.female)) * 100}%` }}
                    />
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Main Content Grid */}
        <div className="grid lg:grid-cols-3 gap-8">
          {/* Quick Actions */}
          <div className="lg:col-span-1">
            <Card>
              <CardHeader>
                <CardTitle>Quick Actions</CardTitle>
              </CardHeader>
              <CardContent className="p-4 pt-0">
                <div className="space-y-3">
                  {quickActions.map((action) => {
                    const Icon = action.icon;
                    return (
                      <Link key={action.href} href={action.href}>
                        <div className="flex items-center gap-4 p-3 rounded-xl hover:bg-white/5 transition-colors group cursor-pointer">
                          <div className={`w-10 h-10 rounded-lg bg-gradient-to-br ${action.color} flex items-center justify-center`}>
                            <Icon className="w-5 h-5 text-white" />
                          </div>
                          <span className="text-white/80 group-hover:text-white transition-colors">
                            {action.label}
                          </span>
                          <ArrowRight className="w-4 h-4 text-white/40 ml-auto group-hover:text-white/80 group-hover:translate-x-1 transition-all" />
                        </div>
                      </Link>
                    );
                  })}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Recent Analyses */}
          <div className="lg:col-span-2">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between">
                <CardTitle>Recent Activity</CardTitle>
                <Link href="/history">
                  <Button variant="ghost" size="sm">
                    View All
                    <ArrowRight className="w-4 h-4" />
                  </Button>
                </Link>
              </CardHeader>
              <CardContent className="p-0">
                <div className="text-center py-12">
                  <History className="w-12 h-12 text-white/20 mx-auto mb-4" />
                  <p className="text-white/60 mb-4">No recent analyses</p>
                  <Link href="/upload">
                    <Button>
                      <Upload className="w-5 h-5" />
                      Upload Your First Sample
                    </Button>
                  </Link>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>

        {/* Population Coverage */}
        <Card className="mt-8">
          <CardHeader>
            <CardTitle>Supported Populations</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-4">
              {['CEU', 'CHB', 'CHD', 'GIH', 'JPT', 'LWK', 'MEX', 'MKK', 'TSI', 'YRI', 'ASW'].map((pop) => (
                <div key={pop} className="glass-card p-4 text-center hover:bg-white/10 transition-colors border border-white/5">
                  <div className="text-lg font-bold text-gradient">{pop}</div>
                  <div className="text-xs text-white/40 mt-1">Population</div>
                  {stats?.population_distribution && (
                    <div className="text-xs text-white/60 mt-1">
                      {stats.population_distribution.find(p => p.name === pop)?.value || 0} samples
                    </div>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
