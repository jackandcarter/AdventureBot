import { Sidebar } from "./Sidebar";

const navItems = [
  "Overview",
  "Enemies",
  "Items",
  "Classes",
  "Abilities",
  "Resistances",
  "Room Templates",
  "Eidolons",
  "Trance Abilities",
  "Vendors"
];

export function Layout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen flex text-slate-100">
      <Sidebar items={navItems} active="Enemies" />
      <div className="flex-1 flex flex-col">
        <header className="px-8 py-6 border-b border-white/10 bg-night-850/70 backdrop-blur">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs uppercase tracking-[0.3em] text-slate-400">Adventure Tools Suite</p>
              <h1 className="text-2xl font-display text-white">Content Authoring Console</h1>
            </div>
            <div className="flex items-center gap-3">
              <div className="px-4 py-2 rounded-full border border-white/10 bg-white/5 text-xs text-slate-200">
                Connected: adventure@localhost
              </div>
              <button className="px-4 py-2 rounded-full bg-aurora-violet/80 text-sm text-white shadow-glow">
                New Entry
              </button>
            </div>
          </div>
        </header>
        <main className="flex-1 px-8 py-8">{children}</main>
      </div>
    </div>
  );
}
