import Link from "next/link";
import Vinyl from "../components/vinyl";

export default function BuilderPage() {
  return (
    <main className="grid min-h-dvh grid-cols-1 overflow-x-hidden lg:grid-cols-[380px_1fr]">
      {/* left side, vinyl + go back home + block */}
      <section className="relative hidden bg-[#2A6F86] lg:block">
      <Link href="/" className="underline">← Back home</Link>
        <div className="absolute top-1/2 -translate-y-1/2 -left-80 md:-left-70">
          <Vinyl
            src="/jellyvinyl.png"
            alt=""
            size={620}
            speed={6}
          />
        </div>
      </section>

      {/* right side, message + chat stuff */}
      <section className="relative min-h-screen overflow-hidden">
        <div aria-hidden="true" className="absolute inset-0 -z-10 bg-[url('/djmjbackground.png')] bg-cover bg-center blur-xl transform-gpu scale-105"
        ></div>
        <div className="relative p-10 space-y-4 text-[#F9F0F2]">
        <h1 className={"text-6xl font-['Bodega'] text-center"}>DJ MEGAJELLI BUILDER</h1>
          <p className="mt-4 max-w-lg">Chat your vibe here…</p>
        </div>
      </section>
    </main>
  );
}