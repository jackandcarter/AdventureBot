import { useState } from "react";
import { FormField } from "../components/FormField";
import { JsonEditor } from "../components/JsonEditor";
import { WizardActions } from "../components/WizardActions";
import { WizardSection } from "../components/WizardSection";

const inputClassName =
  "w-full rounded-2xl border border-white/10 bg-night-900/60 px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-aurora-violet/70";

const textareaClassName = `${inputClassName} min-h-[120px]`;

const isValidJson = (value: string) => {
  if (!value.trim()) {
    return "JSON is required.";
  }
  try {
    JSON.parse(value);
    return "";
  } catch {
    return "Enter valid JSON.";
  }
};

type ItemCreateForm = {
  name: string;
  type: string;
  rarity: string;
  iconUrl: string;
  description: string;
  effectJson: string;
  price: string;
  vendorStock: string;
  distributionJson: string;
};

type ItemUpdateForm = {
  target: string;
  price: string;
  cooldown: string;
  effectJson: string;
  placementJson: string;
};

const initialCreateForm: ItemCreateForm = {
  name: "",
  type: "",
  rarity: "",
  iconUrl: "",
  description: "",
  effectJson: "{\n  \"effects\": []\n}",
  price: "",
  vendorStock: "",
  distributionJson: "{\n  \"vendors\": [],\n  \"drops\": []\n}"
};

const initialUpdateForm: ItemUpdateForm = {
  target: "",
  price: "",
  cooldown: "",
  effectJson: "{\n  \"effects\": []\n}",
  placementJson: "{\n  \"vendors\": [],\n  \"chests\": []\n}"
};

