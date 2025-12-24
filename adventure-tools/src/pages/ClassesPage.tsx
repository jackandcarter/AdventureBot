export function ClassesPage() {
  return (
    <div className="space-y-8">
      <section className="glass-panel rounded-3xl p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-xs uppercase tracking-[0.3em] text-slate-400">Content Zone</p>
            <h2 className="text-3xl font-display">Class Authoring</h2>
            <p className="mt-2 text-sm text-slate-300 max-w-2xl">
              Create and update class records through the wizard flows below.
            </p>
          </div>
          <div className="text-right text-xs text-slate-400">
            <p>Database</p>
            <p className="text-aurora-cyan">adventure.classes</p>
          </div>
        </div>
      </section>

      <section className="grid lg:grid-cols-2 gap-6">
        <div className="glass-panel rounded-3xl p-6">
          <div className="flex items-center justify-between">
            <h3 className="text-xl font-display">Class Creation Flow</h3>
            <span className="text-xs text-aurora-lime">Wizard Draft</span>
          </div>
          <ol className="mt-6 grid gap-4 text-sm text-slate-300">
            <li className="flex gap-3">
              <span className="text-aurora-cyan font-semibold">01</span>
              <div>
                <p className="text-white">Identity & Fantasy</p>
                <p>Name, lore, visual identity, and role archetype.</p>
              </div>
            </li>
            <li className="flex gap-3">
              <span className="text-aurora-violet font-semibold">02</span>
              <div>
                <p className="text-white">Base Stats</p>
                <p>HP/MP baselines, offense/defense, accuracy, and speed.</p>
              </div>
            </li>
            <li className="flex gap-3">
              <span className="text-aurora-magenta font-semibold">03</span>
              <div>
                <p className="text-white">Ability Progression</p>
                <p>Unlock levels, temporary abilities, and milestone rewards.</p>
              </div>
            </li>
            <li className="flex gap-3">
              <span className="text-aurora-amber font-semibold">04</span>
              <div>
                <p className="text-white">Trance Variants</p>
                <p>Trance duration, ability swaps, and visual overrides.</p>
              </div>
            </li>
          </ol>
        </div>

        <div className="glass-panel rounded-3xl p-6">
          <div className="flex items-center justify-between">
            <h3 className="text-xl font-display">Class Update Flow</h3>
            <span className="text-xs text-aurora-lime">Wizard Draft</span>
          </div>
          <ol className="mt-6 grid gap-4 text-sm text-slate-300">
            <li className="flex gap-2">
              <span className="text-aurora-cyan font-semibold">01</span>
              <div>
                <p className="text-white">Select Target</p>
                <p>Search class name to load the current profile.</p>
              </div>
            </li>
            <li className="flex gap-2">
              <span className="text-aurora-violet font-semibold">02</span>
              <div>
                <p className="text-white">Patch Stats</p>
                <p>Adjust baselines for HP/MP, offense/defense, and speed.</p>
              </div>
            </li>
            <li className="flex gap-2">
              <span className="text-aurora-magenta font-semibold">03</span>
              <div>
                <p className="text-white">Update Progression</p>
                <p>Modify unlocks, temp skills, and trance configuration.</p>
              </div>
            </li>
            <li className="flex gap-2">
              <span className="text-aurora-amber font-semibold">04</span>
              <div>
                <p className="text-white">Publish</p>
                <p>Review changes and save the updated class.</p>
              </div>
            </li>
          </ol>
        </div>
      </section>
    </div>
  );
}
