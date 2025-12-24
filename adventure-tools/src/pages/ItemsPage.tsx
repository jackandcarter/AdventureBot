export function ItemsPage() {
  return (
    <div className="space-y-8">
      <section className="glass-panel rounded-3xl p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-xs uppercase tracking-[0.3em] text-slate-400">Content Zone</p>
            <h2 className="text-3xl font-display">Item Authoring</h2>
            <p className="mt-2 text-sm text-slate-300 max-w-2xl">
              Build and revise item records through the creation and update wizards.
            </p>
          </div>
          <div className="text-right text-xs text-slate-400">
            <p>Database</p>
            <p className="text-aurora-cyan">adventure.items</p>
          </div>
        </div>
      </section>

      <section className="grid lg:grid-cols-2 gap-6">
        <div className="glass-panel rounded-3xl p-6">
          <div className="flex items-center justify-between">
            <h3 className="text-xl font-display">Item Creation Flow</h3>
            <span className="text-xs text-aurora-lime">Wizard Draft</span>
          </div>
          <ol className="mt-6 grid gap-4 text-sm text-slate-300">
            <li className="flex gap-3">
              <span className="text-aurora-cyan font-semibold">01</span>
              <div>
                <p className="text-white">Identity & Art</p>
                <p>Name, item type, rarity tier, icon, and flavor description.</p>
              </div>
            </li>
            <li className="flex gap-3">
              <span className="text-aurora-violet font-semibold">02</span>
              <div>
                <p className="text-white">Effect Payload</p>
                <p>JSON effects, target type, usage limits, and cooldown behavior.</p>
              </div>
            </li>
            <li className="flex gap-3">
              <span className="text-aurora-magenta font-semibold">03</span>
              <div>
                <p className="text-white">Economy</p>
                <p>Price bands, vendor stock defaults, and sell ratios.</p>
              </div>
            </li>
            <li className="flex gap-3">
              <span className="text-aurora-amber font-semibold">04</span>
              <div>
                <p className="text-white">Distribution</p>
                <p>Attach to vendors, enemy drop tables, and loot chests.</p>
              </div>
            </li>
          </ol>
        </div>

        <div className="glass-panel rounded-3xl p-6">
          <div className="flex items-center justify-between">
            <h3 className="text-xl font-display">Item Update Flow</h3>
            <span className="text-xs text-aurora-lime">Wizard Draft</span>
          </div>
          <ol className="mt-6 grid gap-4 text-sm text-slate-300">
            <li className="flex gap-2">
              <span className="text-aurora-cyan font-semibold">01</span>
              <div>
                <p className="text-white">Select Target</p>
                <p>Search by name or item type to load an entry.</p>
              </div>
            </li>
            <li className="flex gap-2">
              <span className="text-aurora-violet font-semibold">02</span>
              <div>
                <p className="text-white">Patch Core Data</p>
                <p>Update item effect payload, usage limit, and pricing.</p>
              </div>
            </li>
            <li className="flex gap-2">
              <span className="text-aurora-magenta font-semibold">03</span>
              <div>
                <p className="text-white">Revise Placement</p>
                <p>Adjust vendor availability and drop table placement.</p>
              </div>
            </li>
            <li className="flex gap-2">
              <span className="text-aurora-amber font-semibold">04</span>
              <div>
                <p className="text-white">Publish</p>
                <p>Review changes and save to the live item catalog.</p>
              </div>
            </li>
          </ol>
        </div>
      </section>
    </div>
  );
}
