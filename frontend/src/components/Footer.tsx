import { Info } from 'lucide-react';
import { useState } from 'react';
import { AUTHOR_NAME, SUBMISSION_LABEL } from '../lib/branding';
import { AboutModal } from './AboutModal';

export function Footer() {
  const [aboutOpen, setAboutOpen] = useState(false);
  return (
    <footer className="mt-10 border-t border-stone-200 bg-white">
      <div className="mx-auto flex max-w-5xl flex-col items-start justify-between gap-2 px-4 py-4 text-xs text-stone-600 sm:flex-row sm:items-center md:px-6">
        <div>
          <p className="font-medium text-stone-800">Built by {AUTHOR_NAME}</p>
          <p className="mt-0.5">{SUBMISSION_LABEL}</p>
        </div>
        <button
          type="button"
          onClick={() => setAboutOpen(true)}
          className="inline-flex items-center gap-2 rounded-full border border-stone-300 bg-white px-3 py-1.5 text-xs font-medium text-stone-800 hover:bg-stone-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-stone-500"
        >
          <Info aria-hidden className="h-3.5 w-3.5" />
          About PM Accelerator
        </button>
      </div>
      <AboutModal open={aboutOpen} onClose={() => setAboutOpen(false)} />
    </footer>
  );
}
