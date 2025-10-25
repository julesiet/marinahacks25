// WHY: Render a small, non-intrusive “scroll” arrow that fades out at the bottom.
// WHAT: Listens to scroll position on the client; toggles opacity based on whether you're near the page bottom.
"use client";

import * as React from "react";

type Props = {
  label?: string;          // text under the arrow ("Scroll")
  bottomOffsetPx?: number; // how close to bottom to consider "at bottom"
};

export default function ScrollHint({ label = "Scroll", bottomOffsetPx = 24 }: Props) {
  const [atBottom, setAtBottom] = React.useState(false);

  React.useEffect(() => {
    const onScroll = () => {
      const doc = document.documentElement;
      const atBottomNow = window.scrollY + window.innerHeight >= doc.scrollHeight - bottomOffsetPx;
      setAtBottom(atBottomNow);
    };
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("resize", onScroll);
    return () => {
      window.removeEventListener("scroll", onScroll);
      window.removeEventListener("resize", onScroll);
    };
  }, [bottomOffsetPx]);

  return (
    <div
      className={[
        "pointer-events-none fixed inset-x-0 bottom-6 z-10",
        "flex items-center justify-center",
        "transition-opacity duration-500",
        atBottom ? "opacity-0" : "opacity-100",
      ].join(" ")}
      aria-hidden
    >
      <div className="flex flex-col items-center gap-1 text-white/90 drop-shadow animate-bounce-slow">
        <svg
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 24 24"
          fill="currentColor"
          className="h-9 w-9"
        >
          <path d="M12 16a1 1 0 0 1-.707-.293l-5-5a1 1 0 0 1 1.414-1.414L12 13.586l4.293-4.293a1 1 0 0 1 1.414 1.414l-5 5A1 1 0 0 1 12 16z" />
        </svg>
        <span className="text-[11px] tracking-wide">{label}</span>
      </div>
    </div>
  );
}
