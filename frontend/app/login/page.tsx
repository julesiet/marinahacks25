"use client";
import LoginButton from "@/app/components/loginbutton";

export default function LoginPage() {
  return (
    <main className="flex min-h-screen items-center justify-center p-6">
      <div className="max-w-sm w-full space-y-4 text-center">
        <h1 className="text-2xl font-semibold">Sign in</h1>
        <p className="text-sm text-neutral-600">Continue with your Spotify account.</p>
        <div className="flex justify-center">
          <LoginButton />
        </div>
      </div>
    </main>
  );
}
