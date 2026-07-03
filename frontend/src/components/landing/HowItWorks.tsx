import { motion } from "framer-motion";
import { EASE, fadeUp, VIEWPORT } from "./motion";

const STEPS = [
  ["01", "Predict", "Readmission risk scored at admission — explained factor by factor, not a black box."],
  ["02", "Plan", "Risk factors become discharge tasks, each assigned to the right role automatically."],
  ["03", "Discharge", "The checklist clears, the patient leaves — with a 30-day follow-up plan already scheduled."],
  ["04", "Follow up", "WhatsApp check-ins track recovery. A concerning answer reaches a case manager in minutes."],
] as const;

export function HowItWorks() {
  return (
    <section className="mx-auto max-w-7xl px-6 py-24 md:px-10 md:py-32">
      <motion.h2
        variants={fadeUp}
        initial="hidden"
        whileInView="visible"
        viewport={VIEWPORT}
        className="mb-16 font-hero text-4xl font-bold tracking-[-0.03em] text-ink md:text-6xl"
      >
        How it <em className="font-serifit font-normal italic">works.</em>
      </motion.h2>

      <div>
        {STEPS.map(([num, title, body], i) => (
          <motion.div
            key={num}
            initial="hidden"
            whileInView="visible"
            viewport={VIEWPORT}
            className="relative py-10 md:py-12"
          >
            <motion.span
              variants={{
                hidden: { scaleX: 0 },
                visible: { scaleX: 1, transition: { duration: 1, ease: EASE } },
              }}
              className="absolute inset-x-0 top-0 h-px origin-left bg-ink/15"
            />
            <motion.div
              variants={fadeUp}
              custom={i * 0.5}
              className="flex flex-col gap-4 md:flex-row md:items-baseline md:gap-16"
            >
              <span className="font-hero text-2xl font-bold text-ink/25 md:w-24">{num}</span>
              <span className="font-hero text-3xl font-bold tracking-tight text-ink md:w-72 md:text-4xl">
                {title}
              </span>
              <span className="max-w-xl text-base leading-relaxed text-ink/60">{body}</span>
            </motion.div>
          </motion.div>
        ))}
      </div>
    </section>
  );
}
