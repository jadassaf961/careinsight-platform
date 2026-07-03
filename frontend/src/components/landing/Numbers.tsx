import { useEffect, useRef } from "react";
import { animate, motion, useInView } from "framer-motion";
import { EASE, fadeUp, VIEWPORT } from "./motion";

function Counter({ to }: { to: number }) {
  const ref = useRef<HTMLSpanElement>(null);
  const inView = useInView(ref, { once: true, amount: 0.6 });

  useEffect(() => {
    if (!inView || !ref.current) return;
    const controls = animate(0, to, {
      duration: 1.6,
      ease: EASE as unknown as [number, number, number, number],
      onUpdate: (v) => {
        if (ref.current) ref.current.textContent = String(Math.round(v));
      },
    });
    return () => controls.stop();
  }, [inView, to]);

  return <span ref={ref}>0</span>;
}

const STATS = [
  { value: 30, suffix: "days", body: "of automated follow-up after every discharge — Arabic and English" },
  { value: 4, suffix: "roles", body: "physicians, nurses, pharmacists and case managers on one checklist" },
  { value: 94, suffix: "% response", body: "pilot check-in response rate — patients actually answer WhatsApp" },
] as const;

export function Numbers() {
  return (
    <section id="outcomes" className="border-y border-hairline bg-tint">
      <div className="mx-auto grid max-w-7xl gap-12 px-6 py-20 md:grid-cols-3 md:px-10 md:py-28">
        {STATS.map((s, i) => (
          <motion.div
            key={s.suffix}
            variants={fadeUp}
            initial="hidden"
            whileInView="visible"
            viewport={VIEWPORT}
            custom={i}
          >
            <div className="font-hero text-6xl font-bold tracking-[-0.04em] text-ink md:text-7xl">
              <Counter to={s.value} />
              <em className="ml-2 font-serifit text-4xl font-normal italic md:text-5xl">{s.suffix}</em>
            </div>
            <p className="mt-4 max-w-xs text-sm leading-relaxed text-ink/55">{s.body}</p>
          </motion.div>
        ))}
      </div>
    </section>
  );
}
