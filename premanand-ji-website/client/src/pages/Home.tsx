import { useLayoutEffect, useRef, useState } from "react";
import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import {
  ArrowDown,
  ArrowUpRight,
  ChevronRight,
  CirclePlay,
  MessageCircle,
  Menu,
  Pause,
  Send,
  Sparkles,
  X,
} from "lucide-react";
import SatsangChat from "@/components/SatsangChat";
import { LoopingWords } from "@/components/ui/looping-words-with-gsap";

gsap.registerPlugin(ScrollTrigger);

const navItems = [
  { label: "Darshan", target: "darshan" },
  { label: "Naam Japa", target: "japa" },
  { label: "Teachings", target: "teachings" },
  { label: "Ashram", target: "ashram" },
  { label: "Chat", target: "chat" },
];

const teachings = [
  {
    number: "01",
    title: "Return to the name",
    copy: "When the mind scatters, let the name bring it gently home.",
    tag: "Japa",
  },
  {
    number: "02",
    title: "Let seva be simple",
    copy: "The smallest act, offered without noise, can become a prayer.",
    tag: "Seva",
  },
  {
    number: "03",
    title: "Keep the heart soft",
    copy: "Grace is not distant. It is felt in the way we meet each moment.",
    tag: "Bhakti",
  },
];

