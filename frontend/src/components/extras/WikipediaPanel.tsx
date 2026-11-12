import { BookOpen, ExternalLink } from 'lucide-react';
import type { ExtraPiece, WikipediaExtraValue } from '../../types/api';

interface Props {
  piece: ExtraPiece<WikipediaExtraValue>;
}

export function WikipediaPanel({ piece }: Props) {
  if (!piece.value || !piece.value.extract) return null;
  const { title, extract, url, thumbnail } = piece.value;
  return (
    <section
      aria-label="Wikipedia"
      className="rounded-xl border border-stone-200 bg-white p-4"
    >
      <h3 className="flex items-center gap-2 text-sm font-medium uppercase tracking-wide text-stone-500">
        <BookOpen aria-hidden className="h-4 w-4" />
        Wikipedia
      </h3>
      <div className="mt-3 flex gap-4">
        {thumbnail && (
          <img
            src={thumbnail}
            alt=""
            className="h-24 w-24 flex-none rounded border border-stone-200 object-cover"
          />
        )}
        <div className="min-w-0 text-sm text-stone-800">
          {title && <h4 className="text-base font-semibold text-stone-900">{title}</h4>}
          <p className="mt-1 leading-relaxed">{extract}</p>
          {url && (
            <a
              href={url}
              target="_blank"
              rel="noreferrer"
              className="mt-2 inline-flex items-center gap-1 text-xs font-medium text-stone-700 hover:text-stone-950"
            >
              Read on Wikipedia
              <ExternalLink aria-hidden className="h-3 w-3" />
            </a>
          )}
        </div>
      </div>
    </section>
  );
}
