import { useQuery } from '@tanstack/react-query';
import { ChevronLeft, ChevronRight, Search } from 'lucide-react';
import { useState } from 'react';
import { ErrorMessage } from '../ErrorMessage';
import { LoadingState } from '../LoadingState';
import { useDebounced } from '../../hooks/useDebounced';
import { api } from '../../lib/api';
import type { SavedRequestListItem } from '../../types/api';

interface Props {
  onOpen: (id: number) => void;
}

const PAGE_SIZE = 10;

export function RequestsList({ onOpen }: Props) {
  const [q, setQ] = useState('');
  const [page, setPage] = useState(1);
  const debouncedQ = useDebounced(q, 250);

  const query = useQuery({
    queryKey: ['requests', debouncedQ, page],
    queryFn: ({ signal }) =>
      api.listRequests({ q: debouncedQ || undefined, page, pageSize: PAGE_SIZE }, signal),
    placeholderData: (prev) => prev,
    staleTime: 10_000,
  });

  const totalPages = query.data ? Math.max(1, Math.ceil(query.data.total / PAGE_SIZE)) : 1;

  return (
    <section className="rounded-xl border border-stone-200 bg-white">
      <header className="flex flex-wrap items-center justify-between gap-3 border-b border-stone-200 px-5 py-3">
        <h2 className="text-sm font-medium uppercase tracking-wide text-stone-500">
          Saved requests
        </h2>
        <label className="flex min-w-0 flex-1 items-center gap-2 rounded-full border border-stone-300 px-3 py-1.5 focus-within:border-stone-500 sm:flex-none">
          <Search aria-hidden className="h-4 w-4 flex-none text-stone-500" />
          <span className="sr-only">Search saved requests by location</span>
          <input
            type="search"
            value={q}
            placeholder="Search by location"
            onChange={(e) => {
              setQ(e.target.value);
              setPage(1);
            }}
            className="min-w-0 flex-1 bg-transparent text-sm text-stone-900 placeholder-stone-400 focus:outline-none sm:w-56 sm:flex-none"
          />
        </label>
      </header>

      <div className="px-5 py-3">
        {query.isLoading && <LoadingState label="Loading saved requests…" />}
        {query.error && <ErrorMessage error={query.error} onRetry={() => query.refetch()} />}
        {query.data && query.data.items.length === 0 && (
          <p className="py-6 text-center text-sm text-stone-500">
            No saved requests yet. Create one above.
          </p>
        )}
        {query.data && query.data.items.length > 0 && <Table items={query.data.items} onOpen={onOpen} />}
      </div>

      {query.data && query.data.total > 0 && (
        <footer className="flex items-center justify-between border-t border-stone-200 px-5 py-3 text-xs text-stone-600">
          <span>
            {query.data.total} total · page {page} of {totalPages}
          </span>
          <div className="flex items-center gap-2">
            <button
              type="button"
              disabled={page <= 1}
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              className="inline-flex items-center gap-1 rounded border border-stone-300 bg-white px-2 py-1 disabled:opacity-50"
              aria-label="Previous page"
            >
              <ChevronLeft aria-hidden className="h-3 w-3" /> Prev
            </button>
            <button
              type="button"
              disabled={page >= totalPages}
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              className="inline-flex items-center gap-1 rounded border border-stone-300 bg-white px-2 py-1 disabled:opacity-50"
              aria-label="Next page"
            >
              Next <ChevronRight aria-hidden className="h-3 w-3" />
            </button>
          </div>
        </footer>
      )}
    </section>
  );
}

function Table({ items, onOpen }: { items: SavedRequestListItem[]; onOpen: (id: number) => void }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse text-sm">
        <thead className="text-xs uppercase tracking-wide text-stone-500">
          <tr>
            <th scope="col" className="px-2 py-2 text-left">Location</th>
            <th scope="col" className="px-2 py-2 text-left">Range</th>
            <th scope="col" className="px-2 py-2 text-left">Notes</th>
            <th scope="col" className="px-2 py-2 text-right">Updated</th>
          </tr>
        </thead>
        <tbody>
          {items.map((r) => (
            <tr key={r.id} className="border-t border-stone-100">
              <td className="px-2 py-2">
                <button
                  type="button"
                  onClick={() => onOpen(r.id)}
                  className="text-left font-medium text-stone-900 hover:underline"
                >
                  {r.location.display_name}
                </button>
              </td>
              <td className="px-2 py-2 text-stone-700">
                {r.start_date} → {r.end_date}
              </td>
              <td className="px-2 py-2 text-stone-600">{r.notes ?? '—'}</td>
              <td className="px-2 py-2 text-right text-xs tabular-nums text-stone-500">
                {formatDate(r.updated_at)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function formatDate(iso: string): string {
  try {
    return new Date(iso).toLocaleDateString(undefined, {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  } catch {
    return iso;
  }
}