export default function Home() {
  const root = useRef<HTMLDivElement>(null);
  const [menuOpen, setMenuOpen] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);

  const scrollTo = (target: string) => {
    document.getElementById(target)?.scrollIntoView({ behavior: "smooth" });
    setMenuOpen(false);
  };

  useLayoutEffect(() => {
    const ctx = gsap.context(() => {
      const intro = gsap.timeline({ defaults: { ease: "power3.out" } });
      intro
        .from(".site-header", { y: -18, opacity: 0, duration: 0.75 })
        .from(".hero-kicker", { y: 18, opacity: 0, duration: 0.55 }, "-=0.35")
        .from(".hero-title-line", { y: 36, opacity: 0, duration: 0.7, stagger: 0.08 }, "-=0.25")
        .from(".hero-copy", { y: 20, opacity: 0, duration: 0.55 }, "-=0.32")
        .from(".hero-actions", { y: 18, opacity: 0, duration: 0.5 }, "-=0.28")
        .from(".hero-art", { scale: 0.86, opacity: 0, rotate: -4, duration: 1.25, ease: "back.out(1.4)" }, "-=0.8")
        .from(".hero-side-note", { x: 20, opacity: 0, duration: 0.55 }, "-=0.65");

      gsap.to(".hero-art", {
        y: -14,
        rotate: 2,
        duration: 4.2,
        repeat: -1,
        yoyo: true,
        ease: "sine.inOut",
      });
      gsap.to(".halo-ring", {
        rotate: 360,
        duration: 36,
        repeat: -1,
        ease: "none",
      });
      gsap.to(".orb-a", {
        x: 18,
        y: -18,
        duration: 4.8,
        repeat: -1,
        yoyo: true,
        ease: "sine.inOut",
      });
      gsap.to(".orb-b", {
        x: -14,
        y: 14,
        duration: 5.5,
        repeat: -1,
        yoyo: true,
        ease: "sine.inOut",
      });

      gsap.utils.toArray<HTMLElement>(".reveal").forEach((element) => {
        gsap.fromTo(
          element,
          { y: 32, opacity: 0 },
          {
            y: 0,
            opacity: 1,
            duration: 0.8,
            ease: "power3.out",
            scrollTrigger: {
              trigger: element,
              start: "top 84%",
              once: true,
            },
          },
        );
      });

      const onMove = (event: MouseEvent) => {
        const x = (event.clientX / window.innerWidth - 0.5) * 2;
        const y = (event.clientY / window.innerHeight - 0.5) * 2;
        gsap.to(".hero-art", {
          rotationY: x * 4,
          rotationX: y * -3,
          duration: 1.2,
          ease: "power3.out",
          overwrite: "auto",
        });
        gsap.to(".hero-glow", {
          x: x * 10,
          y: y * 8,
          duration: 1.4,
          ease: "power3.out",
          overwrite: "auto",
        });
      };

      window.addEventListener("mousemove", onMove);
      return () => window.removeEventListener("mousemove", onMove);
    }, root);

    return () => ctx.revert();
  }, []);

  return (
    <div ref={root} className="site-shell">
      <header className="site-header">
        <a className="brand-mark" href="#top" aria-label="Premanand Ji Maharaj home">
          <span className="brand-dot" />
          <span>
            <strong>प्रेमानंद</strong>
            <small>JI MAHARAJ</small>
          </span>
        </a>

        <nav className="desktop-nav" aria-label="Primary navigation">
          {navItems.map((item) => (
            <button key={item.target} onClick={() => scrollTo(item.target)}>
              {item.label}
            </button>
          ))}
        </nav>

        <button
          className="nav-cta"
          onClick={() => scrollTo("read")}
          aria-label="Open the reading nook"
        >
          <span>Read a verse</span>
          <ArrowUpRight size={16} strokeWidth={1.8} />
        </button>
        <button
          className="menu-toggle"
          onClick={() => setMenuOpen((open) => !open)}
          aria-label={menuOpen ? "Close menu" : "Open menu"}
          aria-expanded={menuOpen}
        >
          {menuOpen ? <X size={21} /> : <Menu size={21} />}
        </button>
      </header>

      {menuOpen && (
        <div className="mobile-nav">
          {navItems.map((item) => (
            <button key={item.target} onClick={() => scrollTo(item.target)}>
              {item.label}
              <ChevronRight size={16} />
            </button>
          ))}
          <button onClick={() => scrollTo("read")}>
            Read a verse
            <ChevronRight size={16} />
          </button>
        </div>
      )}

      <main id="top">
        <section className="hero-section">
          <div className="hero-grid" />
          <div className="hero-orbit halo-ring" />
          <div className="hero-glow" />
          <div className="orb orb-a" />
          <div className="orb orb-b" />

          <div className="hero-content">
            <div className="hero-kicker eyebrow">
              <Sparkles size={13} fill="currentColor" />
              <span>Vrindavan · A quiet place to return</span>
            </div>
            <h1>
              <span className="hero-title-line">Begin where</span>
              <span className="hero-title-line title-italic">the heart is still.</span>
            </h1>
            <p className="hero-copy">
              A gentle digital darshan of <em>Premanand Ji Maharaj</em> — a space for
              remembrance, reflection, and the simple work of coming home to the self.
            </p>
            <div className="hero-actions">
              <button className="button button-dark" onClick={() => scrollTo("darshan")}>
                Enter the darshan
                <ArrowDown size={17} />
              </button>
              <button
                className={`button button-quiet ${isPlaying ? "is-playing" : ""}`}
                onClick={() => setIsPlaying((playing) => !playing)}
                aria-pressed={isPlaying}
              >
                {isPlaying ? <Pause size={16} /> : <CirclePlay size={16} />}
                {isPlaying ? "Aarti pause" : "Listen softly"}
              </button>
            </div>
          </div>

          <div className="hero-visual" aria-label="A luminous saffron lotus illustration">
            <div className="hero-side-note note-top">
              <span className="note-index">01</span>
              <span>naam · seva · prem</span>
            </div>
            <div className="hero-art-wrap">
              <div className="hero-art-shadow" />
              <img
                className="hero-art"
                src="/hero-lotus.png"
                alt="A luminous saffron lotus"
              />
              <div className="hero-art-caption">मन को घर लौटने दो</div>
            </div>
            <div className="hero-side-note note-bottom">
              <span>Scroll to soften</span>
              <ArrowDown size={15} />
            </div>
          </div>

          <div className="hero-footer-line">
            <span>01 / 04</span>
            <span>श्री राधे</span>
            <span className="footer-rule" />
            <span>Scroll with presence</span>
          </div>
        </section>

        <section id="darshan" className="darshan-section section-light">
          <div className="section-intro reveal">
            <p className="eyebrow dark-eyebrow">The invitation</p>
            <h2>Not a destination.<br /><span>A direction inward.</span></h2>
          </div>
          <div className="darshan-content reveal">
            <div className="vertical-label">दर्शन · ०१</div>
            <div className="darshan-quote">
              <span className="quote-mark">“</span>
              <p>भगवान का नाम ही<br /><em>सबसे बड़ा सहारा है।</em></p>
              <span className="quote-translation">The name of the divine is the greatest support.</span>
            </div>
            <div className="darshan-note">
              <p>In the middle of a hurried world, this is a small clearing. Move slowly. Read a line. Let it meet you where you are.</p>
              <button className="text-link" onClick={() => scrollTo("japa")}>
                Experience Naam Japa <ArrowUpRight size={15} />
              </button>
            </div>
          </div>
        </section>

        <section id="japa" className="japa-section section-dark reveal">
          <div className="japa-ambient-glow" />
          <div className="japa-container">
            <div className="japa-eyebrow eyebrow">
              <Sparkles size={13} fill="currentColor" />
              <span>अखंड नाम जप · Akhand Naam Japa</span>
            </div>
            <h2>
              श्वास-श्वास में<br />
              <span>श्री राधा।</span>
            </h2>
            <p className="japa-subtext">
              “जब मन विचलित हो, तो सब छोड़कर केवल एक नाम का आश्रय ले लो। राधा नाम ही हर श्वास का विश्राम है।”
            </p>

            <div className="japa-interactive-stage">
              <LoopingWords words={["राधा"]} className="japa-cloneable" hideCredits={false} />
            </div>

            <div className="japa-footer">
              <div className="japa-mantra-badge">
                <span className="japa-dot" />
                <span className="japa-mantra-text">निरंतर नाम संकीर्तन</span>
              </div>
              <p className="japa-guidance">
                Close your eyes for three breaths. Let the rhythm of the sacred name settle the restless mind.
              </p>
            </div>
          </div>
        </section>

        <section id="teachings" className="teachings-section">
          <div className="section-heading reveal">
            <div>
              <p className="eyebrow">A few places to begin</p>
              <h2>Three ways to<br /><span>make space.</span></h2>
            </div>
            <p className="heading-aside">Small practices for an unhurried life — kept close, not kept perfect.</p>
          </div>
          <div className="teaching-list">
            {teachings.map((teaching) => (
              <article className="teaching-card reveal" key={teaching.number}>
                <div className="card-topline">
                  <span>{teaching.number}</span>
                  <span className="card-tag">{teaching.tag}</span>
                </div>
                <h3>{teaching.title}</h3>
                <p>{teaching.copy}</p>
                <span className="card-arrow"><ArrowUpRight size={17} /></span>
              </article>
            ))}
          </div>
        </section>

        <section id="chat" className="chat-section section-light">
          <div className="chat-section-intro reveal">
            <p className="eyebrow dark-eyebrow">A quiet place to ask</p>
            <h2>Bring a thought.<br /><span>Leave with space.</span></h2>
            <p className="chat-section-copy">Sit with a simple question, a restless moment, or a line you would like to remember.</p>
          </div>
          <div className="chat-window-inline reveal" aria-label="सत्संग जिज्ञासा संकुल">
            <SatsangChat />
          </div>
        </section>

        <section id="ashram" className="ashram-section section-dark">
          <div className="ashram-mark reveal">
            <span>श्री</span>
            <div className="mark-line" />
            <span>राधे</span>
          </div>
          <div className="ashram-copy reveal">
            <p className="eyebrow">The feeling of Vrindavan</p>
            <h2>Leave with a little<br /><span>more quiet.</span></h2>
            <p>May this page be a pause between two thoughts. May the next breath be a little more aware.</p>
          </div>
          <div className="ashram-stamp reveal">A place<br />to return to</div>
        </section>

        <section id="read" className="read-section section-light">
          <div className="read-card reveal">
            <div className="read-card-ornament">✳</div>
            <p className="eyebrow dark-eyebrow">A verse for today</p>
            <h2>“Keep the name<br /><em>close to your breath.”</em></h2>
            <div className="read-meta">
              <span>Premanand Ji Maharaj</span>
              <span>श्री राधे</span>
            </div>
          </div>
        </section>
      </main>

      <footer className="site-footer">
        <div className="footer-brand">प्रेमानंद <span>जी महाराज</span></div>
        <p>Made for moments of remembrance.</p>
        <div className="footer-meta"><span>© 2025</span><span>Vrindavan, India</span></div>
      </footer>

      {/* Floating Darshan / Chat Quick-Access Trigger */}
      <button
        className="satsang-floating-trigger"
        onClick={() => scrollTo("chat")}
        aria-label="सत्संग जिज्ञासा चैट खोलें"
      >
        <span className="satsang-floating-trigger-dot" />
        <MessageCircle size={15} />
        <span>सत्संग जिज्ञासा</span>
      </button>
    </div>
  );
}
