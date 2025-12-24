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

type AbilityCreateForm = {
  name: string;
  icon: string;
  target: string;
  element: string;
  trigger: string;
  description: string;
  effectJson: string;
  mpCost: string;
  cooldown: string;
  distributionJson: string;
};

type AbilityUpdateForm = {
  target: string;
  scalingStat: string;
  effectJson: string;
  distributionJson: string;
};

const initialCreateForm: AbilityCreateForm = {
  name: "",
  icon: "",
  target: "",
  element: "",
  trigger: "manual",
  description: "",
  effectJson: "{\n  \"formula\": \"\",\n  \"status\": []\n}",
  mpCost: "",
  cooldown: "",
  distributionJson: "{\n  \"classes\": [],\n  \"enemies\": []\n}"
};

const initialUpdateForm: AbilityUpdateForm = {
  target: "",
  scalingStat: "",
  effectJson: "{\n  \"formula\": \"\",\n  \"status\": []\n}",
  distributionJson: "{\n  \"classes\": [],\n  \"enemies\": []\n}"
};

export function AbilitiesPage() {
  const [createForm, setCreateForm] = useState(initialCreateForm);
  const [updateForm, setUpdateForm] = useState(initialUpdateForm);
  const [createTouched, setCreateTouched] = useState(false);
  const [updateTouched, setUpdateTouched] = useState(false);
  const [createMessage, setCreateMessage] = useState("");
  const [updateMessage, setUpdateMessage] = useState("");

  const createErrors = {
    name: createForm.name.trim() ? "" : "Ability name is required.",
    icon: createForm.icon.trim() ? "" : "Provide an icon reference.",
    target: createForm.target ? "" : "Select a targeting rule.",
    element: createForm.element ? "" : "Select an element.",
    description: createForm.description.trim() ? "" : "Add a short description.",
    effectJson: isValidJson(createForm.effectJson),
    mpCost:
      createForm.mpCost && Number(createForm.mpCost) >= 0
        ? ""
        : "Enter an MP cost.",
    cooldown:
      createForm.cooldown && Number(createForm.cooldown) >= 0
        ? ""
        : "Enter a cooldown value.",
    distributionJson: isValidJson(createForm.distributionJson)
  };

  const updateErrors = {
    target: updateForm.target.trim() ? "" : "Select an ability to update.",
    scalingStat: updateForm.scalingStat ? "" : "Choose a scaling stat.",
    effectJson: isValidJson(updateForm.effectJson),
    distributionJson: isValidJson(updateForm.distributionJson)
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
            <h2 className="text-3xl font-display">Ability Authoring</h2>
            <p className="mt-2 text-sm text-slate-300 max-w-2xl">
              Create and adjust ability records through the authoring wizards.
            </p>
          </div>
          <div className="text-right text-xs text-slate-400">
            <p>Database</p>
            <p className="text-aurora-cyan">adventure.abilities</p>
          </div>
        </div>
      </section>

      <section className="grid lg:grid-cols-2 gap-6">
        <WizardSection
          title="Ability Creation"
          badge="Wizard Draft"
          description="Define identity, effect payloads, and distribution targets."
        >
          <div className="grid gap-4">
            <FormField
              label="Ability name"
              htmlFor="ability-name"
              error={createTouched ? createErrors.name : undefined}
            >
              <input
                id="ability-name"
                className={inputClassName}
                value={createForm.name}
                onChange={(event) => setCreateForm({ ...createForm, name: event.target.value })}
                placeholder="Solar Flare"
              />
            </FormField>
            <div className="grid gap-4 md:grid-cols-2">
              <FormField
                label="Icon asset"
                htmlFor="ability-icon"
                error={createTouched ? createErrors.icon : undefined}
              >
                <input
                  id="ability-icon"
                  className={inputClassName}
                  value={createForm.icon}
                  onChange={(event) => setCreateForm({ ...createForm, icon: event.target.value })}
                  placeholder="icons/flare.svg"
                />
              </FormField>
              <FormField
                label="Targeting"
                htmlFor="ability-target"
                error={createTouched ? createErrors.target : undefined}
              >
                <select
                  id="ability-target"
                  className={inputClassName}
                  value={createForm.target}
                  onChange={(event) => setCreateForm({ ...createForm, target: event.target.value })}
                >
                  <option value="">Select target</option>
                  <option value="single">Single Target</option>
                  <option value="aoe">Area of Effect</option>
                  <option value="self">Self</option>
                  <option value="ally">Ally</option>
                </select>
              </FormField>
            </div>
            <div className="grid gap-4 md:grid-cols-2">
              <FormField
                label="Element"
                htmlFor="ability-element"
                error={createTouched ? createErrors.element : undefined}
              >
                <select
                  id="ability-element"
                  className={inputClassName}
                  value={createForm.element}
                  onChange={(event) =>
                    setCreateForm({ ...createForm, element: event.target.value })
                  }
                >
                  <option value="">Select element</option>
                  <option value="fire">Fire</option>
                  <option value="ice">Ice</option>
                  <option value="lightning">Lightning</option>
                  <option value="holy">Holy</option>
                  <option value="shadow">Shadow</option>
                </select>
              </FormField>
              <FormField
                label="MP cost"
                htmlFor="ability-mp"
                error={createTouched ? createErrors.mpCost : undefined}
              >
                <input
                  id="ability-mp"
                  type="number"
                  className={inputClassName}
                  value={createForm.mpCost}
                  onChange={(event) => setCreateForm({ ...createForm, mpCost: event.target.value })}
                />
              </FormField>
            </div>
            <FormField
              label="Description"
              htmlFor="ability-description"
              error={createTouched ? createErrors.description : undefined}
            >
              <textarea
                id="ability-description"
                className={textareaClassName}
                value={createForm.description}
                onChange={(event) =>
                  setCreateForm({ ...createForm, description: event.target.value })
                }
                placeholder="Short combat flavor text."
              />
            </FormField>
            <FormField
              label="Effect builder"
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
                label="Cooldown (turns)"
                htmlFor="ability-cooldown"
                error={createTouched ? createErrors.cooldown : undefined}
              >
                <input
                  id="ability-cooldown"
                  type="number"
                  className={inputClassName}
                  value={createForm.cooldown}
                  onChange={(event) =>
                    setCreateForm({ ...createForm, cooldown: event.target.value })
                  }
                />
              </FormField>
              <FormField label="Auto-trigger" htmlFor="ability-trigger">
                <select
                  id="ability-trigger"
                  className={inputClassName}
                  value={createForm.trigger}
                  onChange={(event) =>
                    setCreateForm({ ...createForm, trigger: event.target.value })
                  }
                >
                  <option value="manual">Manual cast</option>
                  <option value="on-hit">Trigger on hit</option>
                  <option value="low-health">Trigger under 30% HP</option>
                </select>
              </FormField>
            </div>
            <FormField
              label="Distribution"
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
            onSaveDraft={() => handleCreateAction("Draft saved for ability creation.")}
            onPublish={() => handleCreateAction("Ability creation draft queued for publish.")}
          />
        </WizardSection>

        <WizardSection
          title="Ability Update"
          badge="Wizard Draft"
          description="Revise live abilities, formulas, and assignment overrides."
        >
          <div className="grid gap-4">
            <FormField
              label="Target ability"
              htmlFor="ability-target-update"
              error={updateTouched ? updateErrors.target : undefined}
            >
              <input
                id="ability-target-update"
                className={inputClassName}
                value={updateForm.target}
                onChange={(event) => setUpdateForm({ ...updateForm, target: event.target.value })}
                placeholder="Search by name or ID"
              />
            </FormField>
            <FormField
              label="Scaling stat"
              htmlFor="ability-scaling"
              error={updateTouched ? updateErrors.scalingStat : undefined}
            >
              <select
                id="ability-scaling"
                className={inputClassName}
                value={updateForm.scalingStat}
                onChange={(event) =>
                  setUpdateForm({ ...updateForm, scalingStat: event.target.value })
                }
              >
                <option value="">Select stat</option>
                <option value="strength">Strength</option>
                <option value="magic">Magic</option>
                <option value="spirit">Spirit</option>
                <option value="dexterity">Dexterity</option>
              </select>
            </FormField>
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
              label="Distribution patch"
              hint="JSON"
              error={updateTouched ? updateErrors.distributionJson : undefined}
            >
              <JsonEditor
                value={updateForm.distributionJson}
                onChange={(value) =>
                  setUpdateForm({ ...updateForm, distributionJson: value })
                }
                invalid={updateTouched && Boolean(updateErrors.distributionJson)}
              />
            </FormField>
          </div>
          <WizardActions
            message={updateMessage}
            onSaveDraft={() => handleUpdateAction("Draft saved for ability update.")}
            onPublish={() => handleUpdateAction("Ability update draft queued for publish.")}
          />
        </WizardSection>
      </section>
    </div>
  );
}
