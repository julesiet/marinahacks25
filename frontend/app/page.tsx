import Link from "next/link";

export default function Page() {
  return (
    <div className="min-h-dvh w-full flex flex-col justify-center items-center p-6">
      <div className="flex flex-col space-y-5">
        <h1 className="text-2xl font-semibold">DJ Mega Jellyfish</h1>
        <p>Choose where to go:</p>
        <nav className="space-x-4">
          <a href="/builder" className="underline">Go to Builder</a>
          <a href="/about" className="underline">About</a>
        </nav>
      </div>

      <div className="grid">
        <div>
          evil
        </div>
        <div>
          not evil
        </div>
      </div>
    </div>
  );
}