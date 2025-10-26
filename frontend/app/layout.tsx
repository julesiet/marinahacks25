import Link from "next/link";
import Image from "next/image";
import "./globals.css";
import bg from "@/public/djmjbackground.jpg";

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-dvh">
        <div className="relative min-h-dvh flex flex-col">
          <Image
            src={bg}
            alt=""
            fill
            priority
            sizes="100vw"
            className="object-cover -z-10"
          />
          <div className="absolute inset-0 -z-10 bg-black/35" />

            <Link href="/profile">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                width="42"
                height="40"
                fill="currentColor"
                className="hover:cursor-pointer absolute right-5 top-5"
                viewBox="0 0 16 16"
              >
                <path d="M11 6a3 3 0 1 1-6 0 3 3 0 0 1 6 0" />
                <path d="M0 8a8 8 0 1 1 16 0A8 8 0 0 1 0 8m8-7a7 7 0 0 0-5.468 11.37C3.242 11.226 4.805 10 8 10s4.757 1.225 5.468 2.37A7 7 0 0 0 8 1" />
              </svg>
            </Link>

          <main className="flex-1">{children}</main>
        </div>
      </body>
    </html>
  );
}
