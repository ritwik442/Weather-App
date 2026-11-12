import { Download } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';
import { api, type ExportFormat } from '../../lib/api';

interface Props {
  ids?: number[];
  label?: string;
}

const FORMATS: { value: ExportFormat; label: string }[] = [
  { value: 'json', label: 'JSON' },
  { value: 'csv', label: 'CSV' },
  { value: 'xml', label: 'XML' },
  { value: 'md', label: 'Markdown' },
  { value: 'pdf', label: 'PDF' },
];

export function ExportMenu({ ids, label = 'Export' }: Props) {
  const [open, setOpen] = useState(false);
  const wrapperRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const onDown = (e: MouseEvent) => {
      if (wrapperRef.current && !wrapperRef.current.contains(e.target as Node)) setOpen(false);
    };
    window.addEventListener('mousedown', onDown);
    return () => window.removeEventListener('mousedown', onDown);
  }, []);

  return (
    <div ref={wrapperRef} className="relative">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-haspopup="menu"
        aria-expanded={open}
        className="inline-flex items-center gap-2 rounded-full border border-stone-300 bg-white px-3 py-1.5 text-sm font-medium text-stone-800 hover:bg-stone-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-stone-500"
      >
        <Download aria-hidden className="h-4 w-4" />
        <span>{label}</span>
      </button>
      {open && (
        <ul
          role="menu"
          className="absolute right-0 z-20 mt-2 w-40 overflow-hidden rounded-lg border border-stone-200 bg-white"
        >
          {FORMATS.map((f) => (
            <li key={f.value}>
              <a
                role="menuitem"
                href={api.exportUrl(f.value, ids)}
                className="block px-3 py-2 text-sm text-stone-800 hover:bg-stone-100"
                onClick={() => setOpen(false)}
              >
                {f.label}
              </a>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
