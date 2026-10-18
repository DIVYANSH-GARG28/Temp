import { AlertCircle, LoaderCircle, RefreshCw, UsersRound } from "lucide-react";
import type { ReactNode } from "react";

interface StatusViewProps {
  kind: "loading" | "error" | "empty";
  title: string;
  description: string;
  action?: ReactNode;
}

export function StatusView({
  kind,
  title,
  description,
  action,
}: StatusViewProps) {
  const Icon =
    kind === "loading"
      ? LoaderCircle
      : kind === "error"
        ? AlertCircle
        : UsersRound;

  return (
    <section className={`status-panel status-${kind}`} aria-live="polite">
      <div className="status-icon"><Icon size={22} /></div>
      <h2>{title}</h2>
      <p>{description}</p>
      {action}
    </section>
  );
}

export function RetryButton({ onClick }: { onClick: () => void }) {
  return (
    <button className="button button-secondary" type="button" onClick={onClick}>
      <RefreshCw size={15} />
      Try again
    </button>
  );
}
