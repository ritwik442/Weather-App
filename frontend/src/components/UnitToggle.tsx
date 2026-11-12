import { cn } from '../lib/cn';
import type { Unit } from '../lib/units';

interface Props {
  unit: Unit;
  onChange: (next: Unit) => void;
}

export function UnitToggle({ unit, onChange }: Props) {
  return (
    <div
      role="group"
      aria-label="Temperature unit"
      className="inline-flex overflow-hidden rounded-full border border-stone-300 bg-white text-sm"
    >
      {(['c', 'f'] as const).map((value) => (
        <button
          key={value}
          type="button"
          aria-pressed={unit === value}
          onClick={() => onChange(value)}
          className={cn(
            'px-3 py-1 font-medium transition-colors',
            unit === value
              ? 'bg-stone-800 text-white'
              : 'bg-white text-stone-700 hover:bg-stone-100',
            'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-stone-500',
          )}
        >
          °{value.toUpperCase()}
        </button>
      ))}
    </div>
  );
}
