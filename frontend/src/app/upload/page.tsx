'use client';

import { useState } from 'react';
import { api } from '@/lib/api';

export default function UploadPage() {
  const [file, setFile] = useState<File | null>(null);
  const [constituencyId, setConstituencyId] = useState('');
  const [electionDate, setElectionDate] = useState('');
  const [electionType, setElectionType] = useState('');
  const [loading, setLoading] = useState(false);
  const [step, setStep] = useState<'upload'|'hash'|'blockchain'|'done'>('upload');
  const [resultFileId, setResultFileId] = useState('');
  const [hashRecordId, setHashRecordId] = useState('');
  const [generatedHash, setGeneratedHash] = useState('');
  const [txId, setTxId] = useState('');
  const [error, setError] = useState('');

  async function handleUpload() {
    if (!file || !constituencyId || !electionDate || !electionType) { setError('Fill all fields'); return; }
    setError(''); setLoading(true);
    try {
      const r = await api.uploadResult(file, constituencyId, electionDate, electionType);
      setResultFileId(r.id); setStep('hash');
    } catch (e: any) { setError(e.message); } finally { setLoading(false); }
  }

  async function handleHash() {
    setError(''); setLoading(true);
    try {
      const r: any = await api.generateHash(resultFileId);
      setHashRecordId(r.id); setGeneratedHash(r.sha256_hash); setStep('blockchain');
    } catch (e: any) { setError(e.message); } finally { setLoading(false); }
  }

  async function handleStore() {
    setError(''); setLoading(true);
    try {
      const r: any = await api.storeHash(hashRecordId);
      setTxId(r.blockchain_tx_id); setStep('done');
    } catch (e: any) { setError(e.message); } finally { setLoading(false); }
  }

  const steps = [{ k:'upload',l:'Upload',n:1 }, { k:'hash',l:'Hash',n:2 }, { k:'blockchain',l:'Chain',n:3 }, { k:'done',l:'Done',n:4 }];
  const ci = steps.findIndex(s => s.k === step);

  return (
    <div className="max-w-3xl mx-auto px-6 py-12 animate-fade-in">
      <div className="text-center mb-12">
        <h1 className="section-title text-4xl mb-4">Upload Result File</h1>
        <p className="text-gray-400 max-w-xl mx-auto">Officials: upload files, generate hashes, anchor on blockchain.</p>
        <div className="inline-flex items-center gap-2 mt-4 px-4 py-2 rounded-full bg-amber-500/10 border border-amber-500/20 text-amber-300 text-sm">🔒 Authentication required</div>
      </div>

      {/* Progress */}
      <div className="flex items-center justify-between mb-12">
        {steps.map((s, i) => (
          <div key={s.k} className="flex items-center">
            <div className="flex flex-col items-center">
              <div className={`w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold transition-all ${i <= ci ? 'bg-gradient-to-br from-primary-500 to-primary-700 text-white shadow-lg shadow-primary-500/30' : 'bg-gray-800 text-gray-500 border border-gray-700'}`}>
                {i < ci ? '✓' : s.n}
              </div>
              <span className={`text-xs mt-2 ${i <= ci ? 'text-primary-300' : 'text-gray-600'}`}>{s.l}</span>
            </div>
            {i < steps.length - 1 && <div className={`w-16 md:w-24 h-0.5 mx-2 ${i < ci ? 'bg-primary-500' : 'bg-gray-800'}`} />}
          </div>
        ))}
      </div>

      {error && <div className="glass-card p-4 mb-6 border-danger-500/30 bg-danger-500/5"><p className="text-danger-400 text-sm">⚠ {error}</p></div>}

      {step === 'upload' && (
        <div className="glass-card p-8 animate-slide-up">
          <h2 className="text-xl font-bold text-white mb-6">Step 1: Upload Result File</h2>
          <div className="space-y-5">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">File *</label>
              <input type="file" onChange={(e) => setFile(e.target.files?.[0] || null)} className="w-full file:mr-4 file:py-2.5 file:px-5 file:rounded-xl file:border-0 file:bg-primary-600 file:text-white file:font-semibold input-field" id="upload-file-input" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Constituency ID *</label>
              <input type="text" value={constituencyId} onChange={(e) => setConstituencyId(e.target.value)} placeholder="UUID" className="input-field" id="constituency-input" />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Date *</label>
                <input type="date" value={electionDate} onChange={(e) => setElectionDate(e.target.value)} className="input-field" id="date-input" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Type *</label>
                <select value={electionType} onChange={(e) => setElectionType(e.target.value)} className="input-field" id="type-input">
                  <option value="">Select...</option>
                  <option value="General">General</option>
                  <option value="State">State</option>
                  <option value="ByElection">By-Election</option>
                  <option value="Municipal">Municipal</option>
                </select>
              </div>
            </div>
            <button onClick={handleUpload} disabled={loading || !file} className="btn-primary w-full py-4 disabled:opacity-40" id="upload-btn">{loading ? 'Uploading...' : 'Upload File'}</button>
          </div>
        </div>
      )}

      {step === 'hash' && (
        <div className="glass-card p-8 animate-slide-up">
          <h2 className="text-xl font-bold text-white mb-4">Step 2: Generate SHA-256</h2>
          <div className="mb-6 p-4 bg-gray-800/50 rounded-xl"><span className="text-xs text-gray-500">File ID</span><p className="font-mono text-sm text-primary-300 mt-1">{resultFileId}</p></div>
          <button onClick={handleHash} disabled={loading} className="btn-primary w-full py-4 disabled:opacity-40" id="hash-btn">{loading ? 'Generating...' : 'Generate Hash'}</button>
        </div>
      )}

      {step === 'blockchain' && (
        <div className="glass-card p-8 animate-slide-up">
          <h2 className="text-xl font-bold text-white mb-4">Step 3: Store on Blockchain</h2>
          <div className="mb-6 p-4 bg-gray-800/50 rounded-xl"><span className="text-xs text-gray-500">SHA-256</span><p className="hash-display mt-2">{generatedHash}</p></div>
          <button onClick={handleStore} disabled={loading} className="btn-primary w-full py-4 disabled:opacity-40" id="store-btn">{loading ? 'Submitting...' : 'Store on Blockchain'}</button>
        </div>
      )}

      {step === 'done' && (
        <div className="glass-card p-8 text-center animate-slide-up border-accent-500/30">
          <div className="w-16 h-16 rounded-2xl bg-accent-500/20 flex items-center justify-center mx-auto mb-6">
            <svg className="w-8 h-8 text-accent-400" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
          </div>
          <h2 className="text-2xl font-bold text-white mb-2">Anchored on Blockchain!</h2>
          <p className="text-gray-400 mb-8">Hash immutably stored.</p>
          <div className="space-y-3 text-left max-w-md mx-auto">
            <div className="p-4 bg-gray-800/50 rounded-xl"><span className="text-xs text-gray-500">Hash</span><p className="hash-display mt-2 text-xs">{generatedHash}</p></div>
            <div className="p-4 bg-gray-800/50 rounded-xl"><span className="text-xs text-gray-500">TX ID</span><p className="hash-display mt-2 text-xs">{txId}</p></div>
          </div>
        </div>
      )}
    </div>
  );
}
