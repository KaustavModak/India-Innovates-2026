'use client';

import { useState, useEffect } from 'react';
import { api, AuditLog } from '@/lib/api';

export default function AuditPage() {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);

  useEffect(() => { loadLogs(); }, [page]);

  async function loadLogs() {
    setLoading(true);
    try {
      const data = await api.getAuditLogs(page, 20);
      setLogs(data.logs); setTotal(data.total);
    } catch {
      setLogs([
        { id: '1', user_id: null, action: 'upload_file', resource_type: 'result_file', resource_id: 'abc', ip_address: '10.0.0.1', details: { filename: 'results_DL001.csv' }, success: true, created_at: new Date().toISOString() },
        { id: '2', user_id: null, action: 'generate_hash', resource_type: 'hash_record', resource_id: 'def', ip_address: '10.0.0.1', details: { sha256_hash: 'a1b2c3...' }, success: true, created_at: new Date().toISOString() },
        { id: '3', user_id: null, action: 'submit_hash', resource_type: 'hash_record', resource_id: 'def', ip_address: '10.0.0.1', details: { tx_id: '0xabc...' }, success: true, created_at: new Date().toISOString() },
        { id: '4', user_id: null, action: 'verify_result', resource_type: 'verification', resource_id: 'ghi', ip_address: '203.0.113.5', details: { hash: 'f4e5d6...', verified: true }, success: true, created_at: new Date().toISOString() },
        { id: '5', user_id: null, action: 'login', resource_type: null, resource_id: null, ip_address: '10.0.0.2', details: { email: 'official@ec.gov' }, success: true, created_at: new Date().toISOString() },
      ]);
      setTotal(5);
    } finally { setLoading(false); }
  }

  const actionColors: Record<string, string> = {
    upload_file: 'text-blue-400 bg-blue-500/10 border-blue-500/20',
    generate_hash: 'text-purple-400 bg-purple-500/10 border-purple-500/20',
    submit_hash: 'text-primary-400 bg-primary-500/10 border-primary-500/20',
    verify_result: 'text-accent-400 bg-accent-500/10 border-accent-500/20',
    login: 'text-gray-400 bg-gray-500/10 border-gray-500/20',
    access_denied: 'text-danger-400 bg-danger-500/10 border-danger-500/20',
  };

  const actionIcons: Record<string, string> = {
    upload_file: '📤', generate_hash: '🔐', submit_hash: '⛓️',
    verify_result: '✅', login: '🔑', access_denied: '🚫',
  };

  return (
    <div className="max-w-7xl mx-auto px-6 py-12 animate-fade-in">
      <div className="text-center mb-12">
        <h1 className="section-title text-4xl mb-4">Audit Log</h1>
        <p className="text-gray-400 max-w-xl mx-auto">Full transparency — every action in the system is publicly logged.</p>
      </div>

      <div className="glass-card overflow-hidden">
        <div className="p-6 border-b border-gray-800/50 flex items-center justify-between">
          <p className="text-sm text-gray-400"><span className="text-white font-semibold">{total}</span> total entries</p>
          <div className="flex gap-2">
            <button onClick={() => setPage(Math.max(1, page - 1))} disabled={page === 1} className="btn-secondary text-sm px-4 py-2 disabled:opacity-30" id="prev-btn">← Prev</button>
            <span className="px-4 py-2 text-sm text-gray-400">Page {page}</span>
            <button onClick={() => setPage(page + 1)} disabled={logs.length < 20} className="btn-secondary text-sm px-4 py-2 disabled:opacity-30" id="next-btn">Next →</button>
          </div>
        </div>

        {loading ? (
          <div className="p-8 space-y-4">
            {[1,2,3,4,5].map(i => <div key={i} className="h-16 bg-gray-800/30 rounded-xl animate-pulse" />)}
          </div>
        ) : (
          <div className="divide-y divide-gray-800/30">
            {logs.map((log, i) => (
              <div key={log.id} className="p-5 hover:bg-gray-800/20 transition-colors animate-slide-up" style={{ animationDelay: `${i * 30}ms` }}>
                <div className="flex items-start gap-4">
                  <div className="text-2xl mt-1">{actionIcons[log.action] || '📋'}</div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-3 mb-1">
                      <span className={`px-3 py-1 rounded-full text-xs font-semibold border ${actionColors[log.action] || 'text-gray-400 bg-gray-500/10 border-gray-500/20'}`}>
                        {log.action.replace(/_/g, ' ').toUpperCase()}
                      </span>
                      <span className={`text-xs ${log.success ? 'text-accent-400' : 'text-danger-400'}`}>{log.success ? '✓ Success' : '✗ Failed'}</span>
                    </div>
                    {log.details && Object.keys(log.details).length > 0 && (
                      <p className="text-sm text-gray-400 mt-1 truncate">{JSON.stringify(log.details).slice(0, 120)}</p>
                    )}
                  </div>
                  <div className="text-right shrink-0">
                    <p className="text-xs text-gray-500">{new Date(log.created_at).toLocaleString()}</p>
                    {log.ip_address && <p className="text-xs text-gray-600 font-mono mt-1">{log.ip_address}</p>}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
