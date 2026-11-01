import Link from "next/link";
import { BookOpenText, Brain, FileText, Mic, Sparkles } from "lucide-react";
import { buttonVariants } from "@/components/ui/button";
import { ThemeToggle } from "@/components/theme";
import { cn } from "@/lib/utils";

const FEATURES = [
  { icon: FileText, title: "Any source", body: "Textbooks, screenshots, emails, articles and your own notes become study material." },
  { icon: BookOpenText, title: "Grammar built in", body: "Articles, plurals, conjugations, cases and prepositions on every card — only the fields that apply." },
  { icon: Mic, title: "Speak to learn", body: "Say a sentence and get cards for the words that matter, with pronunciation." },
  { icon: Brain, title: "Remember it", body: "Spaced repetition schedules each word right before you'd forget it." },
];

export default function Landing() {
  return (
    <div className="mx-auto max-w-6xl px-4 sm:px-6">
      <header className="flex h-16 items-center justify-between">
        <Link href="/" className="font-display text-xl font-semibold tracking-tight">
          SmartVocab<span className="text-accent"> AI</span>
        </Link>
        <nav className="flex items-center gap-2">
          <ThemeToggle />
          <Link href="/login" className={buttonVariants({ variant: "ghost", size: "sm" })}>Sign in</Link>
          <Link href="/register" className={buttonVariants({ size: "sm" })}>Get started</Link>
        </nav>
      </header>

      <section className="grid gap-12 py-16 md:grid-cols-[1.2fr_1fr] md:py-24">
        <div>
          <p className="mb-4 inline-flex items-center gap-2 rounded-full border border-line bg-surface px-3 py-1 text-xs text-muted">
            <Sparkles className="h-3.5 w-3.5 text-accent" /> German · explained in English and Hindi
          </p>
          <h1 className="font-display text-4xl leading-[1.1] tracking-tight sm:text-6xl">
            Learn the words you actually meet.
          </h1>
          <p className="mt-6 max-w-xl text-lg text-muted">
            Photograph a page, paste an email, or speak a sentence. SmartVocab pulls out the vocabulary that matters,
            explains the grammar in context, and helps you use it in real conversations.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Link href="/register" className={buttonVariants({ size: "lg" })}>Create free account</Link>
            <Link href="/login" className={buttonVariants({ variant: "secondary", size: "lg" })}>I have an account</Link>
          </div>
        </div>

        {/* Sample card — shows the shape of what the app produces. */}
        <div className="relative">
          <div className="absolute -inset-4 -z-10 rounded-[28px] bg-accent/10 blur-2xl" aria-hidden />
          <div className="rounded-2xl border border-line bg-surface p-6 shadow-sm">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-xs uppercase tracking-widest text-muted">Verb · B1</p>
                <p className="mt-1 font-display text-3xl">vereinbaren</p>
                <p className="text-muted">to arrange, to agree</p>
              </div>
            </div>
            <div className="mt-5 rounded-xl bg-bg p-3 text-sm">
              <p className="italic">„Wir müssen einen Termin <mark className="rounded bg-accent/20 px-0.5 text-ink">vereinbaren</mark>.“</p>
              <p className="mt-1 text-muted">We need to arrange an appointment.</p>
            </div>
            <dl className="mt-5 grid grid-cols-3 gap-3 text-sm">
              <div><dt className="text-xs text-muted">Präteritum</dt><dd>vereinbarte</dd></div>
              <div><dt className="text-xs text-muted">Perfekt</dt><dd>hat vereinbart</dd></div>
              <div><dt className="text-xs text-muted">Objekt</dt><dd>Akkusativ</dd></div>
            </dl>
            <p className="mt-5 text-xs text-muted">Collocations</p>
            <div className="mt-1 flex flex-wrap gap-1.5 text-sm">
              {["einen Termin vereinbaren", "einen Preis vereinbaren"].map((c) => (
                <span key={c} className="rounded-full border border-line px-2.5 py-0.5">{c}</span>
              ))}
            </div>
          </div>
        </div>
      </section>

      <section className="grid gap-4 pb-24 sm:grid-cols-2 lg:grid-cols-4">
        {FEATURES.map(({ icon: Icon, title, body }) => (
          <div key={title} className="rounded-2xl border border-line bg-surface p-5">
            <Icon className="h-5 w-5 text-accent" />
            <h2 className="mt-3 font-medium">{title}</h2>
            <p className={cn("mt-1 text-sm text-muted")}>{body}</p>
          </div>
        ))}
      </section>
    </div>
  );
}
