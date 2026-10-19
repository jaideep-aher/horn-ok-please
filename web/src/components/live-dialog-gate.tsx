"use client";

/**
 * Default export path for the public build. next.config.ts points this module
 * at live-dialog-on only when NEXT_PUBLIC_LIVE_MODE=1, and that file is the
 * one that dynamic-imports the key dialog.
 */
export { LiveDialog } from "@/components/live-dialog-off";
