/**
 * Generic Glass Card Component
 * Provides glassmorphism effect with hover animations
 */
import React from 'react';

interface GlassCardProps {
  children: React.ReactNode;
  className?: string;
  style?: React.CSSProperties;
  hoverable?: boolean;
  onClick?: () => void;
  padding?: number | string;
  borderRadius?: number;
}

const GlassCard: React.FC<GlassCardProps> = ({
  children,
  className = '',
  style = {},
  hoverable = true,
  onClick,
  padding = 16,
  borderRadius = 16,
}) => {
  return (
    <div
      className={`dash-glass-card ${className}`}
      onClick={onClick}
      style={{
        padding,
        borderRadius,
        cursor: onClick ? 'pointer' : 'default',
        ...(!hoverable && {
          transform: 'none',
          transition: 'none',
        }),
        ...style,
      }}
    >
      {children}
    </div>
  );
};

export default GlassCard;
