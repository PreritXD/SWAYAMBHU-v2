import { useEffect, useRef } from "react";
import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";

gsap.registerPlugin(ScrollTrigger);

export default function ScrollProgressBar() {
  const barRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = barRef.current;
    if (!el) return;

    const anim = gsap.to(el, {
      scaleX: 1,
      ease: "none",
      scrollTrigger: {
        trigger: document.documentElement,
        start: "top top",
        end: "bottom bottom",
        scrub: 0.15,
      },
    });

    return () => {
      anim.kill();
    };
  }, []);

  return (
    <div
      className="fixed top-0 left-0 right-0 h-[3px] z-50 pointer-events-none origin-left"
      style={{
        background: "linear-gradient(90deg, rgba(229,154,61,0.2) 0%, rgba(245,188,115,0.9) 50%, rgba(229,154,61,1) 100%)",
        boxShadow: "0 0 10px rgba(229, 154, 61, 0.6), 0 0 20px rgba(245, 188, 115, 0.3)",
        transform: "scaleX(0)",
      }}
      ref={barRef}
      aria-hidden="true"
    />
  );
}
