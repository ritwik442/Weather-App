import { AlertCircle, Info } from 'lucide-react';
import { cn } from '../lib/cn';
import type { Tip } from '../types/api';

interface Props {
  tips: Tip[];
}

export function TipsPanel({ tips }: Props) {
  if (!tips.length) return null;
  return (
    <section
      aria-label="Things you might not think about"
      className="rounded-xl border border-stone-200 bg-white p-6"
    >
      <h2 className="text-sm font-medium uppercase tracking-wide text-stone-500">
        Things you might not think about
      </h2>
      <ul className="mt-3 space-y-2">
        {tips.map((t) => {
          const isWarning = t.severity === 'warning';
          const Icon = isWarning ? AlertCircle : Info;
          return (
            <li
              key={t.code}
              className={cn(
                'flex items-start gap-3 rounded-lg border px-3 py-2 text-sm',
                isWarning
                  ? 'border-amber-300 bg-amber-50 text-amber-900'
                  : 'border-stone-200 bg-stone-50 text-stone-800',
              )}
            >
              <Icon aria-hidden className="mt-0.5 h-4 w-4 flex-none" />
              <span>{t.message}</span>
            </li>
          );
        })}
      </ul>
    </section>
  );
}
