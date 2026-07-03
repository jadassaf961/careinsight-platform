import { useRef } from "react";
import { useMotionValue, useSpring } from "framer-motion";

/** Element translates toward the cursor while hovered, springs back on leave.
 * Spread the returned handlers/style onto a motion element. */
export function useMagnetic<T extends HTMLElement>(strength = 0.35) {
  const ref = useRef<T>(null);
  const mx = useMotionValue(0);
  const my = useMotionValue(0);
  const x = useSpring(mx, { stiffness: 180, damping: 12, mass: 0.2 });
  const y = useSpring(my, { stiffness: 180, damping: 12, mass: 0.2 });

  function onMouseMove(e: React.MouseEvent) {
    const el = ref.current;
    if (!el) return;
    const r = el.getBoundingClientRect();
    mx.set((e.clientX - (r.left + r.width / 2)) * strength);
    my.set((e.clientY - (r.top + r.height / 2)) * strength);
  }

  function onMouseLeave() {
    mx.set(0);
    my.set(0);
  }

  return { ref, style: { x, y }, onMouseMove, onMouseLeave };
}
