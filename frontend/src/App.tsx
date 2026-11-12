import { useEffect, useState } from 'react';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api/v1';

type HealthState =
  | { status: 'loading' }
  | { status: 'ok'; payload: string }
  | { status: 'error'; message: string };

function App() {
  const [health, setHealth] = useState<HealthState>({ status: 'loading' });

  useEffect(() => {
    const controller = new AbortController();
    fetch(`${API_BASE_URL}/health`, { signal: controller.signal })
      .then(async (res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data: unknown = await res.json();
        const value =
          typeof data === 'object' && data !== null && 'status' in data
            ? String((data as { status: unknown }).status)
            : 'unknown';
        setHealth({ status: 'ok', payload: value });
      })
      .catch((err: unknown) => {
        if (err instanceof DOMException && err.name === 'AbortError') return;
        setHealth({
          status: 'error',
          message: err instanceof Error ? err.message : 'Failed to reach backend',
        });
      });
    return () => controller.abort();
  }, []);

  return (
    <main className="min-h-screen bg-slate-50 text-slate-900 flex items-center justify-center p-6">
      <section className="max-w-md w-full rounded-2xl bg-white shadow-sm border border-slate-200 p-8 space-y-4">
        <h1 className="text-2xl font-semibold">Weather App</h1>
        <p className="text-slate-600">Frontend ↔ backend connectivity check.</p>
        <div className="rounded-lg border border-slate-200 p-4 bg-slate-50">
          <div className="text-sm text-slate-500">Backend health</div>
          {health.status === 'loading' && <div className="font-mono">checking…</div>}
          {health.status === 'ok' && (
            <div className="font-mono text-emerald-700">{health.payload}</div>
          )}
          {health.status === 'error' && (
            <div className="font-mono text-rose-700">error: {health.message}</div>
          )}
        </div>
        <p className="text-xs text-slate-400">API base: {API_BASE_URL}</p>
      </section>
    </main>
  );
}

export default App;
