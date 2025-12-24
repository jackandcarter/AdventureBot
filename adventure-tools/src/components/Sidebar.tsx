import clsx from "clsx";

export function Sidebar({
  items,
  active,
  onSelect
}: {
  items: string[];
  active: string;
  onSelect: (item: string) => void;
}) {
  return (
    <aside className="w-72 border-r border-white/10 bg-night-850/80 backdrop-blur-xl px-6 py-8 flex flex-col">
      <div className="glass-panel rounded-2xl p-4">
        <p className="text-xs text-slate-400 uppercase tracking-[0.2em]">Project</p>
        <h2 className="text-xl font-display text-white">AdventureBot</h2>
        <div className="mt-4 h-px luminous-line" />
        <p className="mt-4 text-sm text-slate-300">Frosted, luminous control suite for live content updates.</p>
      </div>

      <nav className="mt-10 space-y-2">
        {items.map((item) => (
          <button
            key={item}
            type="button"
            onClick={() => onSelect(item)}
            className={clsx(
              "w-full flex items-center justify-between px-4 py-3 rounded-xl text-sm transition",
              item === active
                ? "bg-aurora-cyan/20 border border-aurora-cyan/60 text-white shadow-glow"
                : "text-slate-300 hover:bg-white/5"
            )}
          >
            <span>{item}</span>
            {item === active ? <span className="text-[10px] uppercase">Active</span> : null}
          </button>
        ))}
      </nav>

      <div className="mt-auto pt-8 text-xs text-slate-500">
        <p>Service: /opt/AdventureTools</p>
        <p>Mode: Authoring (live DB)</p>
      </div>
    </aside>
  );
}
