import React from 'react';

export type StepStatus = 'pending' | 'running' | 'complete' | 'failed';

interface Step {
  id: string;
  label: string;
  status: StepStatus;
  description?: string;
}

interface ProgressStepsProps {
  steps: Step[];
}

export const ProgressSteps: React.FC<ProgressStepsProps> = ({ steps }) => {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem', width: '100%' }}>
      {steps.map((step, index) => {
        const isLast = index === steps.length - 1;
        
        let iconColor = 'var(--color-border)';
        let iconBg = 'transparent';
        if (step.status === 'complete') {
          iconColor = 'var(--color-success)';
          iconBg = 'rgba(16, 185, 129, 0.1)';
        } else if (step.status === 'running') {
          iconColor = 'var(--color-primary)';
          iconBg = 'rgba(139, 92, 246, 0.1)';
        } else if (step.status === 'failed') {
          iconColor = 'var(--color-error)';
          iconBg = 'rgba(239, 68, 68, 0.1)';
        }

        return (
          <div key={step.id} style={{ display: 'flex', gap: '1rem', position: 'relative' }}>
            {!isLast && (
              <div style={{
                position: 'absolute',
                left: '11px',
                top: '32px',
                bottom: '-24px',
                width: '2px',
                background: step.status === 'complete' ? 'var(--color-success)' : 'var(--color-border)',
                transition: 'all 0.3s ease'
              }} />
            )}
            
            <div style={{
              width: '24px',
              height: '24px',
              borderRadius: '50%',
              background: iconBg,
              border: `2px solid ${iconColor}`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexShrink: 0,
              zIndex: 1,
              transition: 'all 0.3s ease',
              marginTop: '4px'
            }}>
              {step.status === 'complete' && (
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" style={{ color: iconColor }}>
                  <polyline points="20 6 9 17 4 12" />
                </svg>
              )}
              {step.status === 'running' && (
                <div style={{
                  width: '8px',
                  height: '8px',
                  borderRadius: '50%',
                  background: 'var(--color-primary)',
                  animation: 'pulseGlow 2s infinite'
                }} />
              )}
              {step.status === 'failed' && (
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" style={{ color: iconColor }}>
                  <line x1="18" y1="6" x2="6" y2="18" />
                  <line x1="6" y1="6" x2="18" y2="18" />
                </svg>
              )}
            </div>
            
            <div style={{ flex: 1, opacity: step.status === 'pending' ? 0.5 : 1, transition: 'all 0.3s ease' }}>
              <div style={{ fontWeight: 600, fontSize: '1.1rem', color: step.status === 'running' ? 'var(--color-primary)' : 'var(--color-text)' }}>
                {step.label}
              </div>
              {step.description && (
                <div style={{ color: 'var(--color-text-muted)', fontSize: '0.9rem', marginTop: '0.25rem' }}>
                  {step.description}
                </div>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
};
