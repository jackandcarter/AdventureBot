import { clsx } from "clsx";

export function JsonEditor({
  id,
  value,
  onChange,
  placeholder,
  invalid
}: {
  id?: string;
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  invalid?: boolean;
}) {
  return (
    <textarea
      id={id}
      className={clsx(
        "min-h-[140px] w-full rounded-2xl border px-4 py-3 text-sm font-mono bg-night-900/60",
        "focus:outline-none focus:ring-2 focus:ring-aurora-violet/70",
        invalid ? "border-aurora-amber/60" : "border-white/10"
      )}
      placeholder={placeholder}
      value={value}
      onChange={(event) => onChange(event.target.value)}
    />
  );
}
