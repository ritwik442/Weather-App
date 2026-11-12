import { cn } from '../lib/cn';

export function LoadingState({ label = 'Loading…' }: { label?: string }) {
  return (
    <div
      role="status"
      aria-live="polite"
      className="flex items-center gap-3 rounded-lg border border-stone-200 bg-white px-4 py-3 text-stone-600"
    >
      <span className="h-2 w-2 animate-pulse rounded-full bg-stone-400" />
      <span className="text-sm">{label}</span>
    </div>
  );
}

export function SkeletonBlock({ className }: { className?: string }) {
  return (
    <div
      aria-hidden
      className={cn('animate-pulse rounded-md bg-stone-200', className)}
    />
  );
}
