"use client";

import dynamic from "next/dynamic";

/** Loaded only when the webpack alias swaps this in for NEXT_PUBLIC_LIVE_MODE=1. */
export const LiveDialog = dynamic(
  () => import("@/components/live-dialog").then((mod) => mod.LiveDialog),
  { ssr: false },
);
