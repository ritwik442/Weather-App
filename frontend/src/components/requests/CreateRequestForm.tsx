import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';
import { CandidatePicker } from '../CandidatePicker';
import { ErrorMessage } from '../ErrorMessage';
import { api, ApiError } from '../../lib/api';
import type { LocationCandidate } from '../../types/api';

interface FormState {
  location: string;
  start_date: string;
  end_date: string;
  notes: string;
}

const DEFAULT_STATE: FormState = {
  location: '',
  start_date: today(),
  end_date: today(),
  notes: '',
};

function today(): string {
  return new Date().toISOString().slice(0, 10);
}

export function CreateRequestForm() {
  const [form, setForm] = useState<FormState>(DEFAULT_STATE);
  const [pickingIndex, setPickingIndex] = useState<number | undefined>(undefined);
  const queryClient = useQueryClient();

  const mutation = useMutation({
    mutationFn: () =>
      api.createRequest({
        location: form.location,
        start_date: form.start_date,
        end_date: form.end_date,
        notes: form.notes.trim() || null,
        location_index: pickingIndex ?? null,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['requests'] });
      setForm(DEFAULT_STATE);
      setPickingIndex(undefined);
    },
  });

  const ambiguousCandidates: LocationCandidate[] = (() => {
    if (!(mutation.error instanceof ApiError)) return [];
    if (mutation.error.code !== 'LOCATION_AMBIGUOUS') return [];
    const raw = mutation.error.details['candidates'];
    return Array.isArray(raw) ? (raw as LocationCandidate[]) : [];
  })();

  return (
    <section className="rounded-xl border border-stone-200 bg-white p-6">
      <h2 className="text-sm font-medium uppercase tracking-wide text-stone-500">
        Save a new request
      </h2>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          mutation.mutate();
        }}
        className="mt-4 grid grid-cols-1 gap-3 md:grid-cols-6"
      >
        <label className="md:col-span-3">
          <span className="block text-xs font-medium text-stone-600">Location</span>
          <input
            type="text"
            value={form.location}
            required
            placeholder="City, landmark, postal code, or 'lat, lon'"
            onChange={(e) => {
              setForm({ ...form, location: e.target.value });
              setPickingIndex(undefined);
            }}
            className="mt-1 w-full rounded border border-stone-300 bg-white px-3 py-2 text-sm text-stone-900 placeholder-stone-400 focus:border-stone-500 focus:outline-none"
          />
        </label>
        <label>
          <span className="block text-xs font-medium text-stone-600">Start date</span>
          <input
            type="date"
            required
            value={form.start_date}
            max={form.end_date}
            onChange={(e) => setForm({ ...form, start_date: e.target.value })}
            className="mt-1 w-full rounded border border-stone-300 bg-white px-3 py-2 text-sm text-stone-900 focus:border-stone-500 focus:outline-none"
          />
        </label>
        <label>
          <span className="block text-xs font-medium text-stone-600">End date</span>
          <input
            type="date"
            required
            value={form.end_date}
            min={form.start_date}
            onChange={(e) => setForm({ ...form, end_date: e.target.value })}
            className="mt-1 w-full rounded border border-stone-300 bg-white px-3 py-2 text-sm text-stone-900 focus:border-stone-500 focus:outline-none"
          />
        </label>
        <label className="md:col-span-6">
          <span className="block text-xs font-medium text-stone-600">
            Notes (optional)
          </span>
          <input
            type="text"
            value={form.notes}
            onChange={(e) => setForm({ ...form, notes: e.target.value })}
            placeholder="e.g. trip prep, event planning"
            className="mt-1 w-full rounded border border-stone-300 bg-white px-3 py-2 text-sm text-stone-900 placeholder-stone-400 focus:border-stone-500 focus:outline-none"
          />
        </label>
        <div className="md:col-span-6 flex items-center gap-3">
          <button
            type="submit"
            disabled={mutation.isPending}
            className="rounded-full bg-stone-800 px-4 py-2 text-sm font-medium text-white hover:bg-stone-700 disabled:cursor-not-allowed disabled:opacity-60 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-stone-500"
          >
            {mutation.isPending ? 'Saving…' : 'Save request'}
          </button>
          {mutation.isSuccess && (
            <span className="text-sm text-stone-600">Saved.</span>
          )}
        </div>
      </form>

      {ambiguousCandidates.length > 0 && (
        <div className="mt-4">
          <CandidatePicker
            candidates={ambiguousCandidates}
            onPick={(index) => {
              setPickingIndex(index);
              mutation.mutate();
            }}
          />
        </div>
      )}

      {mutation.error && ambiguousCandidates.length === 0 && (
        <div className="mt-4">
          <ErrorMessage error={mutation.error} onRetry={() => mutation.mutate()} />
        </div>
      )}
    </section>
  );
}
