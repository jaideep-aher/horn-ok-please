import type { Metadata } from "next";
import { Barlow_Condensed, Fraunces, Noto_Sans_Devanagari, Source_Sans_3 } from "next/font/google";

import "./globals.css";

const display = Fraunces({
  subsets: ["latin"],
  variable: "--font-fraunces",
  display: "swap",
});

const stencil = Barlow_Condensed({
  subsets: ["latin"],
  weight: ["500", "600", "700"],
  variable: "--font-barlow",
  display: "swap",
});

const sans = Source_Sans_3({
  subsets: ["latin"],
  variable: "--font-source",
  display: "swap",
});

const deva = Noto_Sans_Devanagari({
  subsets: ["devanagari"],
  weight: ["500", "700"],
  variable: "--font-noto-deva",
  display: "swap",
});

export const metadata: Metadata = {
  title: "Horn OK Please",
  description:
    "Can painted text on a truck or a road change a vision-language model's driving action? An audit by Jaideep (Jay) Aher for Duke AIPI 590.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className={`${display.variable} ${stencil.variable} ${sans.variable} ${deva.variable}`}>
      <body className="antialiased">{children}</body>
    </html>
  );
}
