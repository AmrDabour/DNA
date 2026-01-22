'use client';

import { useState, useCallback } from 'react';
import { Upload, FileText, X, CheckCircle, AlertCircle, Dna, Info, Shield, Zap } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Loading } from '@/components/ui/Loading';
import { api } from '@/lib/api';
import { cn } from '@/lib/utils';

interface UploadState {
  file: File | null;
  uploading: boolean;
  progress: number;
  error: string | null;
  result: {
    sample_id: string;
    filename: string;
    snp_count: number;
  } | null;
}

export default function UploadPage() {
  const [state, setState] = useState<UploadState>({
    file: null,
    uploading: false,
    progress: 0,
    error: null,
    result: null,
  });
  const [dragActive, setDragActive] = useState(false);

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0]);
    }
  }, []);

  const handleFile = (file: File) => {
    // Validate file type
    const validTypes = ['.csv', '.txt', '.vcf', '.ped'];
    const fileExtension = '.' + file.name.split('.').pop()?.toLowerCase();
    
    if (!validTypes.includes(fileExtension)) {
      setState(prev => ({
        ...prev,
        error: 'Invalid file type. Please upload a CSV, TXT, VCF, or PED file.',
        file: null,
      }));
      return;
    }

    // Validate file size (max 50MB)
    if (file.size > 50 * 1024 * 1024) {
      setState(prev => ({
        ...prev,
        error: 'File too large. Maximum size is 50MB.',
        file: null,
      }));
      return;
    }

    setState(prev => ({
      ...prev,
      file,
      error: null,
      result: null,
    }));
  };

  const handleUpload = async () => {
    if (!state.file) return;

    setState(prev => ({ ...prev, uploading: true, progress: 0, error: null }));

    try {
      const formData = new FormData();
      formData.append('file', state.file);

      // Simulate progress
      const progressInterval = setInterval(() => {
        setState(prev => ({
          ...prev,
          progress: Math.min(prev.progress + 10, 90),
        }));
      }, 200);

      const response = await api.uploadFile(formData);

      clearInterval(progressInterval);

      if (response.success) {
        setState(prev => ({
          ...prev,
          uploading: false,
          progress: 100,
          result: response,
        }));
      } else {
        setState(prev => ({
          ...prev,
          uploading: false,
          progress: 0,
          error: response.error || 'Upload failed. Please try again.',
        }));
      }
    } catch (error) {
      setState(prev => ({
        ...prev,
        uploading: false,
        progress: 0,
        error: error instanceof Error ? error.message : 'Upload failed. Please try again.',
      }));
    }
  };

  const resetUpload = () => {
    setState({
      file: null,
      uploading: false,
      progress: 0,
      error: null,
      result: null,
    });
  };

  return (
    <div className="min-h-screen py-8">
      <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-blue-500 to-cyan-500 flex items-center justify-center mx-auto mb-4">
            <Upload className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-3xl font-bold text-white mb-2">Upload Genetic Data</h1>
          <p className="text-white/60">
            Upload your SNP data file for AI-powered ancestry and trait analysis
          </p>
        </div>

        {/* Upload Card */}
        <Card>
          <CardContent className="p-8">
            {/* Success State */}
            {state.result && (
              <div className="text-center">
                <div className="w-20 h-20 rounded-full bg-green-500/20 flex items-center justify-center mx-auto mb-6">
                  <CheckCircle className="w-10 h-10 text-green-400" />
                </div>
                <h2 className="text-2xl font-bold text-white mb-2">Upload Successful!</h2>
                <p className="text-white/60 mb-6">
                  Your genetic data has been uploaded and is ready for analysis.
                </p>
                
                <div className="glass-card p-4 mb-6 text-left">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <div className="text-sm text-white/60">Sample ID</div>
                      <div className="text-white font-mono">{state.result.sample_id}</div>
                    </div>
                    <div>
                      <div className="text-sm text-white/60">SNPs Detected</div>
                      <div className="text-white font-semibold">{state.result.snp_count?.toLocaleString()}</div>
                    </div>
                  </div>
                </div>

                <div className="flex gap-4 justify-center">
                  <Button onClick={() => window.location.href = `/predictions/${state.result?.sample_id}`}>
                    <Dna className="w-5 h-5" />
                    View Analysis
                  </Button>
                  <Button variant="secondary" onClick={resetUpload}>
                    Upload Another
                  </Button>
                </div>
              </div>
            )}

            {/* Error State */}
            {state.error && !state.result && (
              <div className="mb-6 p-4 rounded-xl bg-red-500/20 border border-red-500/30 flex items-start gap-3">
                <AlertCircle className="w-5 h-5 text-red-400 shrink-0 mt-0.5" />
                <div>
                  <div className="text-red-400 font-medium">Upload Error</div>
                  <div className="text-red-400/80 text-sm">{state.error}</div>
                </div>
                <button onClick={() => setState(prev => ({ ...prev, error: null }))} className="ml-auto">
                  <X className="w-5 h-5 text-red-400" />
                </button>
              </div>
            )}

            {/* Upload Zone */}
            {!state.result && (
              <>
                <div
                  className={cn(
                    'relative border-2 border-dashed rounded-2xl p-12 text-center transition-all duration-300',
                    dragActive
                      ? 'border-primary-500 bg-primary-500/10'
                      : 'border-white/20 hover:border-white/40',
                    state.file && 'border-green-500/50 bg-green-500/5'
                  )}
                  onDragEnter={handleDrag}
                  onDragLeave={handleDrag}
                  onDragOver={handleDrag}
                  onDrop={handleDrop}
                >
                  <input
                    type="file"
                    accept=".csv,.txt,.vcf,.ped"
                    className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                    onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])}
                    disabled={state.uploading}
                  />

                  {state.file ? (
                    <div className="flex flex-col items-center">
                      <div className="w-16 h-16 rounded-xl bg-green-500/20 flex items-center justify-center mb-4">
                        <FileText className="w-8 h-8 text-green-400" />
                      </div>
                      <div className="text-lg font-semibold text-white mb-1">
                        {state.file.name}
                      </div>
                      <div className="text-sm text-white/60">
                        {(state.file.size / 1024 / 1024).toFixed(2)} MB
                      </div>
                    </div>
                  ) : (
                    <div className="flex flex-col items-center">
                      <div className="w-16 h-16 rounded-xl bg-white/10 flex items-center justify-center mb-4">
                        <Upload className="w-8 h-8 text-white/60" />
                      </div>
                      <div className="text-lg font-semibold text-white mb-2">
                        Drag & drop your file here
                      </div>
                      <div className="text-sm text-white/60 mb-4">
                        or click to browse
                      </div>
                      <div className="text-xs text-white/40">
                        Supported formats: CSV, TXT, VCF, PED (max 50MB)
                      </div>
                      {state.file && (state.file as File).name.endsWith('.ped') && (
                        <div className="mt-2 text-xs text-primary-400 flex items-center gap-1">
                          <Info className="w-3 h-3" />
                          PED file will be automatically converted to CSV format
                        </div>
                      )}
                    </div>
                  )}
                </div>

                {/* Progress Bar */}
                {state.uploading && (
                  <div className="mt-6">
                    <div className="flex justify-between text-sm text-white/60 mb-2">
                      <span>Uploading...</span>
                      <span>{state.progress}%</span>
                    </div>
                    <div className="h-2 bg-white/10 rounded-full overflow-hidden relative">
                      <div
                        className="h-full bg-gradient-to-r from-primary-500 to-accent-500 rounded-full transition-all duration-300 relative"
                        style={{ width: `${state.progress}%` }}
                      >
                        <div className="absolute right-0 top-1/2 -translate-y-1/2 w-5 h-5 bg-white rounded-full shadow-lg shadow-primary-500/40"></div>
                      </div>
                    </div>
                  </div>
                )}

                {/* Upload Button */}
                {state.file && !state.uploading && (
                  <div className="mt-6 flex gap-4 justify-center">
                    <Button onClick={handleUpload}>
                      <Upload className="w-5 h-5" />
                      Start Analysis
                    </Button>
                    <Button variant="secondary" onClick={resetUpload}>
                      <X className="w-5 h-5" />
                      Clear
                    </Button>
                  </div>
                )}

                {state.uploading && (
                  <div className="mt-6 flex justify-center">
                    <Loading text="Processing your genetic data..." />
                  </div>
                )}
              </>
            )}
          </CardContent>
        </Card>

        {/* Format Info Section */}
        <div className="mt-8">
          <Card className="p-6">
            <h6 className="text-white font-semibold mb-4 text-center">File Format Requirements</h6>
            <div className="grid md:grid-cols-2 gap-4">
              <div className="format-section p-4 bg-white/5 rounded-lg">
                <h6 className="text-white font-medium mb-2 text-sm">CSV Format</h6>
                <div className="flex flex-wrap gap-2 mb-2">
                  <span className="tag px-2 py-1 bg-primary-500/20 text-primary-300 rounded-full text-xs">rsid</span>
                  <span className="tag px-2 py-1 bg-primary-500/20 text-primary-300 rounded-full text-xs">chromosome</span>
                  <span className="tag px-2 py-1 bg-primary-500/20 text-primary-300 rounded-full text-xs">position</span>
                  <span className="tag px-2 py-1 bg-primary-500/20 text-primary-300 rounded-full text-xs">genotype</span>
                </div>
                <p className="text-xs text-white/60">Required columns for CSV files</p>
              </div>
              <div className="format-section p-4 bg-white/5 rounded-lg">
                <h6 className="text-white font-medium mb-2 text-sm">PED Format</h6>
                <div className="flex flex-wrap gap-2 mb-2">
                  <span className="tag optional px-2 py-1 bg-emerald-500/20 text-emerald-300 rounded-full text-xs">Family ID</span>
                  <span className="tag optional px-2 py-1 bg-emerald-500/20 text-emerald-300 rounded-full text-xs">Individual ID</span>
                  <span className="tag optional px-2 py-1 bg-emerald-500/20 text-emerald-300 rounded-full text-xs">Paternal ID</span>
                  <span className="tag optional px-2 py-1 bg-emerald-500/20 text-emerald-300 rounded-full text-xs">Maternal ID</span>
                  <span className="tag optional px-2 py-1 bg-emerald-500/20 text-emerald-300 rounded-full text-xs">Sex</span>
                  <span className="tag optional px-2 py-1 bg-emerald-500/20 text-emerald-300 rounded-full text-xs">Phenotype</span>
                </div>
                <p className="text-xs text-white/60">PED files will be automatically converted</p>
              </div>
            </div>
          </Card>
        </div>

        {/* Help Section */}
        <div className="mt-6 grid md:grid-cols-3 gap-4">
          <Card className="p-4">
            <h3 className="text-white font-semibold mb-2 flex items-center gap-2">
              <FileText className="w-4 h-4" />
              File Format
            </h3>
            <p className="text-sm text-white/60">
              We accept CSV, PED, TXT, and VCF files with SNP data
            </p>
          </Card>
          <Card className="p-4">
            <h3 className="text-white font-semibold mb-2 flex items-center gap-2">
              <Shield className="w-4 h-4" />
              Privacy
            </h3>
            <p className="text-sm text-white/60">
              Your data is encrypted and processed securely. We never share your genetic information.
            </p>
          </Card>
          <Card className="p-4">
            <h3 className="text-white font-semibold mb-2 flex items-center gap-2">
              <Zap className="w-4 h-4" />
              Fast Analysis
            </h3>
            <p className="text-sm text-white/60">
              Results are typically ready within seconds using our AI-powered analysis.
            </p>
          </Card>
        </div>
      </div>
    </div>
  );
}