export function ItemsPage() {
  const [createForm, setCreateForm] = useState(initialCreateForm);
  const [updateForm, setUpdateForm] = useState(initialUpdateForm);
  const [createTouched, setCreateTouched] = useState(false);
  const [updateTouched, setUpdateTouched] = useState(false);
  const [createMessage, setCreateMessage] = useState("");
  const [updateMessage, setUpdateMessage] = useState("");

  const createErrors = {
    name: createForm.name.trim() ? "" : "Item name is required.",
    type: createForm.type ? "" : "Select an item type.",
    rarity: createForm.rarity ? "" : "Select a rarity tier.",
    iconUrl: createForm.iconUrl.trim() ? "" : "Provide an icon URL.",
    description: createForm.description.trim() ? "" : "Add a short description.",
    effectJson: isValidJson(createForm.effectJson),
    price:
      createForm.price && Number(createForm.price) >= 0
        ? ""
        : "Enter a price value.",
    vendorStock:
      createForm.vendorStock && Number(createForm.vendorStock) >= 0
        ? ""
        : "Enter vendor stock quantity.",
    distributionJson: isValidJson(createForm.distributionJson)
  };

  const updateErrors = {
    target: updateForm.target.trim() ? "" : "Select an item to update.",
    price:
      !updateForm.price || Number(updateForm.price) >= 0
        ? ""
        : "Enter a valid price.",
    cooldown:
      !updateForm.cooldown || Number(updateForm.cooldown) >= 0
        ? ""
        : "Enter a cooldown value.",
    effectJson: isValidJson(updateForm.effectJson),
    placementJson: isValidJson(updateForm.placementJson)
  };

  const handleCreateAction = (message: string) => {
    setCreateTouched(true);
    const hasErrors = Object.values(createErrors).some((error) => error);
    setCreateMessage(hasErrors ? "Resolve validation errors before continuing." : message);
  };

  const handleUpdateAction = (message: string) => {
    setUpdateTouched(true);
    const hasErrors = Object.values(updateErrors).some((error) => error);
    setUpdateMessage(hasErrors ? "Resolve validation errors before continuing." : message);
  };

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
        <WizardSection
          title="Item Creation"
          badge="Wizard Draft"
          description="Define item identity, gameplay effects, and distribution defaults."
        >
          <div className="grid gap-4">
            <FormField
              label="Item name"
              htmlFor="item-name"
              error={createTouched ? createErrors.name : undefined}
            >
              <input
                id="item-name"
                className={inputClassName}
                value={createForm.name}
                onChange={(event) => setCreateForm({ ...createForm, name: event.target.value })}
                placeholder="Phoenix Tonic"
              />
            </FormField>
            <div className="grid gap-4 md:grid-cols-2">
              <FormField
                label="Item type"
                htmlFor="item-type"
                error={createTouched ? createErrors.type : undefined}
              >
                <select
                  id="item-type"
                  className={inputClassName}
                  value={createForm.type}
                  onChange={(event) => setCreateForm({ ...createForm, type: event.target.value })}
                >
                  <option value="">Select type</option>
                  <option value="consumable">Consumable</option>
                  <option value="weapon">Weapon</option>
                  <option value="armor">Armor</option>
                  <option value="key-item">Key Item</option>
                </select>
              </FormField>
              <FormField
                label="Rarity tier"
                htmlFor="item-rarity"
                error={createTouched ? createErrors.rarity : undefined}
              >
                <select
                  id="item-rarity"
                  className={inputClassName}
                  value={createForm.rarity}
                  onChange={(event) =>
                    setCreateForm({ ...createForm, rarity: event.target.value })
                  }
                >
                  <option value="">Select tier</option>
                  <option value="common">Common</option>
                  <option value="rare">Rare</option>
                  <option value="legendary">Legendary</option>
                </select>
              </FormField>
            </div>
            <div className="grid gap-4 md:grid-cols-2">
              <FormField
                label="Icon URL"
                htmlFor="item-icon"
                error={createTouched ? createErrors.iconUrl : undefined}
              >
                <input
                  id="item-icon"
                  className={inputClassName}
                  value={createForm.iconUrl}
                  onChange={(event) =>
                    setCreateForm({ ...createForm, iconUrl: event.target.value })
                  }
                  placeholder="https://"
                />
              </FormField>
              <FormField
                label="Base price"
                htmlFor="item-price"
                error={createTouched ? createErrors.price : undefined}
              >
                <input
                  id="item-price"
                  type="number"
                  className={inputClassName}
                  value={createForm.price}
                  onChange={(event) => setCreateForm({ ...createForm, price: event.target.value })}
                />
              </FormField>
            </div>
            <FormField
              label="Description"
              htmlFor="item-description"
              error={createTouched ? createErrors.description : undefined}
            >
              <textarea
                id="item-description"
                className={textareaClassName}
                value={createForm.description}
                onChange={(event) =>
                  setCreateForm({ ...createForm, description: event.target.value })
                }
                placeholder="Short flavor copy for the codex."
              />
            </FormField>
            <FormField
              label="Effect payload"
              hint="JSON"
              error={createTouched ? createErrors.effectJson : undefined}
            >
              <JsonEditor
                value={createForm.effectJson}
                onChange={(value) => setCreateForm({ ...createForm, effectJson: value })}
                invalid={createTouched && Boolean(createErrors.effectJson)}
              />
            </FormField>
            <div className="grid gap-4 md:grid-cols-2">
              <FormField
                label="Vendor stock"
                htmlFor="item-stock"
                error={createTouched ? createErrors.vendorStock : undefined}
              >
                <input
                  id="item-stock"
                  type="number"
                  className={inputClassName}
                  value={createForm.vendorStock}
                  onChange={(event) =>
                    setCreateForm({ ...createForm, vendorStock: event.target.value })
                  }
                />
              </FormField>
              <FormField label="Default vendor" htmlFor="item-vendor">
                <select
                  id="item-vendor"
                  className={inputClassName}
                  value={createForm.distributionJson}
                  onChange={(event) =>
                    setCreateForm({ ...createForm, distributionJson: event.target.value })
                  }
                >
                  <option value={createForm.distributionJson}>Use distribution JSON</option>
                  <option
                    value={`{\n  \"vendors\": [\"starter-bazaar\"],\n  \"drops\": []\n}`}
                  >
                    Starter Bazaar
                  </option>
                  <option value={`{\n  \"vendors\": [\"sky-dock\"],\n  \"drops\": []\n}`}>
                    Sky Dock
                  </option>
                </select>
              </FormField>
            </div>
            <FormField
              label="Distribution overrides"
              hint="JSON"
              error={createTouched ? createErrors.distributionJson : undefined}
            >
              <JsonEditor
                value={createForm.distributionJson}
                onChange={(value) => setCreateForm({ ...createForm, distributionJson: value })}
                invalid={createTouched && Boolean(createErrors.distributionJson)}
              />
            </FormField>
          </div>
          <WizardActions
            message={createMessage}
            onSaveDraft={() => handleCreateAction("Draft saved for item creation.")}
            onPublish={() => handleCreateAction("Item creation draft queued for publish.")}
          />
        </WizardSection>

        <WizardSection
          title="Item Update"
          badge="Wizard Draft"
          description="Patch live items with updated effects, price bands, and placement."
        >
          <div className="grid gap-4">
            <FormField
              label="Target item"
              htmlFor="item-target"
              error={updateTouched ? updateErrors.target : undefined}
            >
              <input
                id="item-target"
                className={inputClassName}
                value={updateForm.target}
                onChange={(event) => setUpdateForm({ ...updateForm, target: event.target.value })}
                placeholder="Search by name or ID"
              />
            </FormField>
            <div className="grid gap-4 md:grid-cols-2">
              <FormField
                label="New price"
                htmlFor="item-update-price"
                error={updateTouched ? updateErrors.price : undefined}
              >
                <input
                  id="item-update-price"
                  type="number"
                  className={inputClassName}
                  value={updateForm.price}
                  onChange={(event) => setUpdateForm({ ...updateForm, price: event.target.value })}
                  placeholder="Leave empty to keep"
                />
              </FormField>
              <FormField
                label="Cooldown (turns)"
                htmlFor="item-update-cooldown"
                error={updateTouched ? updateErrors.cooldown : undefined}
              >
                <input
                  id="item-update-cooldown"
                  type="number"
                  className={inputClassName}
                  value={updateForm.cooldown}
                  onChange={(event) =>
                    setUpdateForm({ ...updateForm, cooldown: event.target.value })
                  }
                  placeholder="Optional"
                />
              </FormField>
            </div>
            <FormField
              label="Effect patch"
              hint="JSON"
              error={updateTouched ? updateErrors.effectJson : undefined}
            >
              <JsonEditor
                value={updateForm.effectJson}
                onChange={(value) => setUpdateForm({ ...updateForm, effectJson: value })}
                invalid={updateTouched && Boolean(updateErrors.effectJson)}
              />
            </FormField>
            <FormField
              label="Placement adjustments"
              hint="JSON"
              error={updateTouched ? updateErrors.placementJson : undefined}
            >
              <JsonEditor
                value={updateForm.placementJson}
                onChange={(value) => setUpdateForm({ ...updateForm, placementJson: value })}
                invalid={updateTouched && Boolean(updateErrors.placementJson)}
              />
            </FormField>
          </div>
          <WizardActions
            message={updateMessage}
            onSaveDraft={() => handleUpdateAction("Draft saved for item update.")}
            onPublish={() => handleUpdateAction("Item update draft queued for publish.")}
          />
        </WizardSection>
      </section>
    </div>
  );
}
