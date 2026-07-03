/** Shared motion vocabulary for the landing page. */
export const EASE = [0.16, 1, 0.3, 1] as const;

export const VIEWPORT = { once: true, amount: 0.25 } as const;

/** Standard scroll reveal: fade + rise. Pass a custom index for stagger. */
export const fadeUp = {
  hidden: { opacity: 0, y: 48 },
  visible: (i: number = 0) => ({
    opacity: 1,
    y: 0,
    transition: { duration: 0.9, ease: EASE, delay: i * 0.08 },
  }),
};

/** Text mask reveal: parent needs overflow-hidden. */
export const maskUp = {
  hidden: { y: "110%" },
  visible: (i: number = 0) => ({
    y: "0%",
    transition: { duration: 1, ease: EASE, delay: 0.15 + i * 0.09 },
  }),
};
