import Link from "next/link";

export default function AboutPage() {
  return (
    <div className="p-6 space-y-4">
      <h1 className="text-2xl font-semibold">About</h1>
      <p>This app builds a vibe-based Spotify playlist.</p>
      <Link href="/" className="underline">← Back home</Link>
    </div>
  );
}