import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useEffect, useState } from 'react';
import { CandidatePicker } from '../CandidatePicker';
import { ErrorMessage } from '../ErrorMessage';
import { api, ApiError } from '../../lib/api';
import type { LocationCandidate, SavedRequest } from '../../types/api';

interface Props {
  open: boolean;
  request: SavedRequest | null;
  onClose: () => void;
}

interface FormState {
  location: string;
  start_date: string;
  end_date: string;
  notes: string;
}

export function EditRequestModal({ open, request, onClose }: Props) {
  const [form, setForm] = useState<FormState | null>(null);
  const [pickingIndex, setPickingIndex] = useState<number | undefined>(undefined);
  const queryClient = useQueryClient();

  useEffect(() => {
    if (open && request) {
      setForm({
        location: request.location.display_name,
        start_date: request.start_date,
        end_date: request.end_date,
        notes: request.notes ?? '',
      });
      setPickingIndex(undefined);
    }
    if (!open) {
      setForm(null);
      setPickingIndex(undefined);
    }
  }, [open, request]);

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [open, onClose]);

  const mutation = useMutation({
    mutationFn: () => {
      if (!request || !form) throw new Error('No request');
      const changedLocation =
        form.location.trim() && form.location.trim() !== request.location.display_name;
      return api.updateRequest(request.id, {
        location: changedLocation ? form.location.trim() : null,
        start_date: form.start_date !== request.start_date ? form.start_date : null,
        end_date: form.end_date !== request.end_date ? form.end_date : null,
        notes: form.notes,
        location_index: pickingIndex ?? null,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['requests'] });
      queryClient.invalidateQueries({ queryKey: ['request', request?.id] });
      onClose();
    },
  });

  if (!open || !request || !form) return null;

  const ambiguousCandidates: LocationCandidate[] = (() => {
    if (!(mutation.error instanceof ApiError)) return [];
    if (mutation.error.code !== 'LOCATION_AMBIGUOUS') return [];
    const raw = mutation.error.details['candidates'];
    return Array.isArray(raw) ? (raw as LocationCandidate[]) : [];
  })();

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="edit-title"
      className="fixed inset-0 z-30 flex items-center justify-center bg-stone-900/40 p-4"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div className="w-full max-w-lg overflow-hidden rounded-xl border border-stone-200 bg-white">
        <header className="flex items-center justify-between border-b border-stone-200 px-5 py-3">
          <h3 id="edit-title" className="text-sm font-medium text-stone-900">
            Edit request
          </h3>
          <button
            type="button"
            onClick={onClose}
            className="text-stone-500 hover:text-stone-900"
          >
            Close
          </button>
        </header>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            mutation.mutate();
          }}
          className="space-y-3 px-5 py-4"
        >
          <label className="block">
            <span className="block text-xs font-medium text-stone-600">Location</span>
            <input
              type="text"
              value={form.location}
              onChange={(e) => {
                setForm({ ...form, location: e.target.value });
                setPickingIndex(undefined);
              }}
              className="mt-1 w-full rounded border border-stone-300 bg-white px-3 py-2 text-sm text-stone-900 focus:border-stone-500 focus:outline-none"
            />
          </label>
          <div className="grid grid-cols-2 gap-3">
            <label>
              <span className="block text-xs font-medium text-stone-600">Start date</span>
              <input
                type="date"
                value={form.start_date}
                onChange={(e) => setForm({ ...form, start_date: e.target.value })}
                className="mt-1 w-full rounded border border-stone-300 bg-white px-3 py-2 text-sm text-stone-900 focus:border-stone-500 focus:outline-none"
              />
            </label>
            <label>
              <span className="block text-xs font-medium text-stone-600">End date</span>
              <input
                type="date"
                value={form.end_date}
                onChange={(e) => setForm({ ...form, end_date: e.target.value })}
                className="mt-1 w-full rounded border border-stone-300 bg-white px-3 py-2 text-sm text-stone-900 focus:border-stone-500 focus:outline-none"
              />
            </label>
          </div>
          <label className="block">
            <span className="block text-xs font-medium text-stone-600">Notes</span>
            <input
              type="text"
              value={form.notes}
              onChange={(e) => setForm({ ...form, notes: e.target.value })}
              className="mt-1 w-full rounded border border-stone-300 bg-white px-3 py-2 text-sm text-stone-900 focus:border-stone-500 focus:outline-none"
            />
          </label>

          {ambiguousCandidates.length > 0 && (
            <CandidatePicker
              candidates={ambiguousCandidates}
              onPick={(index) => {
                setPickingIndex(index);
                mutation.mutate();
              }}
            />
          )}

          {mutation.error && ambiguousCandidates.length === 0 && (
            <ErrorMessage error={mutation.error} onRetry={() => mutation.mutate()} />
          )}

          <div className="flex justify-end gap-2 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="rounded-full border border-stone-300 bg-white px-3 py-1.5 text-sm font-medium text-stone-800 hover:bg-stone-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-stone-500"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={mutation.isPending}
              className="rounded-full border border-stone-800 bg-stone-800 px-3 py-1.5 text-sm font-medium text-white hover:bg-stone-700 disabled:opacity-60 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-stone-500"
            >
              {mutation.isPending ? 'Saving…' : 'Save changes'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
