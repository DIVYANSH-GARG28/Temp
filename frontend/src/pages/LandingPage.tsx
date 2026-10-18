import {
  ArrowDown,
  ArrowRight,
  ArrowUpRight,
  BriefcaseBusiness,
  GraduationCap,
  Lightbulb,
  MoveUpRight,
  Sparkles,
  UsersRound,
} from "lucide-react";
import { useRef } from "react";
import { Link } from "react-router-dom";
import Crosshair from "../components/Crosshair";

const networkNodes = [
  { className: "landing-node-student", icon: GraduationCap, label: "Students" },
  { className: "landing-node-alumni", icon: BriefcaseBusiness, label: "Alumni" },
  { className: "landing-node-ideas", icon: Lightbulb, label: "Ideas" },
  { className: "landing-node-community", icon: UsersRound, label: "Community" },
];

export function LandingPage() {
  const heroRef = useRef<HTMLElement>(null);

  return (
    <main className="landing-page">
      <header className="landing-nav">
        <Link className="landing-brand" to="/" aria-label="connectED home">
          <span className="landing-brand-mark"><GraduationCap size={20} /></span>
          <span>connect<span>ED</span></span>
        </Link>
        <div className="landing-nav-right">
          <span className="landing-nav-caption">A community for what comes next</span>
          <Link className="landing-login" to="/login">Login</Link>
          <Link className="button button-primary landing-signup" to="/signup">
            Sign up <ArrowUpRight size={15} />
          </Link>
        </div>
      </header>

      <section className="landing-hero" ref={heroRef}>
        <Crosshair
          containerRef={heroRef}
          color="#000000"
          opacity={0.5}
          thickness={1}
          lineStyle="dotted"
          gap={9}
          fade={0.58}
          smoothing={0.34}
          showCoordinates={false}
          targetEffect="lock"
          clickPulse
        />
        <div className="landing-copy">
          <div className="landing-kicker"><span /> MEET YOUR PEOPLE. FIND YOUR WAY.</div>
          <h1 className="landing-title">
            connect<span>ED</span>
          </h1>
          <p className="landing-subtitle">
            The right conversation can change your direction.
          </p>
          <p className="landing-description">
            Find alumni mentors who understand where you want to go, and build
            the kind of connections that take you there.
          </p>
          <div className="landing-actions">
            <Link className="button button-primary landing-cta" to="/login">
              Login <ArrowRight size={16} />
            </Link>
            <Link className="button button-outline landing-cta" to="/signup">
              Sign up <MoveUpRight size={15} />
            </Link>
          </div>
          <div className="landing-trust-note">
            <Sparkles size={14} />
            Meaningful introductions, shaped around your ambitions.
          </div>
        </div>

        <div className="landing-visual" aria-label="Illustration of a connected community">
          <div className="landing-visual-wash" />
          <svg className="landing-connections" viewBox="0 0 540 490" fill="none" aria-hidden="true">
            <path className="connection-path connection-path-one" d="M103 115C182 126 176 221 270 245" />
            <path className="connection-path connection-path-two" d="M440 99C355 126 356 209 270 245" />
            <path className="connection-path connection-path-three" d="M121 377C184 335 198 286 270 245" />
            <path className="connection-path connection-path-four" d="M426 382C360 335 344 279 270 245" />
            <circle className="connection-dot connection-dot-one" cx="183" cy="151" r="4" />
            <circle className="connection-dot connection-dot-two" cx="373" cy="137" r="4" />
            <circle className="connection-dot connection-dot-three" cx="178" cy="335" r="4" />
            <circle className="connection-dot connection-dot-four" cx="370" cy="337" r="4" />
          </svg>
          <div className="landing-center">
            <div className="landing-center-ring landing-center-ring-one" />
            <div className="landing-center-ring landing-center-ring-two" />
            <div className="landing-center-icon"><Sparkles size={28} /></div>
            <span className="landing-center-label">YOUR NEXT CONNECTION</span>
          </div>
          {networkNodes.map(({ className, icon: Icon, label }) => (
            <div className={`landing-node ${className}`} key={label}>
              <span className="landing-node-icon"><Icon size={19} /></span>
              <span className="landing-node-label">{label}</span>
            </div>
          ))}
          <span className="landing-visual-caption">A little closer to what’s next.</span>
        </div>

        <a className="landing-scroll" href="#how-it-works" aria-label="Scroll to learn how connectED works">
          <span>SCROLL TO EXPLORE</span>
          <ArrowDown size={14} />
        </a>
      </section>

      <section className="landing-intro" id="how-it-works">
        <div>
          <div className="eyebrow">YOUR NEXT CHAPTER, TOGETHER</div>
          <h2>Good things happen<br />when paths cross.</h2>
        </div>
        <div className="landing-intro-copy">
          <p>
            connectED brings students and alumni closer through thoughtful
            mentorship recommendations—so finding a guide feels less like
            searching a crowd and more like starting a conversation.
          </p>
          <Link className="text-link" to="/mentors">
            Explore mentor discovery <ArrowRight size={15} />
          </Link>
        </div>
      </section>

      <footer className="landing-footer">
        <Link className="landing-brand landing-footer-brand" to="/">
          <span className="landing-brand-mark"><GraduationCap size={18} /></span>
          <span>connect<span>ED</span></span>
        </Link>
        <span>Making room for meaningful connections.</span>
        <Link to="/dashboard">Open dashboard <ArrowUpRight size={14} /></Link>
      </footer>
    </main>
  );
}
