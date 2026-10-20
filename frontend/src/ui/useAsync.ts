import { useCallback, useState } from "react";

interface AsyncState {
  busy: boolean;
  error: string | null;
  run: <T>(task: () => Promise<T>) => Promise<T | undefined>;
}

/** Envuelve una acción async con estado de carga y mensaje de error para el usuario. */
export function useAsync(): AsyncState {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const run = useCallback(async <T,>(task: () => Promise<T>) => {
    setBusy(true);
    setError(null);
    try {
      return await task();
    } catch (failure) {
      setError(failure instanceof Error ? failure.message : "Algo salió mal.");
      return undefined;
    } finally {
      setBusy(false);
    }
  }, []);

  return { busy, error, run };
}
