import React, { useEffect, useId, useRef } from 'react';
import { X } from 'lucide-react';

interface ModalProps {
  open: boolean;
  title: string;
  subtitle?: string;
  onClose: () => void;
  children: React.ReactNode;
}

const FOCUSABLE_SELECTOR =
  'a[href], button:not([disabled]), textarea:not([disabled]), input:not([disabled]), select:not([disabled]), [tabindex]:not([tabindex="-1"])';

export const Modal: React.FC<ModalProps> = ({ open, title, subtitle, onClose, children }) => {
  const titleId = useId();
  const subtitleId = useId();
  const cardRef = useRef<HTMLDivElement>(null);
  const previousFocusRef = useRef<HTMLElement | null>(null);

  useEffect(() => {
    if (!open) return;

    previousFocusRef.current = document.activeElement as HTMLElement | null;

    const card = cardRef.current;
    if (card) {
      const focusables = card.querySelectorAll<HTMLElement>(FOCUSABLE_SELECTOR);
      if (focusables.length > 0) {
        focusables[0].focus();
      } else {
        card.focus();
      }
    }

    const handleKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        e.preventDefault();
        onClose();
        return;
      }

      if (e.key === 'Tab' && cardRef.current) {
        const focusables = Array.from(
          cardRef.current.querySelectorAll<HTMLElement>(FOCUSABLE_SELECTOR)
        );
        if (focusables.length === 0) {
          e.preventDefault();
          cardRef.current.focus();
          return;
        }
        const first = focusables[0];
        const last = focusables[focusables.length - 1];
        if (e.shiftKey) {
          if (document.activeElement === first || !cardRef.current.contains(document.activeElement)) {
            e.preventDefault();
            last.focus();
          }
        } else if (document.activeElement === last || !cardRef.current.contains(document.activeElement)) {
          e.preventDefault();
          first.focus();
        }
      }
    };

    window.addEventListener('keydown', handleKey);
    return () => {
      window.removeEventListener('keydown', handleKey);
      previousFocusRef.current?.focus();
    };
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div
      className="modal-backdrop"
      role="dialog"
      aria-modal="true"
      aria-labelledby={titleId}
      aria-describedby={subtitle ? subtitleId : undefined}
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div className="modal-card" ref={cardRef} tabIndex={-1}>
        <div className="card-head" style={{ marginBottom: 14 }}>
          <div>
            <h2 id={titleId} style={{ fontSize: 18 }}>
              {title}
            </h2>
            {subtitle && (
              <p id={subtitleId} className="lead" style={{ fontSize: 13 }}>
                {subtitle}
              </p>
            )}
          </div>
          <button
            type="button"
            className="btn btn-ghost btn-sm"
            onClick={onClose}
            aria-label="Cerrar ventana"
          >
            <X size={18} aria-hidden="true" />
          </button>
        </div>
        {children}
      </div>
    </div>
  );
};
