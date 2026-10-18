import { useRef, useState, type FormEvent } from "react";
import { ArrowLeft, ArrowRight, Eye, EyeOff, GraduationCap, LockKeyhole, Mail, UserRound } from "lucide-react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { ApiError, api } from "../services/api";

type LoginField = "email" | "password";
type LoginErrors = Partial<Record<LoginField, string>>;

export function LoginPage() {
  const formRef = useRef<HTMLFormElement>(null);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [errors, setErrors] = useState<LoginErrors>({});
  const location = useLocation();
  const routeNotice =
    typeof location.state === "object" &&
    location.state !== null &&
    "notice" in location.state &&
    typeof location.state.notice === "string"
      ? location.state.notice
      : "";
  const redirectTo =
    typeof location.state === "object" &&
    location.state !== null &&
    "from" in location.state &&
    typeof location.state.from === "string" &&
    location.state.from.startsWith("/") &&
    !location.state.from.startsWith("//")
      ? location.state.from
      : "/dashboard";
  const [loginNotice, setLoginNotice] = useState(routeNotice);
  const [submitting, setSubmitting] = useState(false);
  const navigate = useNavigate();

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoginNotice("");
    if (submitting) return;

    const nextErrors: LoginErrors = {};
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim())) {
      nextErrors.email = "Enter a valid email address.";
    }
    if (!password) nextErrors.password = "Enter your password.";

    setErrors(nextErrors);
    if (Object.keys(nextErrors).length > 0) {
      window.requestAnimationFrame(() => {
        formRef.current
          ?.querySelector<HTMLElement>('[aria-invalid="true"]')
          ?.focus();
      });
      return;
    }

    setSubmitting(true);
    try {
      await api.login(email.trim(), password);
      setPassword("");
      navigate(redirectTo, { replace: true });
    } catch (cause) {
      setLoginNotice(
        cause instanceof ApiError
          ? cause.status === 401
            ? "That email and password combination wasn’t recognized."
            : cause.message
          : "We couldn’t complete sign-in. Please try again.",
      );
    } finally {
      setSubmitting(false);
    }
  }

  function updateField(field: LoginField, update: () => void) {
    update();
    setErrors((current) => ({ ...current, [field]: undefined }));
    setLoginNotice("");
  }

  return (
    <main className="auth-page">
      <div className="auth-backdrop" aria-hidden="true" />
      <Link className="landing-brand auth-brand" to="/" aria-label="connectED home">
        <span className="landing-brand-mark"><GraduationCap size={20} /></span>
        <span>connect<span>ED</span></span>
      </Link>

      <section className="auth-card login-card" aria-labelledby="login-title">
        <div className="auth-card-heading">
          <span className="auth-icon"><UserRound size={19} /></span>
          <p className="auth-eyebrow">GOOD TO HAVE YOU BACK</p>
          <h1 id="login-title">Welcome back.</h1>
          <p className="auth-intro">
            Reconnect with your network and keep moving forward.
          </p>
        </div>

        <form
          ref={formRef}
          className="auth-form login-form"
          onSubmit={handleSubmit}
          noValidate
        >
          <div className="auth-field">
            <label htmlFor="login-email">Email address</label>
            <span className="auth-input-wrap">
              <Mail size={17} aria-hidden="true" />
              <input
                id="login-email"
                name="email"
                type="email"
                autoComplete="username"
                placeholder="Enter your email address"
                value={email}
                onChange={(event) =>
                  updateField("email", () => setEmail(event.target.value))
                }
                aria-invalid={Boolean(errors.email)}
                aria-describedby={errors.email ? "login-email-error" : undefined}
                required
              />
            </span>
            {errors.email && (
              <span className="auth-field-error" id="login-email-error">
                {errors.email}
              </span>
            )}
          </div>

          <div className="auth-field">
            <label htmlFor="login-password">Password</label>
            <span className="auth-input-wrap">
              <LockKeyhole size={17} aria-hidden="true" />
              <input
                id="login-password"
                name="password"
                type={showPassword ? "text" : "password"}
                autoComplete="current-password"
                placeholder="Enter your password"
                value={password}
                onChange={(event) =>
                  updateField("password", () => setPassword(event.target.value))
                }
                aria-invalid={Boolean(errors.password)}
                aria-describedby={errors.password ? "login-password-error" : undefined}
                required
              />
              <button
                className="auth-password-toggle"
                type="button"
                aria-label={showPassword ? "Hide password" : "Show password"}
                aria-pressed={showPassword}
                onClick={() => setShowPassword((visible) => !visible)}
              >
                {showPassword ? <EyeOff size={17} /> : <Eye size={17} />}
              </button>
            </span>
            {errors.password && (
              <span className="auth-field-error" id="login-password-error">
                {errors.password}
              </span>
            )}
          </div>

          <p className="login-reset-unavailable">
            Forgot password? <strong>Password reset isn’t available yet.</strong>
          </p>

          <button className="button button-primary auth-submit" type="submit" disabled={submitting}>
            {submitting ? "Signing in…" : "Log in"} <ArrowRight size={17} />
          </button>

          {loginNotice && (
            <p className="login-auth-notice" role="status" aria-live="polite">
              {loginNotice}
            </p>
          )}
        </form>

        <p className="auth-mode-link">
          Don&apos;t have an account? <Link to="/signup">Sign up</Link>
        </p>
        <div className="auth-card-footnote">
          <UserRound size={14} aria-hidden="true" />
          Your next meaningful connection is waiting.
        </div>
      </section>

      <Link className="auth-back-home" to="/">
        <ArrowLeft size={15} /> Back to connectED
      </Link>
    </main>
  );
}
