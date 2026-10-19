/** Prefix for a project site at jaideep-aher.github.io/horn-ok-please. Empty only if the build omits it. */
export const basePath = process.env.NEXT_PUBLIC_BASE_PATH || "";

/** Next does not prefix a raw img src or fetch() with basePath. */
export function asset(path: string): string {
  if (!path) return path;
  if (path.startsWith("http://") || path.startsWith("https://")) return path;
  const suffix = path.startsWith("/") ? path : `/${path}`;
  return `${basePath}${suffix}`;
}
