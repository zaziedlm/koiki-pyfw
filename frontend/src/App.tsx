import { ArrowRight, CheckCircle2, KeyRound, ShieldCheck } from "lucide-react";

import { Button } from "@/components/ui/button";
import { config } from "@/lib/config";

const highlights = [
  {
    icon: CheckCircle2,
    title: "Tasks",
    description: "Track daily work with the existing task dashboard experience.",
  },
  {
    icon: KeyRound,
    title: "Session Auth",
    description: "Use backend-managed Cookie sessions without a Next.js BFF.",
  },
  {
    icon: ShieldCheck,
    title: "CSRF Guard",
    description: "Keep browser state-changing requests protected at the API boundary.",
  },
];

export function App() {
  return (
    <main className="min-h-screen bg-background text-foreground">
      <section className="mx-auto flex min-h-screen w-full max-w-6xl flex-col px-6 py-6">
        <header className="flex items-center justify-between border-b pb-4">
          <div>
            <h1 className="text-xl font-semibold">{config.app.name}</h1>
            <p className="text-sm text-muted-foreground">Vite React SPA</p>
          </div>
          <nav className="flex items-center gap-2">
            <Button asChild variant="ghost">
              <a href="/auth/login">Sign In</a>
            </Button>
            <Button asChild>
              <a href="/dashboard">
                Dashboard
                <ArrowRight className="size-4" />
              </a>
            </Button>
          </nav>
        </header>

        <div className="grid flex-1 items-center gap-8 py-10 lg:grid-cols-[1.1fr_0.9fr]">
          <section className="space-y-6">
            <div className="space-y-3">
              <p className="text-sm font-medium uppercase tracking-wide text-muted-foreground">
                React SPA Migration
              </p>
              <h2 className="max-w-3xl text-4xl font-semibold leading-tight md:text-5xl">
                Frontend shell running on Vite.
              </h2>
              <p className="max-w-2xl text-lg text-muted-foreground">
                This scaffold keeps the existing design system and provider stack available while
                the Next.js route surface is replaced by client-side routes.
              </p>
            </div>

            <div className="flex flex-wrap gap-3">
              <Button asChild size="lg">
                <a href="/auth/login">Continue to Login</a>
              </Button>
              <Button asChild size="lg" variant="outline">
                <a href="/auth/register">Create Account</a>
              </Button>
            </div>
          </section>

          <section className="grid gap-3">
            {highlights.map((item) => (
              <article
                className="rounded-lg border bg-card p-5 text-card-foreground shadow-sm"
                key={item.title}
              >
                <div className="mb-4 flex size-10 items-center justify-center rounded-md bg-secondary">
                  <item.icon className="size-5" />
                </div>
                <h3 className="text-base font-semibold">{item.title}</h3>
                <p className="mt-1 text-sm leading-6 text-muted-foreground">{item.description}</p>
              </article>
            ))}
          </section>
        </div>
      </section>
    </main>
  );
}
