'use client';

import { useState, useEffect } from 'react';
import { api, Constituency } from '@/lib/api';

export default function ConstituenciesPage() {
  const [constituencies, setConstituencies] = useState<Constituency[]>([]);
  const [filterState, setFilterState] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    loadConstituencies();
  }, []);

  async function loadConstituencies() {
    setLoading(true);
    try {
      const data = await api.getConstituencies();
      setConstituencies(data);
    } catch (err: any) {
      setError(err.message);
      // Demo data for when API is not available
      setConstituencies([
        { id: '1', name: 'New Delhi', code: 'DL-001', state: 'Delhi', district: 'Central Delhi', country: 'India', total_registered_voters: 156000, created_at: new Date().toISOString() },
        { id: '2', name: 'Varanasi', code: 'UP-001', state: 'Uttar Pradesh', district: 'Varanasi', country: 'India', total_registered_voters: 189000, created_at: new Date().toISOString() },
        { id: '3', name: 'Mumbai South', code: 'MH-001', state: 'Maharashtra', district: 'Mumbai', country: 'India', total_registered_voters: 210000, created_at: new Date().toISOString() },
        { id: '4', name: 'Chennai Central', code: 'TN-001', state: 'Tamil Nadu', district: 'Chennai', country: 'India', total_registered_voters: 175000, created_at: new Date().toISOString() },
        { id: '5', name: 'Kolkata North', code: 'WB-001', state: 'West Bengal', district: 'Kolkata', country: 'India', total_registered_voters: 195000, created_at: new Date().toISOString() },
        { id: '6', name: 'Bangalore South', code: 'KA-001', state: 'Karnataka', district: 'Bangalore Urban', country: 'India', total_registered_voters: 220000, created_at: new Date().toISOString() },
      ]);
    } finally {
      setLoading(false);
    }
  }

  const states = [...new Set(constituencies.map((c) => c.state))].sort();
  
  const filtered = constituencies.filter((c) => {
    const matchesState = !filterState || c.state === filterState;
    const matchesSearch = !searchTerm || 
      c.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      c.code.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesState && matchesSearch;
  });

  return (
    <div className="max-w-7xl mx-auto px-6 py-12 animate-fade-in">
      <div className="text-center mb-12">
        <h1 className="section-title text-4xl mb-4">Constituencies</h1>
        <p className="text-gray-400 max-w-xl mx-auto">
          Browse all registered constituencies and their election data
        </p>
      </div>

      {/* Filters */}
      <div className="glass-card p-6 mb-8">
        <div className="grid md:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs text-gray-500 uppercase tracking-wider mb-2">Search</label>
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search by name or code..."
              className="input-field"
              id="constituency-search"
            />
          </div>
          <div>
            <label className="block text-xs text-gray-500 uppercase tracking-wider mb-2">Filter by State</label>
            <select
              value={filterState}
              onChange={(e) => setFilterState(e.target.value)}
              className="input-field"
              id="state-filter"
            >
              <option value="">All States</option>
              {states.map((state) => (
                <option key={state} value={state}>{state}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Results Count */}
      <div className="flex items-center justify-between mb-6">
        <p className="text-sm text-gray-400">
          Showing <span className="text-white font-semibold">{filtered.length}</span> constituencies
        </p>
      </div>

      {/* Grid */}
      {loading ? (
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div key={i} className="glass-card p-6 animate-pulse">
              <div className="h-4 bg-gray-800 rounded w-3/4 mb-4" />
              <div className="h-3 bg-gray-800 rounded w-1/2 mb-3" />
              <div className="h-3 bg-gray-800 rounded w-2/3" />
            </div>
          ))}
        </div>
      ) : (
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filtered.map((constituency, i) => (
            <div
              key={constituency.id}
              className="glass-card-hover p-6 animate-slide-up"
              style={{ animationDelay: `${i * 50}ms` }}
            >
              <div className="flex items-start justify-between mb-4">
                <div>
                  <h3 className="text-lg font-bold text-white">{constituency.name}</h3>
                  <p className="text-sm text-primary-400 font-mono">{constituency.code}</p>
                </div>
                <div className="w-10 h-10 rounded-lg bg-primary-500/10 flex items-center justify-center">
                  <svg className="w-5 h-5 text-primary-400" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M15 10.5a3 3 0 11-6 0 3 3 0 016 0z" />
                    <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 10.5c0 7.142-7.5 11.25-7.5 11.25S4.5 17.642 4.5 10.5a7.5 7.5 0 1115 0z" />
                  </svg>
                </div>
              </div>

              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-500">State</span>
                  <span className="text-gray-300">{constituency.state}</span>
                </div>
                {constituency.district && (
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-500">District</span>
                    <span className="text-gray-300">{constituency.district}</span>
                  </div>
                )}
                {constituency.total_registered_voters && (
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-500">Registered Voters</span>
                    <span className="text-gray-300 font-semibold">
                      {constituency.total_registered_voters.toLocaleString()}
                    </span>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {filtered.length === 0 && !loading && (
        <div className="glass-card p-12 text-center">
          <p className="text-gray-400">No constituencies found matching your criteria.</p>
        </div>
      )}
    </div>
  );
}
