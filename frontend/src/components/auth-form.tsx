"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { FormError, Input, Label } from "@/components/ui/form";
import { api, ApiError } from "@/lib/api";

export function AuthForm({ mode }: { mode: "login" | "register" }) {
  const router = useRouter();
  const params = useSearchParams();
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const isRegister = mode === "register";

  async function onSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const f = new FormData(e.currentTarget);
    setError(null);
    setLoading(true);
    try {
      const email = String(f.get("email"));
      const password = String(f.get("password"));
      if (isRegister) await api.register(email, password, String(f.get("display_name")));
      else await api.login(email, password);
      const next = params.get("next");
      router.replace(next && next.startsWith("/") && !next.startsWith("//") ? next : "/dashboard");
      router.refresh();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong. Please try again.");
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto flex min-h-screen max-w-sm flex-col justify-center px-4 py-12">
      <Link href="/" className="mb-10 font-display text-xl font-semibold">
        SmartVocab<span className="text-accent"> AI</span>
      </Link>
      <h1 className="font-display text-3xl">{isRegister ? "Create your account" : "Welcome back"}</h1>
      <p className="mt-2 text-sm text-muted">
        {isRegister ? "Start building your German vocabulary." : "Sign in to continue learning."}
      </p>
      <form onSubmit={onSubmit} className="mt-8 space-y-4" noValidate={false}>
        {isRegister && (
          <div>
            <Label htmlFor="display_name">Name</Label>
            <Input id="display_name" name="display_name" autoComplete="name" required maxLength={80} />
          </div>
        )}
        <div>
          <Label htmlFor="email">Email</Label>
          <Input id="email" name="email" type="email" autoComplete="email" required />
        </div>
        <div>
          <Label htmlFor="password" hint={isRegister ? "(10+ characters, with a number)" : undefined}>Password</Label>
          <Input
            id="password" name="password" type="password" required
            minLength={isRegister ? 10 : 1} maxLength={72}
            autoComplete={isRegister ? "new-password" : "current-password"}
          />
        </div>
        <FormError message={error} />
        <Button type="submit" className="w-full" loading={loading}>
          {isRegister ? "Create account" : "Sign in"}
        </Button>
      </form>
      <p className="mt-6 text-center text-sm text-muted">
        {isRegister ? "Already have an account? " : "New here? "}
        <Link href={isRegister ? "/login" : "/register"} className="font-medium text-accent hover:underline">
          {isRegister ? "Sign in" : "Create an account"}
        </Link>
      </p>
    </div>
  );
}
