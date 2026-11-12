import { Component, type ReactNode } from 'react';

interface Props {
  children: ReactNode;
}

interface State {
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidCatch(error: Error, info: unknown): void {
    console.error('ErrorBoundary caught', error, info);
  }

  reset = () => this.setState({ error: null });

  render() {
    if (this.state.error) {
      return (
        <div className="mx-auto max-w-md rounded-lg border border-stone-300 bg-white p-6 text-stone-800">
          <h2 className="text-lg font-semibold">Something broke.</h2>
          <p className="mt-2 text-sm text-stone-600">
            The page hit an unexpected error. You can try resetting without losing the
            rest of your session.
          </p>
          <button
            type="button"
            onClick={this.reset}
            className="mt-4 rounded border border-stone-300 bg-stone-50 px-3 py-1 text-sm font-medium hover:bg-stone-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-stone-400"
          >
            Reset view
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}
