"use client";

import ScrollHint from "./components/scrollhint";
import LoginButton from "./components/loginbutton";
import localFont from "next/font/local";
import { useEffect } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";

const titleFont = localFont({
  src: [{ path: "../fonts/CSBodegaDrawn-Regular_demo-BF68edcdd4e3b5f.otf", weight: "400", style: "normal" }],
  display: "swap",
  variable: "--font-title", // gives you a CSS var for Tailwind later
});

const ClientInit = () => {
  const router = useRouter();
  const pathname = usePathname();
  const search = useSearchParams();
  const userId = search.get("user");

  useEffect(() => {
    if (!userId) return;
    // store it anywhere you like (localStorage, context, etc.)
    localStorage.setItem("spotify_user_id", userId);
    console.log(userId);
    // remove the query from the URL without reloading
    router.replace(pathname);
  }, [userId, pathname, router]);

  return null; // nothing to render
}

export default function Page() {
  return (
    <div className="min-h-dvh w-full flex flex-col justify-center items-center p-6 space-y-6">

      <ClientInit />
      <ScrollHint label="scroll!" />

      <div className="flex flex-col space-y-5">
        <h1 className={`text-9xl font-semibold ${titleFont.className}`}>DJ Mega Jellyfish</h1>
      </div>

      <div className="grid">
        <div className="text-2xl">
           "Waves haven't sounded this good since Moses parted the Red Sea."
        </div>
        <div>
          nah that text above was filler i'm sorry
        </div>
      </div>

      <LoginButton className="hover:cursor-pointer"/>
    </div>
  );
}