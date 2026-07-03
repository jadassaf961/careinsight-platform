import { motion } from "framer-motion";
import { fadeUp, VIEWPORT } from "./motion";
import { PillButton } from "./PillButton";

export function LandingFooter() {
  return (
    <footer className="bg-ink py-24 text-paper md:py-32">
      <div className="mx-auto max-w-7xl px-6 md:px-10">
        <motion.div variants={fadeUp} initial="hidden" whileInView="visible" viewport={VIEWPORT}>
          <div className="mb-4 font-hero text-xs font-semibold uppercase tracking-[0.25em] text-white/40">
            Ready when you are
          </div>
          <h2 className="font-hero text-5xl font-bold leading-[1.02] tracking-[-0.03em] md:text-8xl">
            Bring CareInsight to{" "}
            <em className="font-serifit font-normal italic">your hospital.</em>
          </h2>
          <div className="mt-10">
            <PillButton
              tone="paper"
              href="mailto:jadassaf6000@gmail.com?subject=CareInsight%20demo%20request"
            >
              book a demo
            </PillButton>
          </div>
          <a
            href="mailto:jadassaf6000@gmail.com"
            className="mt-16 block font-serifit text-2xl italic text-white/60 transition-colors hover:text-white md:text-4xl"
          >
            jadassaf6000@gmail.com
          </a>
          <div className="mt-12 border-t border-white/10 pt-6 font-hero text-xs text-white/30">
            careinsight — beirut · 2026
          </div>
        </motion.div>
      </div>
    </footer>
  );
}
