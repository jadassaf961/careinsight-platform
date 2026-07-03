import { motion } from "framer-motion";
import { fadeUp, VIEWPORT } from "./motion";
import { PillButton } from "./PillButton";

export function Pricing() {
  return (
    <section id="pricing" className="mx-auto max-w-7xl px-6 py-24 md:px-10 md:py-32">
      <motion.div
        variants={fadeUp}
        initial="hidden"
        whileInView="visible"
        viewport={VIEWPORT}
        className="mx-auto max-w-3xl text-center"
      >
        <div className="mb-4 font-hero text-xs font-semibold uppercase tracking-[0.25em] text-ink/40">
          Pricing
        </div>
        <h2 className="font-hero text-6xl font-bold tracking-[-0.04em] text-ink md:text-8xl">
          $12<em className="font-serifit text-4xl font-normal italic md:text-6xl">/bed/month.</em>
        </h2>
        <p className="mx-auto mt-6 max-w-md text-base leading-relaxed text-ink/60">
          Every module. Every role. No seat licenses, no surprises. Works
          alongside any hospital information system — no EHR migration required.
        </p>
        <div className="mt-10">
          <PillButton href="mailto:jadassaf6000@gmail.com?subject=CareInsight%20demo%20request">
            book a demo
          </PillButton>
        </div>
      </motion.div>
    </section>
  );
}
