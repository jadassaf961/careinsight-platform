import { FormEvent, useState } from "react";
import { useNavigate, useLocation, Navigate } from "react-router-dom";
import { useAuth } from "@/auth/AuthContext";
import { Input } from "@/components/core/Input";
import { Button } from "@/components/core/Button";

export function Login() {
  const { user, login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [email, setEmail] = useState("physician@careinsight.dev");
  const [password, setPassword] = useState("Demo123!");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  if (user) {
    const dest = (location.state as { from?: { pathname: string } })?.from?.pathname ?? "/patients";
    return <Navigate to={dest} replace />;
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await login(email, password);
      navigate("/patients", { replace: true });
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="min-h-screen flex bg-paper text-ink">
      {/* Left: mini-hero (hidden on small screens) */}
      <div className="hidden md:flex md:w-1/2 flex-col justify-between border-r border-hairline p-12">
        <span className="font-display text-lg font-bold tracking-tight">careinsight</span>
        <h1 className="font-display text-[clamp(2.5rem,4.5vw,4.5rem)] font-bold leading-[1.02] tracking-[-0.04em]">
          Every patient,<br />
          <em className="font-serifit font-normal italic">followed home.</em>
        </h1>
        <div className="border-t border-hairline pt-4 font-display text-sm font-semibold tracking-tight text-ink/40">
          predict <span className="px-2 text-ink/20">·</span> plan
          <span className="px-2 text-ink/20">·</span> discharge
          <span className="px-2 text-ink/20">·</span> follow up
        </div>
      </div>

      {/* Right: form */}
      <div className="flex flex-1 items-center justify-center p-8">
        <div className="w-full max-w-sm">
          <div className="mb-10 md:hidden">
            <span className="font-display text-lg font-bold tracking-tight">careinsight</span>
          </div>
          <div className="font-display text-[0.65rem] font-semibold tracking-[0.2em] uppercase text-ink/40 mb-2">
            Sign in
          </div>
          <h2 className="font-display text-3xl font-bold tracking-tight mb-10">
            Welcome <em className="font-serifit font-normal italic">back.</em>
          </h2>
          <form onSubmit={onSubmit} className="space-y-7">
            <Input
              label="Email"
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              autoComplete="username"
            />
            <Input
              label="Password"
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="current-password"
            />
            {error && (
              <div className="text-sm text-risk-high bg-risk-high-bg border border-risk-high-border rounded-md px-3 py-2">
                {error}
              </div>
            )}
            <Button type="submit" disabled={submitting} fullWidth size="lg">
              {submitting ? "signing in…" : "sign in"}
            </Button>
          </form>
          <p className="font-mono text-[0.65rem] text-ink/40 mt-10 leading-relaxed">
            demo accounts: physician@ · nurse@ · casemanager@ · admin@careinsight.dev
            <br />
            password: Demo123!
          </p>
        </div>
      </div>
    </div>
  );
}
