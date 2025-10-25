import Link from "next/link";

export default function BuilderPage() {
  return (
    <div className="p-6 space-y-4">
      <h1 className="text-2xl font-semibold">Builder</h1>
      <p>Chat your vibe here…</p>
      <Link href="/" className="underline">← Back home</Link>
    </div>
  );
}