import { AlertTriangle } from 'lucide-react';
import { ApiError } from '../lib/api';

interface Props {
  error: unknown;
  onRetry?: () => void;
}

export function ErrorMessage({ error, onRetry }: Props) {
  const text = humanize(error);
  return (
    <div
      role="alert"
      aria-live="assertive"
      className="rounded-lg border border-amber-300 bg-amber-50 px-4 py-3 text-amber-900"
    >
      <div className="flex items-start gap-3">
        <AlertTriangle aria-hidden className="mt-0.5 h-4 w-4 flex-none" />
        <div className="text-sm leading-relaxed">{text}</div>
      </div>
      {onRetry && (
        <button
          type="button"
          onClick={onRetry}
          className="mt-3 rounded border border-amber-400 bg-amber-100 px-3 py-1 text-xs font-medium hover:bg-amber-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-amber-500"
        >
          Retry
        </button>
      )}
    </div>
  );
}

function humanize(error: unknown): string {
  if (error instanceof ApiError) {
    switch (error.code) {
      case 'LOCATION_NOT_FOUND':
        return "We couldn't find that place. Try a nearby city or a postal code.";
      case 'LOCATION_AMBIGUOUS':
        return 'Multiple places match — pick one of the suggestions below.';
      case 'UPSTREAM_TIMEOUT':
        return 'The weather service took too long to answer. Try again in a moment.';
      case 'UPSTREAM_FAILURE':
        return 'The weather service is having trouble. Try again shortly.';
      case 'VALIDATION_FAILED':
        return error.message;
      case 'NETWORK_ERROR':
        return 'Network error. Check your connection and try again.';
      default:
        return error.message || 'Something went wrong.';
    }
  }
  if (error instanceof Error) return error.message;
  return 'Something went wrong.';
}
