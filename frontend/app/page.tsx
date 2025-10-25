import Link from "next/link";
import ScrollHint from "./components/scrollhint";
import localFont from "next/font/local";

const titleFont = localFont({
  src: [{ path: "../fonts/CSBodegaDrawn-Regular_demo-BF68edcdd4e3b5f.otf", weight: "400", style: "normal" }],
  display: "swap",
  variable: "--font-title", // gives you a CSS var for Tailwind later
});

export default function Page() {
  return (
    <div className="min-h-dvh w-full flex flex-col justify-center items-center p-6">

      <ScrollHint label="scroll!" />

      <div className="flex flex-col space-y-5">
        <h1 className={`text-9xl font-semibold ${titleFont.className}`}>DJ Mega Jellyfish</h1>
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