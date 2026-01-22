'use client';

import { useState } from 'react';
import { Search, Database, Info } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Badge } from '@/components/ui/Badge';
import { api } from '@/lib/api';

interface SNPResult {
  rs_id: string;
  gene_symbol?: string;
  chromosome?: string;
  position?: number;
  risk_allele?: string;
  description?: string;
  disease_associations?: string[];
  associated_traits?: string[];
  clinical_significance?: string;
}

export default function SNPQueryPage() {
  const [rsId, setRsId] = useState('');
  const [result, setResult] = useState<SNPResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSearch = async () => {
    if (!rsId.trim()) {
      setError('Please enter an RS ID');
      return;
    }

    setLoading(true);
    setError('');
    try {
      const response = await api.searchSnps({ q: rsId, page: 1 });
      if (response.success && response.data) {
        const data = response.data as { snps: SNPResult[] };
        if (data.snps && data.snps.length > 0) {
          setResult(data.snps[0]);
        } else {
          setError('SNP not found');
          setResult(null);
        }
      }
    } catch {
      setError('Error searching for SNP');
      setResult(null);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen py-8">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8 text-center">
          <div className="flex items-center justify-center gap-3 mb-4">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-primary-500 to-accent-500 flex items-center justify-center">
              <Search className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-white">SNP Query</h1>
              <p className="text-white/60">Look up specific SNP markers by RS ID</p>
            </div>
          </div>
        </div>

        {/* Search Form */}
        <Card className="mb-8">
          <CardContent className="p-6">
            <div className="flex gap-4">
              <div className="flex-1">
                <Input
                  placeholder="Enter RS ID (e.g., rs123456)"
                  icon={<Database className="w-5 h-5" />}
                  value={rsId}
                  onChange={(e) => setRsId(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                />
              </div>
              <Button onClick={handleSearch} disabled={loading}>
                <Search className="w-5 h-5" />
                Search
              </Button>
            </div>
            {error && (
              <div className="mt-4 p-3 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400 text-sm">
                {error}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Results */}
        {result && (
          <Card>
            <CardHeader>
              <CardTitle className="font-mono text-2xl">{result.rs_id}</CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid md:grid-cols-2 gap-4">
                <div className="glass-card p-4">
                  <div className="text-sm text-white/60 mb-1">Gene Symbol</div>
                  <div className="text-lg font-semibold text-white">{result.gene_symbol || 'N/A'}</div>
                </div>
                <div className="glass-card p-4">
                  <div className="text-sm text-white/60 mb-1">Chromosome</div>
                  <div className="text-lg font-semibold text-white">{result.chromosome || 'N/A'}</div>
                </div>
                <div className="glass-card p-4">
                  <div className="text-sm text-white/60 mb-1">Position</div>
                  <div className="text-lg font-semibold text-white font-mono">
                    {result.position?.toLocaleString() || 'N/A'}
                  </div>
                </div>
                <div className="glass-card p-4">
                  <div className="text-sm text-white/60 mb-1">Risk Allele</div>
                  <div className="text-lg font-semibold text-red-400 font-mono">
                    {result.risk_allele || 'N/A'}
                  </div>
                </div>
              </div>

              {result.description && (
                <div>
                  <div className="text-sm font-semibold text-white/80 mb-2 flex items-center gap-2">
                    <Info className="w-4 h-4" />
                    Description
                  </div>
                  <p className="text-white/70">{result.description}</p>
                </div>
              )}

              {result.disease_associations && result.disease_associations.length > 0 && (
                <div>
                  <div className="text-sm font-semibold text-white/80 mb-2">Disease Associations</div>
                  <div className="flex flex-wrap gap-2">
                    {result.disease_associations.map((disease: string, i: number) => (
                      <Badge key={i} variant="warning">{disease}</Badge>
                    ))}
                  </div>
                </div>
              )}

              {result.associated_traits && result.associated_traits.length > 0 && (
                <div>
                  <div className="text-sm font-semibold text-white/80 mb-2">Associated Traits</div>
                  <div className="flex flex-wrap gap-2">
                    {result.associated_traits.map((trait: string, i: number) => (
                      <Badge key={i} variant="primary">{trait}</Badge>
                    ))}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        )}

        {/* Info Card */}
        <Card className="mt-8">
          <CardContent className="p-6">
            <div className="flex items-start gap-4">
              <Info className="w-6 h-6 text-primary-400 shrink-0 mt-1" />
              <div>
                <h3 className="text-white font-semibold mb-2">About RS IDs</h3>
                <p className="text-white/60 text-sm leading-relaxed">
                  RS IDs (Reference SNP cluster IDs) are unique identifiers assigned to genetic variants 
                  by the dbSNP database. Each RS ID represents a specific single nucleotide polymorphism 
                  (SNP) in the human genome. Use this tool to quickly look up detailed information about 
                  any SNP by entering its RS ID.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

