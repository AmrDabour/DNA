'use client';

import { useState, useEffect } from 'react';
import { Search, Database, Filter, ChevronLeft, ChevronRight, X, Activity } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Badge } from '@/components/ui/Badge';
import { Loading } from '@/components/ui/Loading';
import { api } from '@/lib/api';

interface SNP {
  rs_id: string;
  gene_symbol: string;
  gene_name: string;
  chromosome: string;
  position: number;
  description: string;
  disease_associations: string[];
  associated_traits: string[];
  risk_allele: string;
  odds_ratio: number;
  clinical_significance: string;
}

interface SearchFilters {
  q: string;
  chromosome: string;
  gene: string;
  trait: string;
  page: number;
}

export default function SNPDatabasePage() {
  const [snps, setSnps] = useState<SNP[]>([]);
  const [stats, setStats] = useState({ total_snps: 0, chromosomes: 0, genes: 0, diseases: 0, traits: 0 });
  const [chromosomes, setChromosomes] = useState<string[]>([]);
  const [genes, setGenes] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState<SearchFilters>({
    q: '',
    chromosome: '',
    gene: '',
    trait: '',
    page: 1,
  });
  const [pagination, setPagination] = useState({ page: 1, pages: 1, total: 0, per_page: 20 });
  const [selectedSnp, setSelectedSnp] = useState<SNP | null>(null);

  // Fetch initial data
  useEffect(() => {
    const fetchInitialData = async () => {
      try {
        const [statsRes, chromRes, genesRes] = await Promise.all([
          api.getSnpStats(),
          api.getChromosomes(),
          api.getGenes(),
        ]);
        
        if (statsRes.success && statsRes.data) {
          setStats((statsRes.data as { stats: typeof stats }).stats);
        }
        if (chromRes.success && chromRes.data) {
          setChromosomes(chromRes.data.chromosomes);
        }
        if (genesRes.success && genesRes.data) {
          setGenes(genesRes.data.genes);
        }
      } catch (error) {
        console.error('Error fetching initial data:', error);
      }
    };
    
    fetchInitialData();
  }, []);

  // Search SNPs
  useEffect(() => {
    const searchSnps = async () => {
      setLoading(true);
      try {
        const response = await api.searchSnps(filters);
        if (response.success && response.data) {
          const data = response.data as { snps: SNP[]; pagination: typeof pagination };
          setSnps(data.snps);
          setPagination(data.pagination);
        }
      } catch (error) {
        console.error('Error searching SNPs:', error);
      } finally {
        setLoading(false);
      }
    };

    const debounce = setTimeout(searchSnps, 300);
    return () => clearTimeout(debounce);
  }, [filters]);

  const handleFilterChange = (key: keyof SearchFilters, value: string | number) => {
    setFilters(prev => ({ ...prev, [key]: value, page: key === 'page' ? value as number : 1 }));
  };

  const clearFilters = () => {
    setFilters({ q: '', chromosome: '', gene: '', trait: '', page: 1 });
  };

  return (
    <div className="min-h-screen py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center">
              <Database className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-white">SNP Database</h1>
              <p className="text-white/60">Explore genetic variants and their associations</p>
            </div>
          </div>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-8">
          <Card className="text-center p-4">
            <div className="text-2xl font-bold text-gradient">{stats.total_snps}</div>
            <div className="text-xs text-white/60 uppercase">Total SNPs</div>
          </Card>
          <Card className="text-center p-4">
            <div className="text-2xl font-bold text-gradient">{stats.chromosomes}</div>
            <div className="text-xs text-white/60 uppercase">Chromosomes</div>
          </Card>
          <Card className="text-center p-4">
            <div className="text-2xl font-bold text-gradient">{stats.genes}</div>
            <div className="text-xs text-white/60 uppercase">Genes</div>
          </Card>
          <Card className="text-center p-4">
            <div className="text-2xl font-bold text-gradient">{stats.diseases}</div>
            <div className="text-xs text-white/60 uppercase">Diseases</div>
          </Card>
          <Card className="text-center p-4">
            <div className="text-2xl font-bold text-gradient">{stats.traits}</div>
            <div className="text-xs text-white/60 uppercase">Traits</div>
          </Card>
        </div>

        {/* Quick Search Tags */}
        <Card className="mb-6">
          <CardContent className="p-4">
            <div className="flex items-center gap-2 mb-3">
              <span className="text-sm text-white/60">Quick Search:</span>
            </div>
            <div className="flex flex-wrap gap-2">
              {[
                { label: 'Eye Color', trait: 'Eye Color' },
                { label: 'Skin', trait: 'Skin' },
                { label: "Alzheimer's", trait: "Alzheimer's" },
                { label: 'Diabetes', trait: 'Diabetes' },
                { label: 'Heart Disease', trait: 'Heart Disease' },
                { label: 'Cancer', trait: 'Cancer' },
                { label: 'Obesity', trait: 'Obesity' },
                { label: 'Height', trait: 'Height' },
              ].map((tag) => (
                <button
                  key={tag.trait}
                  onClick={() => handleFilterChange('trait', tag.trait)}
                  className={cn(
                    'px-3 py-1.5 rounded-full text-xs font-medium transition-all',
                    filters.trait === tag.trait
                      ? 'bg-gradient-to-r from-primary-500 to-accent-500 text-white shadow-lg'
                      : 'bg-white/5 text-white/60 hover:bg-white/10 hover:text-white border border-white/10'
                  )}
                >
                  {tag.label}
                </button>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Search & Filters */}
        <Card className="mb-8">
          <CardContent className="p-6">
            <div className="grid md:grid-cols-4 gap-4">
              <div className="md:col-span-4">
                <Input
                  placeholder="Search by RS ID, gene, or description..."
                  icon={<Search className="w-5 h-5" />}
                  value={filters.q}
                  onChange={(e) => handleFilterChange('q', e.target.value)}
                />
              </div>
              
              <div>
                <label className="block text-sm text-white/60 mb-2">Chromosome</label>
                <select
                  className="input-field"
                  value={filters.chromosome}
                  onChange={(e) => handleFilterChange('chromosome', e.target.value)}
                >
                  <option value="">All Chromosomes</option>
                  {chromosomes.map(chr => (
                    <option key={chr} value={chr}>Chromosome {chr}</option>
                  ))}
                </select>
              </div>
              
              <div>
                <label className="block text-sm text-white/60 mb-2">Gene</label>
                <select
                  className="input-field"
                  value={filters.gene}
                  onChange={(e) => handleFilterChange('gene', e.target.value)}
                >
                  <option value="">All Genes</option>
                  {genes.map(gene => (
                    <option key={gene} value={gene}>{gene}</option>
                  ))}
                </select>
              </div>
              
              <div>
                <label className="block text-sm text-white/60 mb-2">Trait/Disease</label>
                <Input
                  placeholder="Filter by trait..."
                  value={filters.trait}
                  onChange={(e) => handleFilterChange('trait', e.target.value)}
                />
              </div>
              
              <div className="flex items-end">
                <Button variant="ghost" onClick={clearFilters} className="w-full">
                  <X className="w-4 h-4" />
                  Clear Filters
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Results */}
        <Card>
          <CardHeader>
            <CardTitle>Search Results</CardTitle>
            <CardDescription>
              Found {pagination.total} SNPs
            </CardDescription>
          </CardHeader>
          <CardContent className="p-0">
            {loading ? (
              <div className="flex justify-center py-12">
                <Loading text="Searching SNPs..." />
              </div>
            ) : snps.length === 0 ? (
              <div className="text-center py-12">
                <Database className="w-12 h-12 text-white/20 mx-auto mb-4" />
                <p className="text-white/60">No SNPs found matching your criteria</p>
              </div>
            ) : (
              <>
                <div className="overflow-x-auto">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>RS ID</th>
                        <th>Gene</th>
                        <th>Chr</th>
                        <th>Position</th>
                        <th>Risk Allele</th>
                        <th>Associations</th>
                        <th>Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {snps.map((snp) => (
                        <tr key={snp.rs_id} className="cursor-pointer" onClick={() => setSelectedSnp(snp)}>
                          <td className="font-mono text-primary-400">{snp.rs_id}</td>
                          <td>
                            <span className="font-semibold text-white">{snp.gene_symbol}</span>
                          </td>
                          <td>{snp.chromosome}</td>
                          <td className="font-mono text-sm">{snp.position?.toLocaleString()}</td>
                          <td>
                            <Badge 
                              variant={snp.risk_allele ? 'danger' : 'default'}
                              className="font-mono"
                            >
                              {snp.risk_allele || 'N/A'}
                            </Badge>
                          </td>
                          <td>
                            <div className="flex flex-wrap gap-1">
                              {snp.disease_associations?.slice(0, 2).map((disease, i) => (
                                <Badge key={i} variant="warning" className="text-xs">{disease}</Badge>
                              ))}
                              {snp.disease_associations?.length > 2 && (
                                <Badge className="text-xs">+{snp.disease_associations.length - 2}</Badge>
                              )}
                              {(!snp.disease_associations || snp.disease_associations.length === 0) && (
                                <span className="text-white/40 text-xs">None</span>
                              )}
                            </div>
                          </td>
                          <td>
                            <Button size="sm" variant="ghost" onClick={() => setSelectedSnp(snp)}>
                              View
                            </Button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                {/* Modern Pagination */}
                {pagination.pages > 1 && (
                  <div className="flex items-center justify-between p-6 border-t border-white/10 bg-white/5">
                    <div className="text-sm text-white/60">
                      Showing <span className="text-white font-semibold">
                        {((pagination.page - 1) * pagination.per_page) + 1}
                      </span> to{' '}
                      <span className="text-white font-semibold">
                        {Math.min(pagination.page * pagination.per_page, pagination.total)}
                      </span> of{' '}
                      <span className="text-white font-semibold">{pagination.total}</span> results
                    </div>
                    <div className="flex items-center gap-2">
                      <Button
                        variant="secondary"
                        size="sm"
                        disabled={pagination.page === 1}
                        onClick={() => handleFilterChange('page', pagination.page - 1)}
                        className="disabled:opacity-30"
                      >
                        <ChevronLeft className="w-4 h-4" />
                        Previous
                      </Button>
                      
                      {/* Page Numbers */}
                      <div className="flex gap-1">
                        {Array.from({ length: Math.min(5, pagination.pages) }, (_, i) => {
                          let pageNum;
                          if (pagination.pages <= 5) {
                            pageNum = i + 1;
                          } else if (pagination.page <= 3) {
                            pageNum = i + 1;
                          } else if (pagination.page >= pagination.pages - 2) {
                            pageNum = pagination.pages - 4 + i;
                          } else {
                            pageNum = pagination.page - 2 + i;
                          }
                          
                          return (
                            <button
                              key={pageNum}
                              onClick={() => handleFilterChange('page', pageNum)}
                              className={cn(
                                'w-9 h-9 rounded-lg text-sm font-medium transition-all',
                                pagination.page === pageNum
                                  ? 'bg-gradient-to-r from-primary-500 to-accent-500 text-white shadow-lg'
                                  : 'bg-white/5 text-white/60 hover:bg-white/10 hover:text-white border border-white/10'
                              )}
                            >
                              {pageNum}
                            </button>
                          );
                        })}
                      </div>
                      
                      <Button
                        variant="secondary"
                        size="sm"
                        disabled={pagination.page === pagination.pages}
                        onClick={() => handleFilterChange('page', pagination.page + 1)}
                        className="disabled:opacity-30"
                      >
                        Next
                        <ChevronRight className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                )}
              </>
            )}
          </CardContent>
        </Card>

        {/* SNP Detail Modal */}
        {selectedSnp && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 animate-fade-in">
            <div 
              className="modal-backdrop" 
              onClick={() => setSelectedSnp(null)}
            />
            <div className="modal-content relative z-10 max-w-3xl w-full max-h-[90vh] overflow-y-auto">
              {/* Modal Header */}
              <div className="sticky top-0 bg-slate-900/95 backdrop-blur-xl border-b border-white/10 p-6 flex items-start justify-between z-10">
                <div>
                  <h2 className="text-2xl font-bold text-white font-mono mb-1">{selectedSnp.rs_id}</h2>
                  <p className="text-white/60">
                    {selectedSnp.gene_name} ({selectedSnp.gene_symbol})
                  </p>
                </div>
                <button
                  onClick={() => setSelectedSnp(null)}
                  className="w-8 h-8 rounded-lg bg-white/5 hover:bg-white/10 flex items-center justify-center text-white/60 hover:text-white transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
              
              <div className="p-6 space-y-6">
                {/* Key Information Grid */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="glass-card p-4 border-l-4 border-l-blue-500">
                    <div className="text-xs text-white/60 mb-1 uppercase tracking-wider">Chromosome</div>
                    <div className="text-xl font-bold text-white">{selectedSnp.chromosome}</div>
                  </div>
                  <div className="glass-card p-4 border-l-4 border-l-purple-500">
                    <div className="text-xs text-white/60 mb-1 uppercase tracking-wider">Position</div>
                    <div className="text-xl font-bold text-white font-mono">
                      {selectedSnp.position?.toLocaleString()}
                    </div>
                  </div>
                  <div className="glass-card p-4 border-l-4 border-l-red-500">
                    <div className="text-xs text-white/60 mb-1 uppercase tracking-wider">Risk Allele</div>
                    <div className="text-xl font-bold text-red-400 font-mono">{selectedSnp.risk_allele || 'N/A'}</div>
                  </div>
                  <div className="glass-card p-4 border-l-4 border-l-emerald-500">
                    <div className="text-xs text-white/60 mb-1 uppercase tracking-wider">Odds Ratio</div>
                    <div className="text-xl font-bold text-white">{selectedSnp.odds_ratio || 'N/A'}</div>
                  </div>
                </div>
                
                {/* Description */}
                {selectedSnp.description && (
                  <div className="glass-card p-5">
                    <div className="text-sm font-semibold text-white/80 mb-2 flex items-center gap-2">
                      <Database className="w-4 h-4" />
                      Description
                    </div>
                    <p className="text-white/70 leading-relaxed">{selectedSnp.description}</p>
                  </div>
                )}
                
                {/* Disease Associations */}
                {selectedSnp.disease_associations && selectedSnp.disease_associations.length > 0 && (
                  <div>
                    <div className="text-sm font-semibold text-white/80 mb-3 flex items-center gap-2">
                      <Filter className="w-4 h-4" />
                      Disease Associations
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {selectedSnp.disease_associations.map((disease, i) => (
                        <Badge key={i} variant="warning" className="text-sm py-1.5 px-3">
                          {disease}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}
                
                {/* Associated Traits */}
                {selectedSnp.associated_traits && selectedSnp.associated_traits.length > 0 && (
                  <div>
                    <div className="text-sm font-semibold text-white/80 mb-3 flex items-center gap-2">
                      <Activity className="w-4 h-4" />
                      Associated Traits
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {selectedSnp.associated_traits.map((trait, i) => (
                        <Badge key={i} variant="primary" className="text-sm py-1.5 px-3">
                          {trait}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}
                
                {/* Clinical Significance */}
                <div className="pt-4 border-t border-white/10 flex items-center justify-between">
                  <div>
                    <div className="text-sm text-white/60 mb-1">Clinical Significance</div>
                    <Badge 
                      variant={
                        selectedSnp.clinical_significance?.toLowerCase().includes('risk') ? 'danger' : 
                        selectedSnp.clinical_significance?.toLowerCase().includes('protective') ? 'success' :
                        selectedSnp.clinical_significance?.toLowerCase().includes('drug') ? 'warning' : 'default'
                      }
                      className="text-sm py-1.5 px-4"
                    >
                      {selectedSnp.clinical_significance || 'Not specified'}
                    </Badge>
                  </div>
                  <Button variant="secondary" onClick={() => setSelectedSnp(null)}>
                    Close
                  </Button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}


