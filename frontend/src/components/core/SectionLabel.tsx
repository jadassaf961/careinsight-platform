export function SectionLabel({
  children,
  className = "",
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div
      className={`font-display text-[0.65rem] font-semibold tracking-[0.2em] uppercase text-ink/40 mb-3 ${className}`}
    >
      {children}
    </div>
  );
}
