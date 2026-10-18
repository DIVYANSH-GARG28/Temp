import { useRef, useState, type FormEvent } from "react";
import {
  ArrowLeft,
  ArrowRight,
  Eye,
  EyeOff,
  GraduationCap,
  Leaf,
  LockKeyhole,
  Mail,
  UserRound,
  UsersRound,
} from "lucide-react";
import { Link, useNavigate } from "react-router-dom";
import { ApiError, api } from "../services/api";

type SignupRole = "" | "student" | "alumni";
type SignupField = "role" | "email" | "name" | "password" | "confirmPassword";
type SignupErrors = Partial<Record<SignupField, string>>;

export function SignupPage() {
  const formRef = useRef<HTMLFormElement>(null);
  const [role, setRole] = useState<SignupRole>("");
  const [email, setEmail] = useState("");
  const [name, setName] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [errors, setErrors] = useState<SignupErrors>({});
  const [registrationNotice, setRegistrationNotice] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const navigate = useNavigate();

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setRegistrationNotice("");
    if (submitting) return;

    const nextErrors: SignupErrors = {};
    if (!role) nextErrors.role = "Choose whether you’re joining as a student or alum.";
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim())) {
      nextErrors.email = "Enter a valid email address.";
    }
    if (!name.trim()) nextErrors.name = "Enter your full name.";
    if (!password) nextErrors.password = "Enter a password.";
    if (!confirmPassword) {
      nextErrors.confirmPassword = "Confirm your password.";
    } else if (password !== confirmPassword) {
      nextErrors.confirmPassword = "Those passwords don’t match.";
    }

    setErrors(nextErrors);
    if (Object.keys(nextErrors).length > 0 || !role) {
      window.requestAnimationFrame(() => {
        formRef.current
          ?.querySelector<HTMLElement>('[aria-invalid="true"]')
          ?.focus();
      });
      return;
    }

    setSubmitting(true);
    try {
      await api.register({
        email: email.trim(),
        password,
        role,
        name: name.trim(),
      });
      setPassword("");
      setConfirmPassword("");
      navigate("/dashboard", { replace: true });
    } catch (cause) {
      setRegistrationNotice(
        cause instanceof ApiError
          ? cause.status === 409
            ? "An account with this email already exists. Try logging in instead."
            : cause.message
          : "We couldn’t create your account. Please try again.",
      );
    } finally {
      setSubmitting(false);
    }
  }

  function updateField(
    field: SignupField,
    update: () => void,
  ) {
    update();
    setErrors((current) => ({ ...current, [field]: undefined }));
    setRegistrationNotice("");
  }

  return (
    <main className="auth-page">
      <div className="auth-backdrop" aria-hidden="true" />
      <Link className="landing-brand auth-brand" to="/" aria-label="connectED home">
        <span className="landing-brand-mark"><GraduationCap size={20} /></span>
        <span>connect<span>ED</span></span>
      </Link>

      <section className="auth-card" aria-labelledby="signup-title">
        <div className="auth-card-heading">
          <span className="auth-icon"><UsersRound size={19} /></span>
          <p className="auth-eyebrow">A COMMUNITY FOR WHAT COMES NEXT</p>
          <h1 id="signup-title">Find your people.</h1>
          <p className="auth-intro">
            Make room for the connections that move you forward.
          </p>
        </div>

        <form ref={formRef} className="auth-form" onSubmit={handleSubmit} noValidate>
          <div className="auth-field">
            <label htmlFor="signup-role">I am joining as</label>
            <select
              id="signup-role"
              name="role"
              autoComplete="off"
              value={role}
              onChange={(event) =>
                updateField("role", () => setRole(event.target.value as SignupRole))
              }
              aria-invalid={Boolean(errors.role)}
              aria-describedby={errors.role ? "signup-role-error" : undefined}
              required
            >
              <option value="">Select your role</option>
              <option value="student">Student</option>
              <option value="alumni">Alumni</option>
            </select>
            {errors.role && (
              <span className="auth-field-error" id="signup-role-error">
                {errors.role}
              </span>
            )}
          </div>

          <div className="auth-field">
            <label htmlFor="signup-email">Email address</label>
            <span className="auth-input-wrap">
              <Mail size={17} aria-hidden="true" />
              <input
                id="signup-email"
                name="email"
                type="email"
                autoComplete="email"
                placeholder="you@example.com"
                value={email}
                onChange={(event) =>
                  updateField("email", () => setEmail(event.target.value))
                }
                aria-invalid={Boolean(errors.email)}
                aria-describedby={errors.email ? "signup-email-error" : undefined}
                required
              />
            </span>
            {errors.email && (
              <span className="auth-field-error" id="signup-email-error">
                {errors.email}
              </span>
            )}
          </div>

          <div className="auth-field">
            <label htmlFor="signup-name">Full name</label>
            <span className="auth-input-wrap">
              <UserRound size={17} aria-hidden="true" />
              <input
                id="signup-name"
                name="name"
                type="text"
                autoComplete="name"
                placeholder="Enter your full name"
                value={name}
                onChange={(event) =>
                  updateField("name", () => setName(event.target.value))
                }
                aria-invalid={Boolean(errors.name)}
                aria-describedby={errors.name ? "signup-name-error" : undefined}
                required
              />
            </span>
            {errors.name && (
              <span className="auth-field-error" id="signup-name-error">
                {errors.name}
              </span>
            )}
          </div>

          <div className="auth-field">
            <label htmlFor="signup-password">Password</label>
            <span className="auth-input-wrap">
              <LockKeyhole size={17} aria-hidden="true" />
              <input
                id="signup-password"
                name="password"
                type={showPassword ? "text" : "password"}
                autoComplete="new-password"
                placeholder="Create a password"
                value={password}
                onChange={(event) =>
                  updateField("password", () => setPassword(event.target.value))
                }
                aria-invalid={Boolean(errors.password)}
                aria-describedby={errors.password ? "signup-password-error" : undefined}
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
              <span className="auth-field-error" id="signup-password-error">
                {errors.password}
              </span>
            )}
          </div>

          <div className="auth-field">
            <label htmlFor="signup-confirm-password">Confirm password</label>
            <span className="auth-input-wrap">
              <LockKeyhole size={17} aria-hidden="true" />
              <input
                id="signup-confirm-password"
                name="confirmPassword"
                type={showConfirmPassword ? "text" : "password"}
                autoComplete="new-password"
                placeholder="Enter your password again"
                value={confirmPassword}
                onChange={(event) =>
                  updateField("confirmPassword", () =>
                    setConfirmPassword(event.target.value),
                  )
                }
                aria-invalid={Boolean(errors.confirmPassword)}
                aria-describedby={
                  errors.confirmPassword ? "signup-confirm-password-error" : undefined
                }
                required
              />
              <button
                className="auth-password-toggle"
                type="button"
                aria-label={
                  showConfirmPassword ? "Hide confirmation" : "Show confirmation"
                }
                aria-pressed={showConfirmPassword}
                onClick={() => setShowConfirmPassword((visible) => !visible)}
              >
                {showConfirmPassword ? <EyeOff size={17} /> : <Eye size={17} />}
              </button>
            </span>
            {errors.confirmPassword && (
              <span className="auth-field-error" id="signup-confirm-password-error">
                {errors.confirmPassword}
              </span>
            )}
          </div>

          <button className="button button-primary auth-submit" type="submit" disabled={submitting}>
            {submitting ? "Creating your account…" : "Create your account"} <ArrowRight size={17} />
          </button>

          {registrationNotice && (
            <p className="signup-registration-notice" role="status" aria-live="polite">
              {registrationNotice}
            </p>
          )}
        </form>

        <p className="auth-mode-link">
          Already have an account? <Link to="/login">Log in</Link>
        </p>
        <div className="auth-card-footnote">
          <Leaf size={14} aria-hidden="true" />
          Thoughtful connections, built around you.
        </div>
      </section>

      <Link className="auth-back-home" to="/">
        <ArrowLeft size={15} /> Back to connectED
      </Link>
    </main>
  );
}
