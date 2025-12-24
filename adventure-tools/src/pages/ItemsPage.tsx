const metricCards = [
  { label: "Item Entries", value: "9", accentClass: "bg-aurora-cyan/70" },
  { label: "Consumables", value: "6", accentClass: "bg-aurora-lime/70" },
  { label: "Quest Items", value: "2", accentClass: "bg-aurora-violet/70" },
  { label: "Equipment", value: "1", accentClass: "bg-aurora-magenta/70" }
];

const itemSchemaFields = [
  { column: "item_id", type: "int", details: "Primary key, auto increment" },
  { column: "item_name", type: "varchar(100)", details: "Display name" },
  { column: "description", type: "text", details: "Lore + usage" },
  { column: "effect", type: "json", details: "Effect payload" },
  { column: "type", type: "enum", details: "consumable | equipment | quest" },
  { column: "usage_limit", type: "int", details: "Stack usage count" },
  { column: "price", type: "int", details: "Shop price" },
  { column: "store_stock", type: "int", details: "Optional vendor stock" },
  { column: "target_type", type: "enum", details: "self | ally | enemy | any" },
  { column: "image_url", type: "varchar(255)", details: "Icon or art URL" },
  { column: "created_at", type: "timestamp", details: "Auto timestamp" }
];

const itemRelations = [
  {
    name: "item_effects",
    purpose: "Status effect links",
    fields: "item_id, effect_id"
  }
];

export function ItemsPage() {
  return (
    <div className="space-y-8">
      <section className="glass-panel rounded-3xl p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-xs uppercase tracking-[0.3em] text-slate-400">Content Zone</p>
            <h2 className="text-3xl font-display">Item Authoring</h2>
            <p className="mt-2 text-sm text-slate-300 max-w-2xl">
              Define consumables, equipment, and quest items with structured effect payloads for the live game
              database.
            </p>
          </div>
          <div className="text-right text-xs text-slate-400">
            <p>Database</p>
            <p className="text-aurora-cyan">adventure.items</p>
          </div>
        </div>
      </section>

      <section className="grid md:grid-cols-2 xl:grid-cols-4 gap-4">
        {metricCards.map((card) => (
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
            <h3 className="text-xl font-display">Item Creation Flow</h3>
            <span className="text-xs text-aurora-lime">Wizard Draft</span>
          </div>
          <ol className="mt-6 grid gap-4 text-sm text-slate-300">
            <li className="flex gap-3">
              <span className="text-aurora-cyan font-semibold">01</span>
              <div>
                <p className="text-white">Identity + Type</p>
                <p>Name, type, icon art, and display copy.</p>
              </div>
            </li>
            <li className="flex gap-3">
              <span className="text-aurora-violet font-semibold">02</span>
              <div>
                <p className="text-white">Effect Payload</p>
                <p>JSON effect schema for heal, revive, buffs, or damage.</p>
              </div>
            </li>
            <li className="flex gap-3">
              <span className="text-aurora-magenta font-semibold">03</span>
              <div>
                <p className="text-white">Economy Hooks</p>
                <p>Pricing, store stock, and usage limits.</p>
              </div>
            </li>
            <li className="flex gap-3">
              <span className="text-aurora-amber font-semibold">04</span>
              <div>
                <p className="text-white">Status Links</p>
                <p>Assign status effects through item_effects for synergy.</p>
              </div>
            </li>
          </ol>
        </div>

        <div className="glass-panel rounded-3xl p-6">
          <h3 className="text-xl font-display">Live Guardrails</h3>
          <ul className="mt-4 space-y-3 text-sm text-slate-300">
            <li className="flex gap-2">
              <span className="text-aurora-cyan">●</span>
              Item edits update definitions without touching player inventories.
            </li>
            <li className="flex gap-2">
              <span className="text-aurora-violet">●</span>
              JSON validation ensures consistent effects on refresh.
            </li>
            <li className="flex gap-2">
              <span className="text-aurora-magenta">●</span>
              Linked status effects are enforced via foreign keys.
            </li>
          </ul>
          <div className="mt-6 rounded-2xl border border-white/10 bg-white/5 p-4">
            <p className="text-xs uppercase tracking-[0.3em] text-slate-500">Update Window</p>
            <p className="mt-2 text-sm text-slate-200">
              Item changes apply on next usage or inventory refresh.
            </p>
          </div>
        </div>
      </section>

      <section className="glass-panel rounded-3xl p-6">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-xl font-display">Schema: items</h3>
            <p className="text-sm text-slate-400">Primary table for items.</p>
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
              {itemSchemaFields.map((field) => (
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
            <p className="text-sm text-slate-400">Companion structures for item metadata.</p>
          </div>
          <span className="text-xs text-aurora-lime">1 linked table</span>
        </div>
        <div className="mt-6 grid md:grid-cols-3 gap-4">
          {itemRelations.map((table) => (
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
