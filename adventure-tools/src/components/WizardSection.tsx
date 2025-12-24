import type { ReactNode } from "react";

export function WizardSection({
  title,
  badge,
  description,
  children
}: {
  title: string;
  badge?: string;
  description?: string;
  children: ReactNode;
}) {
  return (
    <section className="glass-panel rounded-3xl p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-xl font-display">{title}</h3>
          {description ? <p className="mt-2 text-sm text-slate-300">{description}</p> : null}
        </div>
        {badge ? <span className="text-xs text-aurora-lime">{badge}</span> : null}
      </div>
      {children}
    </section>
  );
}
