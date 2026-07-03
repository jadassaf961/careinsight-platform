import { motion } from "framer-motion";
import { EASE } from "./motion";

const item = {
  hidden: { opacity: 0, y: 14 },
  visible: (i: number = 0) => ({
    opacity: 1,
    y: 0,
    transition: { duration: 0.6, ease: EASE, delay: 0.2 + i * 0.12 },
  }),
};

const stagger = {
  hidden: {},
  visible: { transition: { staggerChildren: 0 } },
};

function Frame({ children, label }: { children: React.ReactNode; label: string }) {
  return (
    <motion.div
      variants={stagger}
      initial="hidden"
      whileInView="visible"
      viewport={{ once: true, amount: 0.4 }}
      className="rounded-2xl border border-white/10 bg-[#181818] p-4"
    >
      <div className="mb-3 font-hero text-[0.6rem] font-semibold uppercase tracking-[0.2em] text-white/40">
        {label}
      </div>
      {children}
    </motion.div>
  );
}

export function BoardVignette() {
  const rows = [
    { name: "Hassan, Layla", pct: "78%", dot: "#f87171", tasks: "3 open · pharmacist" },
    { name: "Patel, Marcus", pct: "72%", dot: "#f87171", tasks: "2 open · case manager" },
    { name: "Farhat, May", pct: "59%", dot: "#fbbf24", tasks: "all tasks done" },
  ];
  return (
    <Frame label="Discharge readiness board">
      <div className="mb-3 flex gap-2">
        {[["Blocked", "3"], ["On track", "14"], ["Response", "94%"]].map(([k, v], i) => (
          <motion.div key={k} custom={i} variants={item} className="flex-1 rounded-lg bg-white/5 p-2.5">
            <div className="text-[0.55rem] uppercase tracking-wider text-white/40">{k}</div>
            <div className="font-hero text-lg font-bold text-white">{v}</div>
          </motion.div>
        ))}
      </div>
      <div className="space-y-1.5">
        {rows.map((r, i) => (
          <motion.div
            key={r.name}
            custom={i + 3}
            variants={item}
            className="flex items-center justify-between rounded-lg bg-white/[0.03] px-3 py-2"
          >
            <span className="flex items-center gap-2 text-xs text-white/80">
              <span className="h-1.5 w-1.5 rounded-full" style={{ background: r.dot }} />
              {r.name}
            </span>
            <span className="font-mono text-[0.65rem] text-white/50">
              {r.pct} · {r.tasks}
            </span>
          </motion.div>
        ))}
      </div>
    </Frame>
  );
}

export function PhoneVignette() {
  return (
    <Frame label="Day-7 WhatsApp check-in">
      <div className="space-y-2">
        <motion.div
          custom={0}
          variants={item}
          className="max-w-[85%] rounded-xl rounded-tl-sm bg-white/10 p-2.5 text-[0.65rem] leading-relaxed text-white/75"
        >
          مرحباً ليلى، معك مستشفى رزق للاطمئنان عليك — اليوم ٧ بعد الخروج. هل تناولت جميع أدويتك؟
        </motion.div>
        <motion.div
          custom={1}
          variants={item}
          className="ml-auto max-w-[85%] rounded-xl rounded-tr-sm bg-emerald-400/15 p-2.5 text-[0.65rem] text-emerald-100"
        >
          نعم الحمدلله، كل شيء تمام
        </motion.div>
        <motion.div
          custom={2}
          variants={item}
          className="flex items-center gap-1.5 pt-1 text-[0.6rem] font-medium text-emerald-300"
        >
          <span className="h-1 w-1 rounded-full bg-emerald-300" /> Responded — no concerns
        </motion.div>
      </div>
    </Frame>
  );
}

export function QueueVignette() {
  return (
    <Frame label="Escalation queue">
      <div className="space-y-1.5">
        <motion.div custom={0} variants={item} className="rounded-lg bg-red-500/10 px-3 py-2">
          <div className="flex items-center justify-between">
            <span className="text-[0.6rem] font-bold uppercase tracking-wider text-red-300">high</span>
            <span className="text-[0.6rem] text-white/40">today</span>
          </div>
          <div className="mt-0.5 text-xs text-white/80">Chest pain reported on day-2 check-in</div>
        </motion.div>
        <motion.div custom={1} variants={item} className="rounded-lg bg-white/[0.04] px-3 py-2">
          <div className="flex items-center justify-between">
            <span className="text-[0.6rem] font-bold uppercase tracking-wider text-amber-300">medium</span>
            <span className="text-[0.6rem] text-white/40">1d</span>
          </div>
          <div className="mt-0.5 text-xs text-white/80">No reply to two consecutive check-ins</div>
        </motion.div>
        <motion.div custom={2} variants={item} className="pt-1 text-[0.6rem] font-medium text-white/40">
          Resolved this week: 12 — every one a call that happened in time
        </motion.div>
      </div>
    </Frame>
  );
}
