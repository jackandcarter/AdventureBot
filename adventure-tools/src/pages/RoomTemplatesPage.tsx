export function RoomTemplatesPage() {
  return (
    <div className="space-y-8">
      <section className="glass-panel rounded-3xl p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-xs uppercase tracking-[0.3em] text-slate-400">World Builder</p>
            <h2 className="text-3xl font-display">Room Template Authoring</h2>
            <p className="mt-2 text-sm text-slate-300 max-w-2xl">
              Design modular rooms with encounter hooks, loot drops, and traversal logic.
            </p>
          </div>
          <div className="text-right text-xs text-slate-400">
            <p>Database</p>
            <p className="text-aurora-cyan">adventure.rooms</p>
          </div>
        </div>
      </section>

      <section className="grid lg:grid-cols-2 gap-6">
        <div className="glass-panel rounded-3xl p-6">
          <div className="flex items-center justify-between">
            <h3 className="text-xl font-display">Template Creation Flow</h3>
            <span className="text-xs text-aurora-lime">Wizard Draft</span>
          </div>
          <ol className="mt-6 grid gap-4 text-sm text-slate-300">
            <li className="flex gap-3">
              <span className="text-aurora-cyan font-semibold">01</span>
              <div>
                <p className="text-white">Layout Blueprint</p>
                <p>Pick geometry, exits, and encounter capacity.</p>
              </div>
            </li>
            <li className="flex gap-3">
              <span className="text-aurora-violet font-semibold">02</span>
              <div>
                <p className="text-white">Room Theme</p>
                <p>Assign biome, ambience, and prop collections.</p>
              </div>
            </li>
            <li className="flex gap-3">
              <span className="text-aurora-magenta font-semibold">03</span>
              <div>
                <p className="text-white">Encounter Hooks</p>
                <p>Define spawn tables, puzzles, or narrative triggers.</p>
              </div>
            </li>
            <li className="flex gap-3">
              <span className="text-aurora-amber font-semibold">04</span>
              <div>
                <p className="text-white">Reward Tables</p>
                <p>Attach loot, vendor portals, and relic drops.</p>
              </div>
            </li>
          </ol>
        </div>

        <div className="glass-panel rounded-3xl p-6">
          <div className="flex items-center justify-between">
            <h3 className="text-xl font-display">Template Revision Flow</h3>
            <span className="text-xs text-aurora-lime">Wizard Draft</span>
          </div>
          <ol className="mt-6 grid gap-4 text-sm text-slate-300">
            <li className="flex gap-2">
              <span className="text-aurora-cyan font-semibold">01</span>
              <div>
                <p className="text-white">Select Template</p>
                <p>Search by biome or ID to load active room data.</p>
              </div>
            </li>
            <li className="flex gap-2">
              <span className="text-aurora-violet font-semibold">02</span>
              <div>
                <p className="text-white">Patch Layout</p>
                <p>Update exit rules, enemy cap, or traversal blockers.</p>
              </div>
            </li>
            <li className="flex gap-2">
              <span className="text-aurora-magenta font-semibold">03</span>
              <div>
                <p className="text-white">Rebalance Hooks</p>
                <p>Adjust spawn rates, puzzle timers, and narrative beats.</p>
              </div>
            </li>
            <li className="flex gap-2">
              <span className="text-aurora-amber font-semibold">04</span>
              <div>
                <p className="text-white">Publish</p>
                <p>Validate navigation graphs and save the new version.</p>
              </div>
            </li>
          </ol>
        </div>
      </section>
    </div>
  );
}
