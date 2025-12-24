export function VendorsPage() {
  return (
    <div className="space-y-8">
      <section className="glass-panel rounded-3xl p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-xs uppercase tracking-[0.3em] text-slate-400">Market Deck</p>
            <h2 className="text-3xl font-display">Vendor Authoring</h2>
            <p className="mt-2 text-sm text-slate-300 max-w-2xl">
              Configure shop inventories, pricing tiers, and limited-time rotations.
            </p>
          </div>
          <div className="text-right text-xs text-slate-400">
            <p>Database</p>
            <p className="text-aurora-cyan">adventure.vendors</p>
          </div>
        </div>
      </section>

      <section className="grid lg:grid-cols-2 gap-6">
        <div className="glass-panel rounded-3xl p-6">
          <div className="flex items-center justify-between">
            <h3 className="text-xl font-display">Vendor Creation Flow</h3>
            <span className="text-xs text-aurora-lime">Wizard Draft</span>
          </div>
          <ol className="mt-6 grid gap-4 text-sm text-slate-300">
            <li className="flex gap-3">
              <span className="text-aurora-cyan font-semibold">01</span>
              <div>
                <p className="text-white">Identity</p>
                <p>Name, location, portrait, and lore summary.</p>
              </div>
            </li>
            <li className="flex gap-3">
              <span className="text-aurora-violet font-semibold">02</span>
              <div>
                <p className="text-white">Inventory Pool</p>
                <p>Assign item groups, rarity caps, and stock limits.</p>
              </div>
            </li>
            <li className="flex gap-3">
              <span className="text-aurora-magenta font-semibold">03</span>
              <div>
                <p className="text-white">Pricing Rules</p>
                <p>Set markup, discounts, and barter multipliers.</p>
              </div>
            </li>
            <li className="flex gap-3">
              <span className="text-aurora-amber font-semibold">04</span>
              <div>
                <p className="text-white">Rotation Schedule</p>
                <p>Define refresh cadence, featured bundles, and bonuses.</p>
              </div>
            </li>
          </ol>
        </div>

        <div className="glass-panel rounded-3xl p-6">
          <div className="flex items-center justify-between">
            <h3 className="text-xl font-display">Vendor Update Flow</h3>
            <span className="text-xs text-aurora-lime">Wizard Draft</span>
          </div>
          <ol className="mt-6 grid gap-4 text-sm text-slate-300">
            <li className="flex gap-2">
              <span className="text-aurora-cyan font-semibold">01</span>
              <div>
                <p className="text-white">Select Vendor</p>
                <p>Search by shop name or zone to load details.</p>
              </div>
            </li>
            <li className="flex gap-2">
              <span className="text-aurora-violet font-semibold">02</span>
              <div>
                <p className="text-white">Patch Inventory</p>
                <p>Swap items, adjust stock caps, or add bundles.</p>
              </div>
            </li>
            <li className="flex gap-2">
              <span className="text-aurora-magenta font-semibold">03</span>
              <div>
                <p className="text-white">Tune Pricing</p>
                <p>Modify discounts, currency conversions, and deals.</p>
              </div>
            </li>
            <li className="flex gap-2">
              <span className="text-aurora-amber font-semibold">04</span>
              <div>
                <p className="text-white">Publish</p>
                <p>Review the rotation and save the update.</p>
              </div>
            </li>
          </ol>
        </div>
      </section>
    </div>
  );
}
