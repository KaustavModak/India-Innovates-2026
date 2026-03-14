'use client';

import { useState } from 'react';
import { api, VerificationResult } from '@/lib/api';

export default function VerifyPage() {
  const [hash, setHash] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<VerificationResult | null>(null);
  const [error, setError] = useState('');
  const [mode, setMode] = useState<'hash' | 'file'>('file');

  /**
   * Compute SHA-256 hash of a file in the browser using Web Crypto API.
   */
  async function computeClientHash(file: File): Promise<string> {
    const buffer = await file.arrayBuffer();
    const hashBuffer = await crypto.subtle.digest('SHA-256', buffer);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    return hashArray.map((b) => b.toString(16).padStart(2, '0')).join('');
  }

  async function handleVerify() {
    setError('');
    setResult(null);
    setLoading(true);

    try {
      let fileHash = hash.trim().toLowerCase();

      if (mode === 'file' && file) {
        fileHash = await computeClientHash(file);
        setHash(fileHash);
      }

      if (!fileHash || fileHash.length !== 64) {
        setError('Please provide a valid SHA-256 hash (64 hex characters)');
        return;
      }

      const verificationResult = await api.verifyResult(fileHash);
      setResult(verificationResult);
    } catch (err: any) {
      setError(err.message || 'Verification failed');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-4xl mx-auto px-6 py-12 animate-fade-in">
      <div className="text-center mb-12">
        <h1 className="section-title text-4xl mb-4">Verify Election Results</h1>
        <p className="text-gray-400 max-w-xl mx-auto">
          Upload a result file or paste its SHA-256 hash to verify that it matches the 
          official record stored on the blockchain.
        </p>
      </div>

      {/* Mode Toggle */}
      <div className="glass-card p-8 mb-8">
        <div className="flex gap-2 mb-8 bg-gray-800/50 rounded-xl p-1">
          <button
            onClick={() => setMode('file')}
            className={`flex-1 py-3 rounded-lg text-sm font-semibold transition-all duration-300 ${
              mode === 'file'
                ? 'bg-primary-600 text-white shadow-lg shadow-primary-500/20'
                : 'text-gray-400 hover:text-gray-200'
            }`}
            id="mode-file-btn"
          >
            Upload File
          </button>
          <button
            onClick={() => setMode('hash')}
            className={`flex-1 py-3 rounded-lg text-sm font-semibold transition-all duration-300 ${
              mode === 'hash'
                ? 'bg-primary-600 text-white shadow-lg shadow-primary-500/20'
                : 'text-gray-400 hover:text-gray-200'
            }`}
            id="mode-hash-btn"
          >
            Paste Hash
          </button>
        </div>

        {mode === 'file' ? (
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-300 mb-3">
              Upload Result File
            </label>
            <div className="relative">
              <input
                type="file"
                onChange={(e) => setFile(e.target.files?.[0] || null)}
                className="w-full file:mr-4 file:py-3 file:px-6 file:rounded-xl file:border-0 file:bg-primary-600 file:text-white file:font-semibold file:cursor-pointer cursor-pointer input-field"
                id="file-input"
              />
            </div>
            {file && (
              <p className="mt-3 text-sm text-gray-400">
                Selected: <span className="text-gray-200">{file.name}</span> ({(file.size / 1024).toFixed(1)} KB)
              </p>
            )}
          </div>
        ) : (
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-300 mb-3">
              SHA-256 Hash
            </label>
            <input
              type="text"
              value={hash}
              onChange={(e) => setHash(e.target.value)}
              placeholder="e.g. a1b2c3d4e5f6..."
              className="input-field font-mono text-sm"
              maxLength={64}
              id="hash-input"
            />
            <p className="mt-2 text-xs text-gray-500">{hash.length}/64 characters</p>
          </div>
        )}

        <button
          onClick={handleVerify}
          disabled={loading || (mode === 'file' ? !file : hash.length !== 64)}
          className="btn-primary w-full py-4 text-lg disabled:opacity-40 disabled:cursor-not-allowed"
          id="verify-btn"
        >
          {loading ? (
            <span className="flex items-center justify-center gap-3">
              <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
              Verifying...
            </span>
          ) : (
            'Verify Integrity'
          )}
        </button>
      </div>

      {/* Error */}
      {error && (
        <div className="glass-card p-6 mb-8 border-danger-500/30 bg-danger-500/5 animate-slide-up" id="error-display">
          <p className="text-danger-400 font-medium">⚠ {error}</p>
        </div>
      )}

      {/* Result */}
      {result && (
        <div className="animate-slide-up" id="verification-result">
          {/* Status Banner */}
          <div className={`glass-card p-8 mb-6 ${
            result.is_verified 
              ? 'border-accent-500/30' 
              : 'border-danger-500/30'
          }`}>
            <div className="flex items-center gap-4 mb-4">
              {result.is_verified ? (
                <div className="w-16 h-16 rounded-2xl bg-accent-500/20 flex items-center justify-center">
                  <svg className="w-8 h-8 text-accent-400" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
              ) : (
                <div className="w-16 h-16 rounded-2xl bg-danger-500/20 flex items-center justify-center">
                  <svg className="w-8 h-8 text-danger-400" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
                  </svg>
                </div>
              )}
              <div>
                <div className={result.is_verified ? 'status-verified' : 'status-tampered'}>
                  {result.is_verified ? '✓ VERIFIED — Integrity Confirmed' : '✗ NOT VERIFIED — Possible Tampering'}
                </div>
              </div>
            </div>

            <div className="space-y-4 mt-6">
              <div>
                <span className="text-xs text-gray-500 uppercase tracking-wider">Submitted Hash</span>
                <div className="hash-display mt-1">{result.submitted_hash}</div>
              </div>

              {result.blockchain_verified && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <span className="text-xs text-gray-500 uppercase tracking-wider">Blockchain TX</span>
                    <div className="hash-display mt-1 text-xs">{result.blockchain_tx_id || 'N/A'}</div>
                  </div>
                  <div>
                    <span className="text-xs text-gray-500 uppercase tracking-wider">Status</span>
                    <p className="text-accent-400 font-semibold mt-1">On-chain ✓</p>
                  </div>
                </div>
              )}

              {result.result_details?.constituency && (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-4 border-t border-gray-800/50">
                  <div>
                    <span className="text-xs text-gray-500 uppercase tracking-wider">Constituency</span>
                    <p className="text-gray-200 font-medium mt-1">{result.result_details.constituency}</p>
                  </div>
                  <div>
                    <span className="text-xs text-gray-500 uppercase tracking-wider">Election Date</span>
                    <p className="text-gray-200 font-medium mt-1">{result.result_details.election_date}</p>
                  </div>
                  <div>
                    <span className="text-xs text-gray-500 uppercase tracking-wider">Election Type</span>
                    <p className="text-gray-200 font-medium mt-1">{result.result_details.election_type}</p>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
