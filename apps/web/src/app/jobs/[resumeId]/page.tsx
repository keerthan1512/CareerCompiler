'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '../../../components/Button';

export default function JobContextPage({ params }: { params: Promise<{ resumeId: string }> }) {
  const router = useRouter();
  const [jobText, setJobText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async () => {
    if (!jobText.trim()) {
      setError('Please enter a job description.');
      return;
    }

    setIsLoading(true);
    setError(null);
    
    try {
      const resolvedParams = await params;
      const resumeId = resolvedParams.resumeId;

      // 1. Submit the Job Description
      const jobRes = await fetch('/api/job-descriptions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          raw_text: jobText,
          display_name: 'Target Role'
        })
      });

      if (!jobRes.ok) throw new Error('Failed to upload job description');
      
      const jobData = await jobRes.json();
      const jobId = jobData.id;

      // 2. We navigate to the tailor dashboard, which will handle the polling and TailoringPlan creation!
      // Actually, let's create the TailoringPlan here, then navigate with planId, 
      // OR navigate with jobId and let the dashboard create the plan.
      // We will navigate with jobId, so the dashboard can handle creating the plan and compilation doc.
      router.push(`/tailor/${resumeId}/${jobId}`);

    } catch (err: any) {
      setError(err.message || 'An error occurred');
      setIsLoading(false);
    }
  };

  return (
    <div className="container animate-fade-in" style={{ maxWidth: '800px', marginTop: '2rem' }}>
      <div style={{ marginBottom: '2rem' }}>
        <h1 style={{ fontSize: '2.5rem', fontWeight: 700, marginBottom: '0.5rem' }}>
          Target <span className="text-gradient">Job Description</span>
        </h1>
        <p style={{ color: 'var(--color-text-muted)' }}>
          Paste the job description of the role you're applying for. We'll analyze it to find the key requirements and tailor your resume to match.
        </p>
      </div>

      <div className="glass-panel" style={{ padding: '2rem' }}>
        <textarea 
          placeholder="Paste job description here..."
          value={jobText}
          onChange={(e) => setJobText(e.target.value)}
          style={{
            width: '100%',
            height: '300px',
            background: 'rgba(0,0,0,0.2)',
            border: '1px solid var(--color-border)',
            borderRadius: 'var(--radius-sm)',
            padding: '1rem',
            color: 'var(--color-text)',
            fontFamily: 'inherit',
            fontSize: '1rem',
            resize: 'vertical',
            outline: 'none',
            marginBottom: '1.5rem',
          }}
          disabled={isLoading}
        />
        
        {error && (
          <div style={{ color: 'var(--color-error)', marginBottom: '1rem', fontSize: '0.9rem' }}>
            {error}
          </div>
        )}

        <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
          <Button onClick={handleSubmit} isLoading={isLoading}>
            Analyze & Tailor
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="5" y1="12" x2="19" y2="12" />
              <polyline points="12 5 19 12 12 19" />
            </svg>
          </Button>
        </div>
      </div>
    </div>
  );
}
