import type { InputHTMLAttributes } from "react";

type Props = InputHTMLAttributes<HTMLInputElement> & {
  id: string;
  label: string;
  helper?: string;
  error?: string;
};

/** Label above, helper below, error replaces helper. */
export function Field({ id, label, helper, error, className = "", ...props }: Props) {
  const describedBy =
    [helper && !error && `${id}-helper`, error && `${id}-error`].filter(Boolean).join(" ") || undefined;
  return (
    <div className="flex flex-col gap-1.5">
      <label htmlFor={id} className="text-sm font-medium text-ink">
        {label}
      </label>
      <input
        id={id}
        aria-describedby={describedBy}
        aria-invalid={error ? true : undefined}
        {...props}
        className={`min-h-11 rounded-md border bg-panel px-3 text-base text-ink placeholder:text-muted/70 ${
          error ? "border-danger" : "border-line"
        } ${className}`}
      />
      {helper && !error && (
        <p id={`${id}-helper`} className="text-sm text-muted">
          {helper}
        </p>
      )}
      {error && (
        <p id={`${id}-error`} className="text-sm text-danger">
          {error}
        </p>
      )}
    </div>
  );
}
