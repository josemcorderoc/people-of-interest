import { useState } from "react";

interface PersonImageProps {
  src: string | null;
  alt: string;
  size?: number;
}

export default function PersonImage({ src, alt, size = 40 }: PersonImageProps) {
  const [error, setError] = useState(false);

  if (!src || error) {
    return (
      <div
        className="bg-gray-200 rounded-full flex items-center justify-center text-gray-400 text-xs font-bold"
        style={{ width: size, height: size }}
      >
        {alt.charAt(0).toUpperCase()}
      </div>
    );
  }

  return (
    <img
      src={src}
      alt={alt}
      loading="lazy"
      onError={() => setError(true)}
      className="rounded-full object-cover"
      style={{ width: size, height: size }}
    />
  );
}
