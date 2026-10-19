"use client";

/** Stand-in used when NEXT_PUBLIC_LIVE_MODE is not 1. It must not import the dialog. */
export function LiveDialog(props: {
  imageUrl?: string;
  canSend?: boolean;
  defense?: "none" | "prompt" | "ocr";
  triggerLabel?: string;
}) {
  void props;
  return null;
}
