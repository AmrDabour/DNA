'use client';

import { useState } from 'react';
import { MapPin, Globe2, Users, TrendingUp } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';

const populations = [
  { code: 'YRI', name: 'Yoruba in Ibadan, Nigeria', region: 'Africa', color: '#6366f1' },
  { code: 'CEU', name: 'Utah Residents (CEPH) with Northern and Western European Ancestry', region: 'Europe', color: '#8b5cf6' },
  { code: 'CHB', name: 'Han Chinese in Beijing, China', region: 'Asia', color: '#06b6d4' },
  { code: 'CHD', name: 'Chinese in Metropolitan Denver, Colorado', region: 'Asia', color: '#10b981' },
  { code: 'GIH', name: 'Gujarati Indians in Houston, Texas', region: 'South Asia', color: '#f59e0b' },
  { code: 'JPT', name: 'Japanese in Tokyo, Japan', region: 'Asia', color: '#f43f5e' },
  { code: 'LWK', name: 'Luhya in Webuye, Kenya', region: 'Africa', color: '#a78bfa' },
  { code: 'MEX', name: 'Mexican Ancestry in Los Angeles, California', region: 'Americas', color: '#22d3ee' },
  { code: 'MKK', name: 'Maasai in Kinyawa, Kenya', region: 'Africa', color: '#ec4899' },
  { code: 'TSI', name: 'Toscani in Italia', region: 'Europe', color: '#14b8a6' },
  { code: 'ASW', name: 'Americans of African Ancestry in SW USA', region: 'Americas', color: '#f97316' },
];

export default function AncestryMapPage() {
  const [selectedPopulation, setSelectedPopulation] = useState<string | null>(null);

  return (
    <div className="min-h-screen py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-primary-500 to-accent-500 flex items-center justify-center">
              <MapPin className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-white">Ancestry Map</h1>
              <p className="text-white/60">Explore genetic ancestral populations and their geographic distribution</p>
            </div>
          </div>
        </div>

        <div className="grid lg:grid-cols-3 gap-8">
          {/* Population List */}
          <div className="lg:col-span-1">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Globe2 className="w-5 h-5 text-primary-400" />
                  Populations
                </CardTitle>
              </CardHeader>
              <CardContent className="p-0">
                <div className="divide-y divide-white/10">
                  {populations.map((pop) => (
                    <button
                      key={pop.code}
                      onClick={() => setSelectedPopulation(pop.code)}
                      className={`w-full p-4 text-left hover:bg-white/5 transition-colors ${
                        selectedPopulation === pop.code ? 'bg-primary-500/10 border-l-4 border-l-primary-500' : ''
                      }`}
                    >
                      <div className="flex items-center justify-between mb-2">
                        <span className="font-bold text-white">{pop.code}</span>
                        <div
                          className="w-4 h-4 rounded-full"
                          style={{ backgroundColor: pop.color }}
                        />
                      </div>
                      <p className="text-sm text-white/60">{pop.name}</p>
                      <Badge variant="primary" className="mt-2 text-xs">
                        {pop.region}
                      </Badge>
                    </button>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Map Visualization */}
          <div className="lg:col-span-2">
            <Card className="h-full">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <MapPin className="w-5 h-5 text-primary-400" />
                  Geographic Distribution
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-[600px] bg-gradient-to-br from-slate-800 to-slate-900 rounded-xl flex items-center justify-center relative overflow-hidden">
                  {/* Placeholder for map visualization */}
                  <div className="text-center z-10">
                    <Globe2 className="w-24 h-24 text-white/20 mx-auto mb-4" />
                    <p className="text-white/60 mb-2">Interactive Map Visualization</p>
                    <p className="text-white/40 text-sm">
                      {selectedPopulation 
                        ? `Showing distribution for ${populations.find(p => p.code === selectedPopulation)?.name}`
                        : 'Select a population to view its geographic distribution'}
                    </p>
                  </div>
                  
                  {/* Animated background */}
                  <div className="absolute inset-0 opacity-10">
                    {populations.map((pop, i) => (
                      <div
                        key={pop.code}
                        className="absolute rounded-full animate-pulse"
                        style={{
                          width: `${20 + Math.random() * 30}px`,
                          height: `${20 + Math.random() * 30}px`,
                          backgroundColor: pop.color,
                          left: `${10 + (i * 8)}%`,
                          top: `${20 + (i * 5)}%`,
                          animationDelay: `${i * 0.2}s`,
                        }}
                      />
                    ))}
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>

        {/* Population Statistics */}
        <div className="mt-8 grid md:grid-cols-4 gap-6">
          {[
            { label: 'Total Populations', value: '11', icon: Users },
            { label: 'Regions Covered', value: '5', icon: Globe2 },
            { label: 'Samples Analyzed', value: '1,000+', icon: TrendingUp },
            { label: 'Accuracy Rate', value: '97%', icon: TrendingUp },
          ].map((stat, i) => {
            const Icon = stat.icon;
            return (
              <Card key={i} className="text-center p-6">
                <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-primary-500/20 to-accent-500/20 flex items-center justify-center mx-auto mb-4">
                  <Icon className="w-6 h-6 text-primary-400" />
                </div>
                <div className="text-3xl font-bold text-gradient mb-2">{stat.value}</div>
                <div className="text-sm text-white/60">{stat.label}</div>
              </Card>
            );
          })}
        </div>
      </div>
    </div>
  );
}

