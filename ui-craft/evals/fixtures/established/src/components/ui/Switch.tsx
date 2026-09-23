type Props = {
  id: string;
  label: string;
  description?: string;
  checked: boolean;
  onChange: (value: boolean) => void;
};

/** Labelled toggle. The button is a 44px hit area; the visible track is 44×24 and darkens on hover. */
export function Switch({ id, label, description, checked, onChange }: Props) {
  return (
    <div className="flex items-start justify-between gap-6 border-b border-line py-4 last:border-b-0">
      <div>
        <label htmlFor={id} className="block text-sm font-medium text-ink">
          {label}
        </label>
        {description && (
          <p id={`${id}-desc`} className="mt-1 text-sm text-muted">
            {description}
          </p>
        )}
      </div>
      <button
        id={id}
        type="button"
        role="switch"
        aria-checked={checked}
        aria-describedby={description ? `${id}-desc` : undefined}
        onClick={() => onChange(!checked)}
        className="group -mr-2 flex h-11 w-14 shrink-0 cursor-pointer items-center justify-center rounded-md"
      >
        <span
          aria-hidden="true"
          className={`relative h-6 w-11 rounded-full transition-colors duration-200 ${
            checked ? "bg-brand group-hover:bg-brand-strong" : "bg-line group-hover:bg-muted/50"
          }`}
        >
          <span
            className={`absolute top-0.5 left-0.5 h-5 w-5 rounded-full bg-white transition-transform duration-200 ${
              checked ? "translate-x-5" : ""
            }`}
          />
        </span>
      </button>
    </div>
  );
}
