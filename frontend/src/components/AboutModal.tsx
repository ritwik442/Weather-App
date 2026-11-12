import { ExternalLink, X } from 'lucide-react';
import { useEffect, useRef } from 'react';
import {
  APP_NAME,
  AUTHOR_NAME,
  PM_ACCELERATOR_BLURB,
  PM_ACCELERATOR_LINK,
  SUBMISSION_LABEL,
} from '../lib/branding';

interface Props {
  open: boolean;
  onClose: () => void;
}

export function AboutModal({ open, onClose }: Props) {
  const closeButtonRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', onKey);
    closeButtonRef.current?.focus();
    return () => window.removeEventListener('keydown', onKey);
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="about-title"
      className="fixed inset-0 z-40 flex items-end justify-center bg-stone-900/40 p-0 sm:items-center sm:p-4"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div className="w-full max-w-lg overflow-hidden rounded-t-2xl border border-stone-200 bg-white sm:rounded-2xl">
        <header className="flex items-center justify-between border-b border-stone-200 px-5 py-3">
          <h3 id="about-title" className="text-sm font-medium text-stone-900">
            About PM Accelerator
          </h3>
          <button
            ref={closeButtonRef}
            type="button"
            onClick={onClose}
            aria-label="Close dialog"
            className="rounded p-1 text-stone-500 hover:bg-stone-100 hover:text-stone-900 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-stone-500"
          >
            <X aria-hidden className="h-4 w-4" />
          </button>
        </header>
        <div className="space-y-4 px-5 py-4 text-sm text-stone-700">
          <p className="leading-relaxed">{PM_ACCELERATOR_BLURB}</p>
          <a
            href={PM_ACCELERATOR_LINK}
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-1 text-sm font-medium text-stone-900 underline underline-offset-2 hover:text-stone-700"
          >
            Learn more on LinkedIn
            <ExternalLink aria-hidden className="h-3.5 w-3.5" />
          </a>
          <div className="border-t border-stone-200 pt-3 text-xs text-stone-500">
            <p>
              <span className="font-medium text-stone-700">{APP_NAME}</span> · built by{' '}
              {AUTHOR_NAME}
            </p>
            <p className="mt-1">{SUBMISSION_LABEL}</p>
          </div>
        </div>
      </div>
    </div>
  );
}
