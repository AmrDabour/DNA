'use client';

import { useState } from 'react';
import { Calculator, AlertTriangle, TrendingUp, Activity } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Badge } from '@/components/ui/Badge';
import { api } from '@/lib/api';

interface RiskResult {
  disease?: string;
  trait?: string;
  risk_level?: string;
  probability?: number;
  description?: string;
}

interface RiskResults {
  risks?: RiskResult[];
}

export default function RiskCalculatorPage() {
  const [sampleId, setSampleId] = useState('');
  const [results, setResults] = useState<RiskResults | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleCalculate = async () => {
    if (!sampleId.trim()) {
      setError('Please enter a sample ID');
      return;
    }

    setLoading(true);
    setError('');
    try {
      const response = await api.calculateRisk({ sample_id: sampleId });
      if (response.success && response.data) {
        setResults(response.data);
      } else {
        setError('Failed to calculate risk. Please check the sample ID.');
        setResults(null);
      }
    } catch {
      setError('Error calculating risk');
      setResults(null);
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
              <Calculator className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-white">Health Risk Calculator</h1>
              <p className="text-white/60">Calculate disease risk based on genetic markers</p>
            </div>
          </div>
        </div>

        {/* Input Form */}
        <Card className="mb-8">
          <CardContent className="p-6">
            <div className="flex gap-4">
              <div className="flex-1">
                <Input
                  label="Sample ID"
                  placeholder="Enter sample ID (e.g., NA18515)"
                  value={sampleId}
                  onChange={(e) => setSampleId(e.target.value)}
                />
              </div>
              <div className="flex items-end">
                <Button onClick={handleCalculate} disabled={loading}>
                  <Calculator className="w-5 h-5" />
                  Calculate Risk
                </Button>
              </div>
            </div>
            {error && (
              <div className="mt-4 p-3 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400 text-sm flex items-center gap-2">
                <AlertTriangle className="w-4 h-4" />
                {error}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Results */}
        {results && (
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <TrendingUp className="w-5 h-5 text-primary-400" />
                  Risk Assessment Results
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {results.risks && Array.isArray(results.risks) && results.risks.length > 0 ? (
                    results.risks.map((risk: RiskResult, i: number) => (
                      <div key={i} className="glass-card p-4">
                        <div className="flex items-center justify-between mb-2">
                          <span className="font-semibold text-white">{risk.disease || risk.trait || 'Unknown'}</span>
                          <Badge
                            variant={
                              risk.risk_level === 'High' ? 'danger' :
                              risk.risk_level === 'Medium' ? 'warning' : 'success'
                            }
                          >
                            {risk.risk_level || 'Low'}
                          </Badge>
                        </div>
                        {risk.probability && (
                          <div className="mt-3">
                            <div className="flex justify-between text-sm text-white/60 mb-1">
                              <span>Risk Probability</span>
                              <span className="text-white font-semibold">{risk.probability}%</span>
                            </div>
                            <div className="h-2 bg-white/10 rounded-full overflow-hidden">
                              <div
                                className={`h-full rounded-full transition-all ${
                                  risk.risk_level === 'High' ? 'bg-gradient-to-r from-red-500 to-rose-500' :
                                  risk.risk_level === 'Medium' ? 'bg-gradient-to-r from-amber-500 to-orange-500' :
                                  'bg-gradient-to-r from-green-500 to-emerald-500'
                                }`}
                                style={{ width: `${risk.probability}%` }}
                              />
                            </div>
                          </div>
                        )}
                        {risk.description && (
                          <p className="text-sm text-white/60 mt-2">{risk.description}</p>
                        )}
                      </div>
                    ))
                  ) : (
                    <div className="text-center py-8 text-white/60">
                      <Activity className="w-12 h-12 mx-auto mb-4 opacity-30" />
                      <p>No risk data available for this sample</p>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Info Card */}
        <Card className="mt-8">
          <CardContent className="p-6">
            <div className="flex items-start gap-4">
              <AlertTriangle className="w-6 h-6 text-amber-400 shrink-0 mt-1" />
              <div>
                <h3 className="text-white font-semibold mb-2">Important Disclaimer</h3>
                <p className="text-white/60 text-sm leading-relaxed">
                  The risk calculations provided are based on genetic markers and statistical models. 
                  These results are for informational purposes only and should not be used as a 
                  substitute for professional medical advice, diagnosis, or treatment. Always consult 
                  with a qualified healthcare provider regarding any health concerns.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

