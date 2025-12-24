const statCards = [
  { label: "Active Enemy Entries", value: "132", accentClass: "bg-aurora-cyan/70" },
  { label: "Boss / Miniboss", value: "21", accentClass: "bg-aurora-violet/70" },
  { label: "Element Links", value: "48", accentClass: "bg-aurora-magenta/70" },
  { label: "Pending Balance Pass", value: "7", accentClass: "bg-aurora-amber/70" }
];

const schemaFields = [
  { column: "enemy_id", type: "int", details: "Primary key, auto increment" },
  { column: "enemy_name", type: "varchar(50)", details: "Display name" },
  { column: "role", type: "enum", details: "normal | miniboss | boss | eidolon" },
  { column: "description", type: "text", details: "Lore + flavor" },
  { column: "hp / max_hp", type: "int", details: "Base and max HP" },
  { column: "attack_power", type: "int", details: "Physical scaling" },
  { column: "magic_power", type: "int", details: "Magic scaling" },
  { column: "defense / magic_defense", type: "int", details: "Mitigation" },
  { column: "speed / atb_max", type: "int", details: "Turn cadence" },
  { column: "abilities", type: "json", details: "Optional inline ability list" },
  { column: "loot_item_id", type: "int", details: "FK → items.item_id" },
  { column: "created_at", type: "timestamp", details: "Auto timestamp" }
];

const relatedTables = [
  {
    name: "enemy_abilities",
    purpose: "Weighted ability rotations + scaling factors",
    fields: "enemy_id, ability_id, weight, scaling_stat, scaling_factor"
  },
  {
    name: "enemy_resistances",
    purpose: "Elemental weaknesses/absorbs",
    fields: "enemy_id, element_id, relation, multiplier"
  },
  {
    name: "enemy_drops",
    purpose: "Item drops and chance",
    fields: "enemy_id, item_id, drop_chance"
  }
];

export function EnemiesPage() {
  return (
    <div className="space-y-8">
      <section className="glass-panel rounded-3xl p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-xs uppercase tracking-[0.3em] text-slate-400">Content Zone</p>
            <h2 className="text-3xl font-display">Enemy Authoring</h2>
            <p className="mt-2 text-sm text-slate-300 max-w-2xl">
              Design and tune enemy entities, minibosses, bosses, and eidolons. Updates apply to live gameplay
              content without touching session state.
            </p>
          </div>
          <div className="text-right text-xs text-slate-400">
            <p>Database</p>
            <p className="text-aurora-cyan">adventure.enemies</p>
          </div>
        </div>
      </section>

      <section className="grid md:grid-cols-2 xl:grid-cols-4 gap-4">
        {statCards.map((card) => (
          <div key={card.label} className="glass-panel rounded-2xl p-5 relative overflow-hidden">
            <div className={`absolute inset-x-6 top-0 h-px ${card.accentClass}`} aria-hidden="true" />
            <p className="text-xs uppercase tracking-[0.3em] text-slate-500">{card.label}</p>
            <p className="mt-4 text-3xl font-display text-white">{card.value}</p>
          </div>
        ))}
      </section>

      <section className="grid lg:grid-cols-[2fr_1fr] gap-6">
        <div className="glass-panel rounded-3xl p-6">
          <div className="flex items-center justify-between">
            <h3 className="text-xl font-display">Enemy Creation Flow</h3>
            <span className="text-xs text-aurora-lime">Wizard Draft</span>
          </div>
          <ol className="mt-6 grid gap-4 text-sm text-slate-300">
            <li className="flex gap-3">
              <span className="text-aurora-cyan font-semibold">01</span>
              <div>
                <p className="text-white">Base Identity</p>
                <p>Name, role, lore description, images, difficulty tier.</p>
              </div>
            </li>
            <li className="flex gap-3">
              <span className="text-aurora-violet font-semibold">02</span>
              <div>
                <p className="text-white">Stat Blueprint</p>
                <p>HP/MP, attack/magic, defenses, accuracy, evasion, speed/ATB.</p>
              </div>
            </li>
            <li className="flex gap-3">
              <span className="text-aurora-magenta font-semibold">03</span>
              <div>
                <p className="text-white">Ability Rotation</p>
                <p>Assign abilities, weights, scaling stats, healing thresholds.</p>
              </div>
            </li>
            <li className="flex gap-3">
              <span className="text-aurora-amber font-semibold">04</span>
              <div>
                <p className="text-white">Resistances & Drops</p>
                <p>Element relations, loot table, gil/xp reward defaults.</p>
              </div>
            </li>
          </ol>
        </div>

        <div className="glass-panel rounded-3xl p-6">
          <h3 className="text-xl font-display">Live Guardrails</h3>
          <ul className="mt-4 space-y-3 text-sm text-slate-300">
            <li className="flex gap-2">
              <span className="text-aurora-cyan">●</span>
              Changes apply to content only; session tables remain untouched.
            </li>
            <li className="flex gap-2">
              <span className="text-aurora-violet">●</span>
              FK constraints validate items, elements, abilities.
            </li>
            <li className="flex gap-2">
              <span className="text-aurora-magenta">●</span>
              JSON schema checks keep ability payloads valid.
            </li>
          </ul>
          <div className="mt-6 rounded-2xl border border-white/10 bg-white/5 p-4">
            <p className="text-xs uppercase tracking-[0.3em] text-slate-500">Next Turn Safety</p>
            <p className="mt-2 text-sm text-slate-200">
              Updates load on next enemy spawn or turn refresh. Active sessions continue without runtime mutation.
            </p>
          </div>
        </div>
      </section>

      <section className="glass-panel rounded-3xl p-6">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-xl font-display">Schema: enemies</h3>
            <p className="text-sm text-slate-400">Primary table for enemy definitions.</p>
          </div>
          <button className="px-4 py-2 rounded-full border border-white/15 text-xs text-slate-200">
            View SQL Snapshot
          </button>
        </div>
        <div className="mt-6 overflow-hidden rounded-2xl border border-white/10">
          <table className="w-full text-sm">
            <thead className="bg-white/5 text-xs uppercase tracking-[0.3em] text-slate-400">
              <tr>
                <th className="px-4 py-3 text-left">Column</th>
                <th className="px-4 py-3 text-left">Type</th>
                <th className="px-4 py-3 text-left">Details</th>
              </tr>
            </thead>
            <tbody>
              {schemaFields.map((field) => (
                <tr key={field.column} className="border-t border-white/5">
                  <td className="px-4 py-3 text-slate-100">{field.column}</td>
                  <td className="px-4 py-3 text-aurora-cyan">{field.type}</td>
                  <td className="px-4 py-3 text-slate-300">{field.details}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="glass-panel rounded-3xl p-6">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-xl font-display">Related Tables</h3>
            <p className="text-sm text-slate-400">Companion structures for enemy behaviors.</p>
          </div>
          <span className="text-xs text-aurora-lime">3 linked tables</span>
        </div>
        <div className="mt-6 grid md:grid-cols-3 gap-4">
          {relatedTables.map((table) => (
            <div key={table.name} className="rounded-2xl border border-white/10 bg-white/5 p-4">
              <p className="text-sm text-white font-medium">{table.name}</p>
              <p className="mt-2 text-xs text-slate-400">{table.purpose}</p>
              <p className="mt-3 text-xs text-slate-300">{table.fields}</p>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
