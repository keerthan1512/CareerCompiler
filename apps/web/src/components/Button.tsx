import React from 'react';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline';
  isLoading?: boolean;
}

export const Button: React.FC<ButtonProps> = ({ 
  children, 
  variant = 'primary', 
  isLoading, 
  style, 
  ...props 
}) => {
  const baseStyle: React.CSSProperties = {
    padding: '0.75rem 1.5rem',
    borderRadius: 'var(--radius-sm)',
    fontWeight: 600,
    fontSize: '0.95rem',
    cursor: props.disabled || isLoading ? 'not-allowed' : 'pointer',
    opacity: props.disabled || isLoading ? 0.7 : 1,
    transition: 'all 0.2s ease',
    border: 'none',
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '0.5rem',
    fontFamily: 'var(--font-sans)',
  };

  const variants: Record<string, React.CSSProperties> = {
    primary: {
      background: 'linear-gradient(135deg, var(--color-primary), var(--color-secondary))',
      color: '#fff',
      boxShadow: '0 4px 14px 0 rgba(139, 92, 246, 0.39)',
    },
    secondary: {
      background: 'var(--color-surface)',
      color: 'var(--color-text)',
      border: '1px solid var(--color-border)',
    },
    outline: {
      background: 'transparent',
      color: 'var(--color-primary)',
      border: '1px solid var(--color-primary)',
    }
  };

  return (
    <button 
      style={{ ...baseStyle, ...variants[variant], ...style }} 
      disabled={isLoading || props.disabled}
      onMouseOver={(e) => {
        if (props.disabled || isLoading) return;
        if (variant === 'primary') {
          e.currentTarget.style.transform = 'translateY(-1px)';
          e.currentTarget.style.boxShadow = '0 6px 20px rgba(139, 92, 246, 0.5)';
        } else {
          e.currentTarget.style.background = 'var(--color-surface-hover)';
        }
      }}
      onMouseOut={(e) => {
        if (props.disabled || isLoading) return;
        if (variant === 'primary') {
          e.currentTarget.style.transform = 'translateY(0)';
          e.currentTarget.style.boxShadow = '0 4px 14px 0 rgba(139, 92, 246, 0.39)';
        } else {
          e.currentTarget.style.background = variants[variant].background as string;
        }
      }}
      {...props}
    >
      {isLoading && (
        <span style={{ 
          width: '16px', 
          height: '16px', 
          border: '2px solid rgba(255,255,255,0.3)', 
          borderTopColor: '#fff', 
          borderRadius: '50%', 
          animation: 'spin 1s linear infinite' 
        }} />
      )}
      {children}
    </button>
  );
};
