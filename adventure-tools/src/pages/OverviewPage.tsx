export function OverviewPage() {
  return (
    <div className="space-y-8">
      <section className="glass-panel rounded-3xl p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-xs uppercase tracking-[0.3em] text-slate-400">Command Center</p>
            <h2 className="text-3xl font-display">Adventure Overview</h2>
            <p className="mt-2 text-sm text-slate-300 max-w-2xl">
              Monitor content pipelines, staging queues, and upcoming authoring milestones.
            </p>
          </div>
          <div className="text-right text-xs text-slate-400">
            <p>Status</p>
            <p className="text-aurora-cyan">6 modules live</p>
          </div>
        </div>
      </section>

      <section className="grid lg:grid-cols-2 gap-6">
        <div className="glass-panel rounded-3xl p-6">
          <div className="flex items-center justify-between">
            <h3 className="text-xl font-display">Pipeline Health</h3>
            <span className="text-xs text-aurora-lime">Live Sync</span>
          </div>
          <ol className="mt-6 grid gap-4 text-sm text-slate-300">
            <li className="flex gap-3">
              <span className="text-aurora-cyan font-semibold">01</span>
              <div>
                <p className="text-white">Authoring Queue</p>
                <p>24 drafts waiting for review across enemies, items, and classes.</p>
              </div>
            </li>
            <li className="flex gap-3">
              <span className="text-aurora-violet font-semibold">02</span>
              <div>
                <p className="text-white">Balance Review</p>
                <p>5 balance passes scheduled for resistances and eidolon kits.</p>
              </div>
            </li>
            <li className="flex gap-3">
              <span className="text-aurora-magenta font-semibold">03</span>
              <div>
                <p className="text-white">Lore Alignment</p>
                <p>2 story beats flagged for narrative approval.</p>
              </div>
            </li>
            <li className="flex gap-3">
              <span className="text-aurora-amber font-semibold">04</span>
              <div>
                <p className="text-white">Release Ready</p>
                <p>12 assets queued for export into the nightly build.</p>
              </div>
            </li>
          </ol>
        </div>

        <div className="glass-panel rounded-3xl p-6">
          <div className="flex items-center justify-between">
            <h3 className="text-xl font-display">Upcoming Milestones</h3>
            <span className="text-xs text-aurora-lime">Next Sprint</span>
          </div>
          <ol className="mt-6 grid gap-4 text-sm text-slate-300">
            <li className="flex gap-2">
              <span className="text-aurora-cyan font-semibold">01</span>
              <div>
                <p className="text-white">Zone 7 Rooms</p>
                <p>Finalize the room template set for the etheric sanctum.</p>
              </div>
            </li>
            <li className="flex gap-2">
              <span className="text-aurora-violet font-semibold">02</span>
              <div>
                <p className="text-white">Vendor Refresh</p>
                <p>Curate new item rotations and discount tables.</p>
              </div>
            </li>
            <li className="flex gap-2">
              <span className="text-aurora-magenta font-semibold">03</span>
              <div>
                <p className="text-white">Trance Pass</p>
                <p>Audit trance abilities for cooldown pacing and visuals.</p>
              </div>
            </li>
            <li className="flex gap-2">
              <span className="text-aurora-amber font-semibold">04</span>
              <div>
                <p className="text-white">Launch Checklist</p>
                <p>Lock copy, confirm localization, and export patch notes.</p>
              </div>
            </li>
          </ol>
        </div>
      </section>
    </div>
  );
}
