import Link from 'next/link'

export default function HomePage() {
  const features = [
    {
      icon: (
        <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" d="M7.5 7.5h-.75A2.25 2.25 0 004.5 9.75v7.5a2.25 2.25 0 002.25 2.25h7.5a2.25 2.25 0 002.25-2.25v-7.5a2.25 2.25 0 00-2.25-2.25h-.75m0-3l-3-3m0 0l-3 3m3-3v11.25m6-2.25h.75a2.25 2.25 0 012.25 2.25v7.5a2.25 2.25 0 01-2.25 2.25h-7.5a2.25 2.25 0 01-2.25-2.25v-7.5a2.25 2.25 0 012.25-2.25H12" />
        </svg>
      ),
      title: 'Upload & Hash',
      description: 'Officials upload result files. The system generates a SHA-256 cryptographic fingerprint.',
    },
    {
      icon: (
        <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" d="M13.19 8.688a4.5 4.5 0 011.242 7.244l-4.5 4.5a4.5 4.5 0 01-6.364-6.364l1.757-1.757m9.86-7.07l4.5-4.5a4.5 4.5 0 016.364 6.364l-1.757 1.757" />
        </svg>
      ),
      title: 'Blockchain Anchor',
      description: 'The fingerprint is stored immutably on Hyperledger Fabric — it can never be altered.',
    },
    {
      icon: (
        <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
        </svg>
      ),
      title: 'Public Verification',
      description: 'Any citizen can verify a result file. If tampered, the hash mismatch is immediately detected.',
    },
  ];

  const stats = [
    { value: 'SHA-256', label: 'Cryptographic Standard' },
    { value: 'Blockchain', label: 'Immutable Ledger' },
    { value: '100%', label: 'Tamper Detection' },
    { value: 'Public', label: 'Open Verification' },
  ];

  return (
    <div className="animate-fade-in">
      {/* Hero */}
      <section className="relative overflow-hidden">
        <div className="max-w-7xl mx-auto px-6 py-24 md:py-32">
          <div className="text-center max-w-4xl mx-auto">
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary-500/10 border border-primary-500/20 text-primary-300 text-sm font-medium mb-8">
              <span className="w-2 h-2 rounded-full bg-primary-400 animate-pulse-slow"></span>
              Post-Count Cryptographic Audit Layer
            </div>

            <h1 className="text-5xl md:text-7xl font-extrabold leading-tight mb-6">
              <span className="text-white">Election Integrity</span>
              <br />
              <span className="bg-clip-text text-transparent bg-gradient-to-r from-primary-400 via-purple-400 to-primary-300">
                Verified by Blockchain
              </span>
            </h1>

            <p className="text-xl text-gray-400 max-w-2xl mx-auto mb-10 leading-relaxed">
              A tamper-proof verification layer that allows anyone to confirm that official 
              election result files have never been altered — powered by SHA-256 hashing 
              and distributed ledger technology.
            </p>

            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link href="/verify" className="btn-primary text-lg px-8 py-4" id="hero-verify-btn">
                Verify a Result
              </Link>
              <Link href="/constituencies" className="btn-secondary text-lg px-8 py-4" id="hero-browse-btn">
                Browse Constituencies
              </Link>
            </div>
          </div>
        </div>

        {/* Decorative glow */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] rounded-full bg-primary-500/5 blur-[120px] pointer-events-none" />
      </section>

      {/* Stats */}
      <section className="max-w-7xl mx-auto px-6 py-8">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
          {stats.map((stat, i) => (
            <div key={i} className="glass-card p-6 text-center animate-slide-up" style={{ animationDelay: `${i * 100}ms` }}>
              <div className="text-2xl md:text-3xl font-bold text-white mb-1">{stat.value}</div>
              <div className="text-sm text-gray-400">{stat.label}</div>
            </div>
          ))}
        </div>
      </section>

      <div className="max-w-7xl mx-auto px-6 py-4">
        <div className="glow-line" />
      </div>

      {/* How It Works */}
      <section className="max-w-7xl mx-auto px-6 py-20">
        <div className="text-center mb-16">
          <h2 className="section-title mb-4">How It Works</h2>
          <p className="text-gray-400 max-w-xl mx-auto">
            Three simple steps ensure every election result is cryptographically verified
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-8">
          {features.map((feature, i) => (
            <div key={i} className="glass-card-hover p-8 animate-slide-up" style={{ animationDelay: `${i * 150}ms` }}>
              <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-primary-500/20 to-primary-700/20 border border-primary-500/30 flex items-center justify-center text-primary-400 mb-6">
                {feature.icon}
              </div>
              <div className="text-sm text-primary-400 font-semibold mb-2">Step {i + 1}</div>
              <h3 className="text-xl font-bold text-white mb-3">{feature.title}</h3>
              <p className="text-gray-400 leading-relaxed">{feature.description}</p>
            </div>
          ))}
        </div>
      </section>

      {/* What This System Does NOT Do */}
      <section className="max-w-7xl mx-auto px-6 py-20">
        <div className="glass-card p-10 md:p-14">
          <h2 className="text-2xl font-bold text-white mb-6 flex items-center gap-3">
            <svg className="w-7 h-7 text-amber-400" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
            </svg>
            Important: Scope Clarification
          </h2>
          <div className="grid md:grid-cols-2 gap-8">
            <div>
              <h3 className="text-accent-400 font-semibold mb-3">✓ This System DOES</h3>
              <ul className="space-y-2 text-gray-300">
                <li className="flex items-start gap-2"><span className="text-accent-400 mt-1">•</span> Verify integrity of official result files</li>
                <li className="flex items-start gap-2"><span className="text-accent-400 mt-1">•</span> Generate cryptographic fingerprints</li>
                <li className="flex items-start gap-2"><span className="text-accent-400 mt-1">•</span> Store hashes on an immutable blockchain</li>
                <li className="flex items-start gap-2"><span className="text-accent-400 mt-1">•</span> Detect any file tampering instantly</li>
              </ul>
            </div>
            <div>
              <h3 className="text-danger-400 font-semibold mb-3">✗ This System Does NOT</h3>
              <ul className="space-y-2 text-gray-300">
                <li className="flex items-start gap-2"><span className="text-danger-400 mt-1">•</span> Replace voting machines</li>
                <li className="flex items-start gap-2"><span className="text-danger-400 mt-1">•</span> Store votes or voter identities</li>
                <li className="flex items-start gap-2"><span className="text-danger-400 mt-1">•</span> Enable online voting</li>
                <li className="flex items-start gap-2"><span className="text-danger-400 mt-1">•</span> Modify election processes</li>
              </ul>
            </div>
          </div>
        </div>
      </section>
    </div>
  )
}
