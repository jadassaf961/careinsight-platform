import { useRef } from "react";
import { motion, useScroll, useTransform } from "framer-motion";
import { fadeUp, VIEWPORT } from "./motion";
import { BoardVignette, PhoneVignette, QueueVignette } from "./vignettes";

export function ProductShowcase() {
  const ref = useRef<HTMLDivElement>(null);
  const { scrollYProgress } = useScroll({ target: ref, offset: ["start end", "end start"] });
  const parallax = useTransform(scrollYProgress, [0, 1], ["4%", "-4%"]);

  return (
    <section id="product" ref={ref} className="bg-ink py-24 text-paper md:py-32">
      <div className="mx-auto max-w-7xl px-6 md:px-10">
        <motion.div variants={fadeUp} initial="hidden" whileInView="visible" viewport={VIEWPORT}>
          <div className="mb-4 font-hero text-xs font-semibold uppercase tracking-[0.25em] text-white/40">
            The platform
          </div>
          <h2 className="max-w-3xl font-hero text-4xl font-bold leading-[1.05] tracking-[-0.03em] md:text-6xl">
            The discharge board your ward opens{" "}
            <em className="font-serifit font-normal italic">every morning.</em>
          </h2>
        </motion.div>

        <motion.div style={{ y: parallax }} className="mt-14">
          <motion.div variants={fadeUp} initial="hidden" whileInView="visible" viewport={VIEWPORT} custom={1}>
            <BoardVignette />
          </motion.div>
        </motion.div>

        <div className="mt-6 grid gap-6 md:grid-cols-2">
          <motion.div variants={fadeUp} initial="hidden" whileInView="visible" viewport={VIEWPORT} custom={2}>
            <PhoneVignette />
            <p className="mt-4 max-w-sm text-sm leading-relaxed text-white/50">
              Automated WhatsApp check-ins on days 2, 7, 14 and 30 — in Arabic
              and English. Concerning answers escalate to a human within minutes.
            </p>
          </motion.div>
          <motion.div variants={fadeUp} initial="hidden" whileInView="visible" viewport={VIEWPORT} custom={3}>
            <QueueVignette />
            <p className="mt-4 max-w-sm text-sm leading-relaxed text-white/50">
              Case managers work one priority-sorted queue. Nothing is silently
              dropped — unreachable patients become phone calls, not statistics.
            </p>
          </motion.div>
        </div>
      </div>
    </section>
  );
}
