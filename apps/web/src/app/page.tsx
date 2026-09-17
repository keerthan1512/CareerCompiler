'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Dropzone } from '../components/Dropzone';
import { Button } from '../components/Button';

export default function Home() {
  const router = useRouter();
  const [file, setFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleUpload = async () => {
    if (!file) return;
    
    setIsUploading(true);
    setError(null);
    
    try {
      const formData = new FormData();
      formData.append('pdf_file', file);
      formData.append('display_name', file.name || 'Master Resume');

      const response = await fetch('/api/master-resumes', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`Upload failed: ${response.statusText}`);
      }

      const data = await response.json();
      const resumeId = data.id;
      
      // Navigate to the job context page
      router.push(`/jobs/${resumeId}`);
      
    } catch (err: any) {
      setError(err.message || 'An error occurred during upload');
      setIsUploading(false);
    }
  };

  return (
    <div className="container animate-fade-in" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: 'calc(100vh - 120px)' }}>
      <div style={{ textAlign: 'center', maxWidth: '600px', marginBottom: '3rem' }}>
        <h1 style={{ fontSize: '3rem', fontWeight: 700, marginBottom: '1rem', lineHeight: 1.1 }}>
          Engineer Your <br/><span className="text-gradient">Perfect Resume</span>
        </h1>
        <p style={{ fontSize: '1.1rem', color: 'var(--color-text-muted)' }}>
          Upload your master resume PDF. Our AI will analyze your experience and generate a tailored, ATS-friendly document for any job description.
        </p>
      </div>

      <div style={{ width: '100%', maxWidth: '600px' }}>
        <Dropzone 
          onFileAccepted={setFile} 
          isLoading={isUploading} 
        />
        
        {file && (
          <div className="glass-panel animate-fade-in" style={{ marginTop: '1.5rem', padding: '1rem 1.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="var(--color-primary)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                <polyline points="14 2 14 8 20 8" />
                <line x1="16" y1="13" x2="8" y2="13" />
                <line x1="16" y1="17" x2="8" y2="17" />
                <polyline points="10 9 9 9 8 9" />
              </svg>
              <div>
                <div style={{ fontWeight: 500 }}>{file.name}</div>
                <div style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>{(file.size / 1024 / 1024).toFixed(2)} MB</div>
              </div>
            </div>
            <Button onClick={handleUpload} isLoading={isUploading}>
              Continue
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <line x1="5" y1="12" x2="19" y2="12" />
                <polyline points="12 5 19 12 12 19" />
              </svg>
            </Button>
          </div>
        )}
        
        {error && (
          <div style={{ marginTop: '1rem', color: 'var(--color-error)', textAlign: 'center', fontSize: '0.9rem' }}>
            {error}
          </div>
        )}
      </div>
    </div>
  );
}
