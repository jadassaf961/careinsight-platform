import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { PillButton } from "./PillButton";

const LINKS = [
  { label: "product", href: "#product" },
  { label: "outcomes", href: "#outcomes" },
  { label: "pricing", href: "#pricing" },
];

export function LandingNav() {
  const [solid, setSolid] = useState(false);

  useEffect(() => {
    const onScroll = () => setSolid(window.scrollY > 80);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  function jump(e: React.MouseEvent<HTMLAnchorElement>, href: string) {
    e.preventDefault();
    document.querySelector(href)?.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  return (
    <header
      className={`fixed inset-x-0 top-0 z-50 transition-all duration-300 ${
        solid ? "bg-paper/95 shadow-[0_1px_0_0_#e5e5e5] backdrop-blur" : "bg-transparent"
      }`}
    >
      <nav className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4 md:px-10">
        <a
          href="#top"
          onClick={(e) => jump(e, "#top")}
          className="font-hero text-lg font-bold tracking-tight text-ink"
        >
          careinsight
        </a>
        <div className="flex items-center gap-8">
          <div className="hidden items-center gap-8 md:flex">
            {LINKS.map((l) => (
              <a
                key={l.href}
                href={l.href}
                onClick={(e) => jump(e, l.href)}
                className="font-hero text-sm font-medium text-ink/70 transition-colors hover:text-ink"
              >
                {l.label}
              </a>
            ))}
            <Link
              to="/login"
              className="font-hero text-sm font-medium text-ink/70 transition-colors hover:text-ink"
            >
              sign in
            </Link>
          </div>
          <PillButton href="mailto:jadassaf6000@gmail.com?subject=CareInsight%20demo%20request">
            book a demo
          </PillButton>
        </div>
      </nav>
    </header>
  );
}
