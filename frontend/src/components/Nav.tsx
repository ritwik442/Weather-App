import { NavLink } from 'react-router-dom';
import { cn } from '../lib/cn';

export function Nav() {
  return (
    <nav className="border-b border-stone-200 bg-white">
      <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-3 md:px-6">
        <span className="text-sm font-semibold uppercase tracking-wide text-stone-700">
          Weather App
        </span>
        <ul className="flex items-center gap-1">
          {[
            { to: '/', label: 'Home' },
            { to: '/saved', label: 'Saved' },
          ].map((item) => (
            <li key={item.to}>
              <NavLink
                to={item.to}
                end
                className={({ isActive }) =>
                  cn(
                    'rounded-full px-3 py-1.5 text-sm font-medium',
                    isActive
                      ? 'bg-stone-800 text-white'
                      : 'text-stone-700 hover:bg-stone-100',
                  )
                }
              >
                {item.label}
              </NavLink>
            </li>
          ))}
        </ul>
      </div>
    </nav>
  );
}
