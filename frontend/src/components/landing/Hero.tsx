import { motion } from "framer-motion";
import { useNavigate } from "react-router-dom";
import { EASE, maskUp } from "./motion";
import { useMagnetic } from "./useMagnetic";

export function Hero() {
  const navigate = useNavigate();
  const m = useMagnetic<HTMLButtonElement>(0.45);

  return (
    <section id="top" className="mx-auto max-w-7xl px-6 pb-20 pt-40 md:px-10 md:pb-28 md:pt-52">
      <h1 className="font-hero text-[clamp(3.2rem,9.5vw,8.5rem)] font-bold leading-[0.98] tracking-[-0.04em] text-ink">
        <span className="block overflow-hidden">
          <motion.span className="block" variants={maskUp} initial="hidden" animate="visible" custom={0}>
            Every patient,
          </motion.span>
        </span>
        <span className="block overflow-hidden">
          <motion.span className="block" variants={maskUp} initial="hidden" animate="visible" custom={1}>
            <em className="font-serifit font-normal italic">followed home.</em>
          </motion.span>
        </span>
      </h1>

      <div className="mt-12 flex flex-col items-start justify-between gap-10 md:flex-row md:items-end">
        <motion.p
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.9, ease: EASE, delay: 0.55 }}
          className="max-w-md text-base leading-relaxed text-ink/60 md:text-lg"
        >
          CareInsight runs your hospital's discharge process and follows every
          patient for 30 days — predicting who comes back before they do.
        </motion.p>

        <motion.button
          ref={m.ref}
          style={m.style}
          onMouseMove={m.onMouseMove}
          onMouseLeave={m.onMouseLeave}
          onClick={() => navigate("/login")}
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.9, ease: EASE, delay: 0.7 }}
          className="flex h-32 w-32 shrink-0 items-center justify-center rounded-full bg-ink font-hero text-sm font-semibold text-paper transition-transform hover:scale-105 md:h-40 md:w-40"
        >
          see it live
        </motion.button>
      </div>
    </section>
  );
}
