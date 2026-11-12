import { ExternalLink, Youtube } from 'lucide-react';
import type { ExtraPiece, YoutubeExtraValue } from '../../types/api';

interface Props {
  piece: ExtraPiece<YoutubeExtraValue>;
  locationName: string;
}

export function VideosPanel({ piece, locationName }: Props) {
  const value = piece.value;
  if (!value) {
    return (
      <section
        aria-label="Videos"
        className="rounded-xl border border-stone-200 bg-white p-4"
      >
        <PanelHeader />
        <p className="mt-2 text-sm text-stone-600">
          Videos are unavailable right now.
        </p>
      </section>
    );
  }

  return (
    <section
      aria-label="Videos"
      className="rounded-xl border border-stone-200 bg-white p-4"
    >
      <PanelHeader />
      {value.videos.length === 0 ? (
        <p className="mt-2 text-sm text-stone-600">
          No videos to show inline.{' '}
          <a
            href={value.search_url}
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-1 font-medium text-stone-900 underline underline-offset-2 hover:text-stone-700"
          >
            Watch videos of {locationName} on YouTube
            <ExternalLink aria-hidden className="h-3 w-3" />
          </a>
        </p>
      ) : (
        <ul className="mt-3 grid grid-cols-1 gap-3 sm:grid-cols-2">
          {value.videos.map((v) => (
            <li
              key={v.id}
              className="flex gap-3 rounded-lg border border-stone-200 bg-stone-50 p-3"
            >
              {v.thumbnail && (
                <img
                  src={v.thumbnail}
                  alt=""
                  className="h-16 w-28 flex-none rounded border border-stone-200 object-cover"
                />
              )}
              <div className="min-w-0">
                <a
                  href={v.url}
                  target="_blank"
                  rel="noreferrer"
                  className="line-clamp-2 text-sm font-medium text-stone-900 hover:underline"
                >
                  {v.title ?? 'Untitled video'}
                </a>
                <p className="mt-1 truncate text-xs text-stone-500">
                  {v.channel ?? 'Unknown channel'}
                </p>
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

function PanelHeader() {
  return (
    <h3 className="flex items-center gap-2 text-sm font-medium uppercase tracking-wide text-stone-500">
      <Youtube aria-hidden className="h-4 w-4" />
      Videos
    </h3>
  );
}
