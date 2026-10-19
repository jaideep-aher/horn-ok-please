import { asset, basePath } from "@/lib/asset";
import sizesJson from "@/lib/image-sizes.json";

const sizes = sizesJson as Record<string, { width: number; height: number }>;

function publicPath(src: string): string {
  if (basePath && (src === basePath || src.startsWith(`${basePath}/`))) {
    const bare = src.slice(basePath.length);
    return bare.startsWith("/") ? bare : `/${bare}`;
  }
  return src.startsWith("/") ? src : `/${src}`;
}

export function Picture({
  src,
  alt,
  className,
  priority = false,
}: {
  src: string;
  alt: string;
  className?: string;
  priority?: boolean;
}) {
  const path = publicPath(src);
  const size = sizes[path];
  const match = path.match(/\.(png|jpe?g|webp)$/i);
  const ext = match?.[0].toLowerCase() ?? "";
  const stem = ext ? path.slice(0, -ext.length) : path;
  const fallback = asset(path);

  return (
    <picture className="block w-full">
      {ext ? <source srcSet={asset(`${stem}.avif`)} type="image/avif" /> : null}
      {ext && ext !== ".webp" ? <source srcSet={asset(`${stem}.webp`)} type="image/webp" /> : null}
      <img
        src={fallback}
        alt={alt}
        width={size?.width}
        height={size?.height}
        className={className}
        loading={priority ? "eager" : "lazy"}
        decoding="async"
        fetchPriority={priority ? "high" : undefined}
      />
    </picture>
  );
}
