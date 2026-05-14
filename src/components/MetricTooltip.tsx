/**
 * MetricTooltip — A reusable "?" icon with hover tooltip for metric explanations.
 * Usage: <MetricTooltip text="Explanation of this metric." />
 */
import { useState, useRef, useEffect, CSSProperties } from 'react';

interface MetricTooltipProps {
  text: string;
  position?: 'top' | 'bottom' | 'left' | 'right';
}

export function MetricTooltip({ text, position = 'top' }: MetricTooltipProps) {
  const [visible, setVisible] = useState(false);
  const [hovered, setHovered] = useState(false);
  const [tooltipStyle, setTooltipStyle] = useState<CSSProperties>({});
  const triggerRef = useRef<HTMLSpanElement>(null);
  const tooltipRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (visible && triggerRef.current && tooltipRef.current) {
      const trigger = triggerRef.current.getBoundingClientRect();
      const tooltip = tooltipRef.current.getBoundingClientRect();
      const viewport = { w: window.innerWidth, h: window.innerHeight };

      let top = 0, left = 0;

      if (position === 'top') {
        top = trigger.top - tooltip.height - 8;
        left = trigger.left + trigger.width / 2 - tooltip.width / 2;
      } else if (position === 'bottom') {
        top = trigger.bottom + 8;
        left = trigger.left + trigger.width / 2 - tooltip.width / 2;
      } else if (position === 'left') {
        top = trigger.top + trigger.height / 2 - tooltip.height / 2;
        left = trigger.left - tooltip.width - 8;
      } else {
        top = trigger.top + trigger.height / 2 - tooltip.height / 2;
        left = trigger.right + 8;
      }

      // Clamp to viewport
      if (left < 8) left = 8;
      if (left + tooltip.width > viewport.w - 8) left = viewport.w - tooltip.width - 8;
      if (top < 8) top = trigger.bottom + 8;
      if (top + tooltip.height > viewport.h - 8) top = trigger.top - tooltip.height - 8;

      setTooltipStyle({ top, left, position: 'fixed' });
    }
  }, [visible, position]);

  const handleShow = () => setVisible(true);
  const handleHide = () => setVisible(false);

  return (
    <span style={{ display: 'inline-flex', alignItems: 'center', marginLeft: '4px', verticalAlign: 'middle' }}>
      <span
        ref={triggerRef}
        onMouseEnter={() => { handleShow(); setHovered(true); }}
        onMouseLeave={() => { handleHide(); setHovered(false); }}
        onFocus={handleShow}
        onBlur={handleHide}
        tabIndex={0}
        role="button"
        aria-label="More information about this metric"
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          justifyContent: 'center',
          width: '14px',
          height: '14px',
          borderRadius: '50%',
          background: hovered ? '#475569' : '#94a3b8',
          color: '#fff',
          fontSize: '9px',
          fontWeight: 700,
          cursor: 'help',
          flexShrink: 0,
          lineHeight: 1,
          border: 'none',
          outline: 'none',
          transition: 'background 0.15s ease',
          userSelect: 'none',
        }}
      >
        ?
      </span>

      {visible && (
        <div
          ref={tooltipRef}
          role="tooltip"
          style={{
            ...tooltipStyle,
            zIndex: 9999,
            maxWidth: '280px',
            background: '#1e293b',
            color: '#f1f5f9',
            padding: '8px 12px',
            borderRadius: '8px',
            fontSize: '12px',
            lineHeight: '1.6',
            boxShadow: '0 4px 24px rgba(0,0,0,0.35)',
            pointerEvents: 'none',
            fontWeight: 400,
          }}
        >
          {text}
        </div>
      )}
    </span>
  );
}
