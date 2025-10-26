"use client";

import ScrollHint from "./components/scrollhint";
import LoginButton from "./components/loginbutton";
import localFont from "next/font/local";
import { useEffect } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import Vinyl from "./components/vinyl";

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

      <Vinyl
        src="/jellyvinyl.png"
        alt=""
        size={550}
        speed={6}
      />

      <div className="flex flex-col space-y-5">
        <h1 className={`text-9xl font-semibold ${titleFont.className}`}>DJ MEGAJELLI</h1>
      </div>

      <div className="flex rounded-[25px] py-[35px] px-[90px] bg-[#006B8F]">
        <div className="grid place-items-center">
          <div className="text-3xl text-center">
            "Waves haven't sounded this good since Moses parted the Red Sea."
          </div>
          <div className="text-lg text-center pb-[20px] pt-[10px]">
            DJ MegaJelli is the next best playlist maker! Log in with your Spotify and chat with
            <br />MegaJelli about your current vibe to get a personalized playlist fit for your liking!
          </div>
          <LoginButton className="hover:cursor-pointer "/>
        </div>
      </div>

    </div>
  );
}