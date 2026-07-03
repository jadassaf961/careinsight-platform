import { useRef, useState } from "react";
import {
  motion,
  useAnimationFrame,
  useMotionValue,
  useScroll,
  useSpring,
  useTransform,
  useVelocity,
} from "framer-motion";

const ITEMS = ["predict", "plan", "discharge", "follow up"];
const BASE_SPEED = 4; // percent of half-width per second

export function Marquee() {
  const baseX = useMotionValue(0);
  const { scrollY } = useScroll();
  const velocity = useVelocity(scrollY);
  const smooth = useSpring(velocity, { damping: 50, stiffness: 400 });
  const factor = useTransform(smooth, [0, 1200], [0, 4], { clamp: false });
  const [paused, setPaused] = useState(false);
  const pausedRef = useRef(paused);
  pausedRef.current = paused;

  useAnimationFrame((_, delta) => {
    if (pausedRef.current) return;
    let moveBy = -BASE_SPEED * (delta / 1000);
    moveBy *= 1 + Math.abs(factor.get());
    let next = baseX.get() + moveBy;
    if (next <= -50) next += 50;
    if (next > 0) next -= 50;
    baseX.set(next);
  });

  const x = useTransform(baseX, (v) => `${v}%`);
  const half = [...ITEMS, ...ITEMS, ...ITEMS, ...ITEMS];

  return (
    <div
      className="overflow-hidden border-y border-ink py-4"
      onMouseEnter={() => setPaused(true)}
      onMouseLeave={() => setPaused(false)}
      aria-hidden
    >
      <motion.div style={{ x }} className="flex w-max whitespace-nowrap">
        {[0, 1].map((copy) => (
          <div key={copy} className="flex shrink-0">
            {half.map((item, i) => (
              <span
                key={`${copy}-${i}`}
                className="px-6 font-hero text-2xl font-bold tracking-tight text-ink md:text-3xl"
              >
                {item} <span className="px-4 text-ink/30">·</span>
              </span>
            ))}
          </div>
        ))}
      </motion.div>
    </div>
  );
}
