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
  BarChart3
} from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Loading, LoadingSkeleton } from '@/components/ui/Loading';
import { api } from '@/lib/api';

interface DashboardStats {
  total_analyses: number;
  total_snps: number;
  total_samples: number;
  recent_analyses: Array<{
    id: string;
    sample_id: string;
    population: string;
    gender: string;
    created_at: string;
  }>;
}

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [snpStats, setSnpStats] = useState({ total_snps: 0, genes: 0, chromosomes: 0 });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [snpRes] = await Promise.all([
          api.getSnpStats(),
        ]);
        
        if (snpRes.success && snpRes.data) {
          const data = snpRes.data as { stats: typeof snpStats };
          setSnpStats(data.stats);
        }
        
        // Mock dashboard stats for now
        setStats({
          total_analyses: 127,
          total_snps: snpStats.total_snps,
          total_samples: 45,
          recent_analyses: [
            { id: '1', sample_id: 'NA18515', population: 'YRI', gender: 'Male', created_at: '2026-01-22' },
            { id: '2', sample_id: 'NA20805', population: 'GIH', gender: 'Male', created_at: '2026-01-21' },
          ],
        });
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
          <p className="text-white/60">Welcome back! Here's an overview of your genetic analysis activity.</p>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <Card className="p-6">
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

          <Card className="p-6">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-purple-500/20 to-pink-500/20 flex items-center justify-center">
                <Dna className="w-6 h-6 text-purple-400" />
              </div>
              <div>
                <div className="text-2xl font-bold text-white">{snpStats.total_snps}</div>
                <div className="text-sm text-white/60">SNPs in Database</div>
              </div>
            </div>
          </Card>

          <Card className="p-6">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-green-500/20 to-emerald-500/20 flex items-center justify-center">
                <Users className="w-6 h-6 text-green-400" />
              </div>
              <div>
                <div className="text-2xl font-bold text-white">{stats?.total_samples || 0}</div>
                <div className="text-sm text-white/60">Samples Analyzed</div>
              </div>
            </div>
          </Card>

          <Card className="p-6">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-orange-500/20 to-red-500/20 flex items-center justify-center">
                <TrendingUp className="w-6 h-6 text-orange-400" />
              </div>
              <div>
                <div className="text-2xl font-bold text-white">{snpStats.genes}</div>
                <div className="text-sm text-white/60">Genes Covered</div>
              </div>
            </div>
          </Card>
        </div>

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
                        <div className="flex items-center gap-4 p-3 rounded-xl hover:bg-white/5 transition-colors group">
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
                <CardTitle>Recent Analyses</CardTitle>
                <Link href="/history">
                  <Button variant="ghost" size="sm">
                    View All
                    <ArrowRight className="w-4 h-4" />
                  </Button>
                </Link>
              </CardHeader>
              <CardContent className="p-0">
                {stats?.recent_analyses && stats.recent_analyses.length > 0 ? (
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Sample ID</th>
                        <th>Population</th>
                        <th>Gender</th>
                        <th>Date</th>
                        <th>Action</th>
                      </tr>
                    </thead>
                    <tbody>
                      {stats.recent_analyses.map((analysis) => (
                        <tr key={analysis.id}>
                          <td className="font-mono text-primary-400">{analysis.sample_id}</td>
                          <td>
                            <Badge variant="primary">{analysis.population}</Badge>
                          </td>
                          <td>{analysis.gender}</td>
                          <td className="text-white/60">{analysis.created_at}</td>
                          <td>
                            <Link href={`/predictions/${analysis.sample_id}`}>
                              <Button variant="ghost" size="sm">View</Button>
                            </Link>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                ) : (
                  <div className="text-center py-12">
                    <History className="w-12 h-12 text-white/20 mx-auto mb-4" />
                    <p className="text-white/60 mb-4">No analyses yet</p>
                    <Link href="/upload">
                      <Button>
                        <Upload className="w-5 h-5" />
                        Upload Your First Sample
                      </Button>
                    </Link>
                  </div>
                )}
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
                <div key={pop} className="glass-card p-4 text-center hover:bg-white/10 transition-colors">
                  <div className="text-lg font-bold text-gradient">{pop}</div>
                  <div className="text-xs text-white/40 mt-1">Population</div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

