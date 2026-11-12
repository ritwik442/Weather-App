import type { LocationCandidate } from '../types/api';

interface Props {
  candidates: LocationCandidate[];
  onPick: (index: number) => void;
}

export function CandidatePicker({ candidates, onPick }: Props) {
  return (
    <section
      aria-labelledby="disambig-title"
      className="rounded-lg border border-stone-200 bg-white p-4"
    >
      <h2 id="disambig-title" className="text-sm font-medium text-stone-800">
        Did you mean…?
      </h2>
      <ul className="mt-2 divide-y divide-stone-200">
        {candidates.map((c, i) => (
          <li key={`${c.lat}-${c.lon}-${i}`}>
            <button
              type="button"
              onClick={() => onPick(i)}
              className="w-full py-2 text-left text-sm text-stone-800 hover:text-stone-950 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-stone-400"
            >
              <span className="block font-medium">{c.display_name}</span>
              <span className="block text-xs text-stone-500">
                {c.lat.toFixed(4)}, {c.lon.toFixed(4)}
                {c.timezone ? ` · ${c.timezone}` : ''}
              </span>
            </button>
          </li>
        ))}
      </ul>
    </section>
  );
}
