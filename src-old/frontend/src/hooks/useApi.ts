import { useCallback, useEffect, useRef, useState } from "react";
import { ApiError } from "../services/http";

interface UseApiState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
  status: number | null;
  refetch: () => void;
}

// Hook fetch generik dengan loading/error/refetch dan pembatalan request.
// `deps` mengontrol kapan fetch dijalankan ulang.
export function useApi<T>(fetcher: (signal: AbortSignal) => Promise<T>, deps: unknown[] = []): UseApiState<T> {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState<number | null>(null);
  const [nonce, setNonce] = useState(0);

  // Simpan fetcher terbaru tanpa memicu efek (deps yang mengontrol).
  const fetcherRef = useRef(fetcher);
  fetcherRef.current = fetcher;

  useEffect(() => {
    const controller = new AbortController();
    let active = true;
    setLoading(true);
    setError(null);

    fetcherRef.current(controller.signal)
      .then((result) => {
        if (!active) return;
        setData(result);
        setStatus(200);
      })
      .catch((err) => {
        if (!active || controller.signal.aborted) return;
        if (err instanceof DOMException && err.name === "AbortError") return;
        setError(err instanceof Error ? err.message : "Terjadi kesalahan tak terduga.");
        setStatus(err instanceof ApiError ? err.status : null);
        setData(null);
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => {
      active = false;
      controller.abort();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...deps, nonce]);

  const refetch = useCallback(() => setNonce((n) => n + 1), []);

  return { data, loading, error, status, refetch };
}

interface UseMutationResult<TArgs extends unknown[], TResult> {
  mutate: (...args: TArgs) => Promise<TResult>;
  loading: boolean;
  error: string | null;
}

// Hook untuk aksi tulis (POST/PATCH) dengan state pending/error.
export function useMutation<TArgs extends unknown[], TResult>(
  action: (...args: TArgs) => Promise<TResult>,
): UseMutationResult<TArgs, TResult> {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const mutate = useCallback(
    async (...args: TArgs) => {
      setLoading(true);
      setError(null);
      try {
        return await action(...args);
      } catch (err) {
        const message = err instanceof Error ? err.message : "Aksi gagal.";
        setError(message);
        throw err;
      } finally {
        setLoading(false);
      }
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [],
  );

  return { mutate, loading, error };
}
