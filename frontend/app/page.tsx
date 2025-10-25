import Link from "next/link";

export default function Page() {
  return (
    <main className="p-6 space-y-4">
      <h1 className="text-2xl font-semibold">Home</h1>
      <p>Choose where to go:</p>
      <nav className="space-x-4">
        <Link href="/builder" className="underline">Go to Builder</Link>
        <Link href="/about" className="underline">About</Link>
      </nav>
    </main>
  );
}