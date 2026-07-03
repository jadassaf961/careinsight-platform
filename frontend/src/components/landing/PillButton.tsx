import { motion } from "framer-motion";
import { EASE } from "./motion";
import { useMagnetic } from "./useMagnetic";

interface PillButtonProps {
  children: React.ReactNode;
  href: string;
  /** "ink" = dark border on light bg; "paper" = light border on dark bg */
  tone?: "ink" | "paper";
  className?: string;
}

/** Bordered pill CTA: magnetic, with a fill-sweep hover. */
export function PillButton({ children, href, tone = "ink", className = "" }: PillButtonProps) {
  const m = useMagnetic<HTMLAnchorElement>(0.25);
  const border = tone === "ink" ? "border-ink text-ink" : "border-paper text-paper";
  const fill = tone === "ink" ? "bg-ink" : "bg-paper";
  const hoverText = tone === "ink" ? "group-hover:text-paper" : "group-hover:text-ink";

  return (
    <motion.a
      ref={m.ref}
      style={m.style}
      onMouseMove={m.onMouseMove}
      onMouseLeave={m.onMouseLeave}
      href={href}
      initial="rest"
      whileHover="hover"
      animate="rest"
      className={`group relative inline-flex items-center gap-2 overflow-hidden rounded-full border-[1.5px] px-7 py-3 font-hero text-sm font-semibold tracking-tight ${border} ${className}`}
    >
      <motion.span
        aria-hidden
        variants={{ rest: { y: "101%" }, hover: { y: "0%" } }}
        transition={{ duration: 0.35, ease: EASE }}
        className={`absolute inset-0 ${fill}`}
      />
      <span className={`relative z-10 transition-colors duration-300 ${hoverText}`}>
        {children}
      </span>
    </motion.a>
  );
}
