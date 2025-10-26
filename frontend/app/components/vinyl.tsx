import * as React from "react";

export type VinylProps = Omit<React.ImgHTMLAttributes<HTMLImageElement>, "width" | "height"> & {
  /** Required image source */
  src: string;
  /** Accessible alt text */
  alt?: string;
  /** Final rendered size — number (px) or any CSS size (e.g., "8rem") */
  size?: number | string;
  /** Seconds per rotation (default 2) */
  speed?: number;
  /** Tailwind rounded utility (default: "rounded-full") */
  rounded?: string;
};

const Vinyl: React.FC<VinylProps> = ({
  src,
  alt = "",
  size = 128,
  speed = 2,
  rounded = "rounded-full",
  className,
  style,
  draggable = false,
  ...imgProps
}) => {
  const dimension = typeof size === "number" ? `${size}px` : size;

  const classes = [
    "animate-spin select-none object-cover shadow-lg",
    rounded,
    className || "",
  ]
    .filter(Boolean)
    .join(" ");

  const containerStyle: React.CSSProperties = {
    width: dimension,
    height: dimension,
  };

  const imageStyle: React.CSSProperties = {
    width: "100%",
    height: "100%",
    animationDuration: `${speed}s`, // customize speed without editing tailwind.config
    ...style,
  };

  return (
    <div className="relative grid place-items-center" style={containerStyle} aria-busy="true">
      <img src={src} alt={alt} draggable={draggable} className={classes} style={imageStyle} {...imgProps} />
    </div>
  );
};

export default Vinyl;