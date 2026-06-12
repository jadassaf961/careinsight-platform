import { createContext, useContext, useEffect, useState, ReactNode } from "react";
import { api, tokenStore, UserMe } from "@/lib/api";

interface AuthState {
  user: UserMe | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthState | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserMe | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    const t = tokenStore.get();
    if (!t) {
      setLoading(false);
      return;
    }
    api.get<UserMe>("/auth/me")
      .then((u) => { if (!cancelled) setUser(u); })
      .catch(() => tokenStore.clear())
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, []);

  async function login(email: string, password: string): Promise<void> {
    const { access_token } = await api.post<{ access_token: string }>(
      "/auth/login", { email, password },
    );
    tokenStore.set(access_token);
    const me = await api.get<UserMe>("/auth/me");
    setUser(me);
  }

  function logout() {
    tokenStore.clear();
    setUser(null);
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside <AuthProvider>");
  return ctx;
}
