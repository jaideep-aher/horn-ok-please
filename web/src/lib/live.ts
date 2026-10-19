/** Public and static builds leave this unset. Set NEXT_PUBLIC_LIVE_MODE=1 to show the key dialog. */
export const liveMode = process.env.NEXT_PUBLIC_LIVE_MODE === "1";
