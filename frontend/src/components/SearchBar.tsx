import { useQuery } from '@tanstack/react-query';
import { Loader2, LocateFixed, Search } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';
import { api, ApiError } from '../lib/api';
import { cn } from '../lib/cn';
import { useDebounced } from '../hooks/useDebounced';
import type { LocationCandidate } from '../types/api';

interface Props {
  onSubmit: (query: string) => void;
  onUseMyLocation: () => void;
  geolocating: boolean;
  disabled?: boolean;
}

export function SearchBar({ onSubmit, onUseMyLocation, geolocating, disabled }: Props) {
  const [raw, setRaw] = useState('');
  const [open, setOpen] = useState(false);
  const debounced = useDebounced(raw, 250);
  const wrapperRef = useRef<HTMLDivElement>(null);

  const suggestions = useQuery({
    queryKey: ['autocomplete', debounced],
    queryFn: ({ signal }) => api.autocomplete(debounced, signal),
    enabled: debounced.trim().length >= 2,
    staleTime: 60_000,
    retry: false,
  });

  useEffect(() => {
    const onDown = (e: MouseEvent) => {
      if (wrapperRef.current && !wrapperRef.current.contains(e.target as Node)) setOpen(false);
    };
    window.addEventListener('mousedown', onDown);
    return () => window.removeEventListener('mousedown', onDown);
  }, []);

  const submit = (value: string) => {
    const trimmed = value.trim();
    if (!trimmed) return;
    setOpen(false);
    onSubmit(trimmed);
  };

  const candidates = suggestions.data?.candidates ?? [];

  return (
    <div ref={wrapperRef} className="relative">
      <form
        onSubmit={(e) => {
          e.preventDefault();
          submit(raw);
        }}
        className="flex flex-col gap-2 sm:flex-row"
      >
        <label className="sr-only" htmlFor="location-search">
          Search for a location
        </label>
        <div className="flex min-w-0 flex-1 items-center gap-2 rounded-full border border-stone-300 bg-white px-4 py-2 focus-within:border-stone-500">
          <Search aria-hidden className="h-4 w-4 flex-none text-stone-500" />
          <input
            id="location-search"
            type="text"
            autoComplete="off"
            value={raw}
            placeholder="City, landmark, postal code, or 'lat, lon'"
            disabled={disabled}
            onFocus={() => setOpen(true)}
            onChange={(e) => {
              setRaw(e.target.value);
              setOpen(true);
            }}
            className="min-w-0 flex-1 bg-transparent text-sm text-stone-900 placeholder-stone-400 focus:outline-none"
          />
          {suggestions.isFetching && (
            <Loader2 aria-hidden className="h-4 w-4 flex-none animate-spin text-stone-500" />
          )}
        </div>
        <div className="flex gap-2">
          <button
            type="submit"
            disabled={disabled}
            className="flex-1 rounded-full border border-stone-300 bg-stone-800 px-4 py-2 text-sm font-medium text-white hover:bg-stone-700 disabled:cursor-not-allowed disabled:opacity-60 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-stone-500 sm:flex-none"
          >
            Search
          </button>
          <button
            type="button"
            onClick={onUseMyLocation}
            disabled={geolocating || disabled}
            aria-label="Use my location"
            className="inline-flex flex-1 items-center justify-center gap-2 rounded-full border border-stone-300 bg-white px-4 py-2 text-sm font-medium text-stone-800 hover:bg-stone-100 disabled:cursor-not-allowed disabled:opacity-60 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-stone-500 sm:flex-none"
          >
            {geolocating ? (
              <Loader2 aria-hidden className="h-4 w-4 animate-spin" />
            ) : (
              <LocateFixed aria-hidden className="h-4 w-4" />
            )}
            <span className="hidden sm:inline">My location</span>
            <span className="sm:hidden">Locate me</span>
          </button>
        </div>
      </form>

      {open && candidates.length > 0 && (
        <ul
          role="listbox"
          className="absolute left-0 right-0 z-10 mt-2 max-h-72 overflow-auto rounded-lg border border-stone-200 bg-white"
        >
          {candidates.map((c, i) => (
            <li key={`${c.lat}-${c.lon}-${i}`}>
              <button
                type="button"
                onClick={() => {
                  setRaw(c.display_name);
                  submit(c.display_name);
                }}
                className={cn(
                  'w-full px-4 py-2 text-left text-sm text-stone-800 hover:bg-stone-100',
                  'focus:bg-stone-100 focus:outline-none',
                )}
              >
                <span className="block font-medium">{primaryName(c)}</span>
                <span className="block text-xs text-stone-500">{secondaryName(c)}</span>
              </button>
            </li>
          ))}
        </ul>
      )}

      {suggestions.error && suggestions.error instanceof ApiError && (
        <p className="mt-2 text-xs text-stone-500">Suggestions unavailable right now.</p>
      )}
    </div>
  );
}

function primaryName(c: LocationCandidate): string {
  return c.display_name.split(',')[0]?.trim() || c.display_name;
}

function secondaryName(c: LocationCandidate): string {
  const parts = [c.region, c.country].filter(Boolean);
  return parts.join(', ');
}
