import { useCallback, useState } from 'react';

export type GeolocationStatus =
  | { kind: 'idle' }
  | { kind: 'loading' }
  | { kind: 'ok'; lat: number; lon: number }
  | { kind: 'denied' }
  | { kind: 'unsupported' }
  | { kind: 'timeout' }
  | { kind: 'error'; message: string };

export function useGeolocation(): {
  status: GeolocationStatus;
  request: () => void;
  reset: () => void;
} {
  const [status, setStatus] = useState<GeolocationStatus>({ kind: 'idle' });

  const request = useCallback(() => {
    if (typeof navigator === 'undefined' || !navigator.geolocation) {
      setStatus({ kind: 'unsupported' });
      return;
    }
    setStatus({ kind: 'loading' });
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setStatus({ kind: 'ok', lat: pos.coords.latitude, lon: pos.coords.longitude });
      },
      (err) => {
        if (err.code === err.PERMISSION_DENIED) setStatus({ kind: 'denied' });
        else if (err.code === err.TIMEOUT) setStatus({ kind: 'timeout' });
        else setStatus({ kind: 'error', message: err.message });
      },
      { enableHighAccuracy: false, timeout: 10_000, maximumAge: 60_000 },
    );
  }, []);

  const reset = useCallback(() => setStatus({ kind: 'idle' }), []);
  return { status, request, reset };
}
