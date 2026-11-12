import { useCallback, useEffect, useState } from 'react';
import { loadUnit, saveUnit, type Unit } from '../lib/units';

export function useUnit(): [Unit, (next: Unit) => void] {
  const [unit, setUnit] = useState<Unit>(() => loadUnit());

  useEffect(() => {
    saveUnit(unit);
  }, [unit]);

  const setAndPersist = useCallback((next: Unit) => setUnit(next), []);
  return [unit, setAndPersist];
}
