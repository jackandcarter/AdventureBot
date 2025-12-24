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

type ClassCreateForm = {
  name: string;
  role: string;
  style: string;
  lore: string;
  baseHp: string;
  baseMp: string;
  speed: string;
  progressionJson: string;
  tranceJson: string;
};

type ClassUpdateForm = {
  target: string;
  patchHp: string;
  patchMp: string;
  unlocksJson: string;
  tranceJson: string;
};

const initialCreateForm: ClassCreateForm = {
  name: "",
  role: "",
  style: "regal",
  lore: "",
  baseHp: "",
  baseMp: "",
  speed: "",
  progressionJson: "{\n  \"levels\": []\n}",
  tranceJson: "{\n  \"duration\": 0,\n  \"overrides\": {}\n}"
};

const initialUpdateForm: ClassUpdateForm = {
  target: "",
  patchHp: "",
  patchMp: "",
  unlocksJson: "{\n  \"levels\": []\n}",
  tranceJson: "{\n  \"duration\": 0,\n  \"overrides\": {}\n}"
};

export function ClassesPage() {
  const [createForm, setCreateForm] = useState(initialCreateForm);
  const [updateForm, setUpdateForm] = useState(initialUpdateForm);
  const [createTouched, setCreateTouched] = useState(false);
  const [updateTouched, setUpdateTouched] = useState(false);
  const [createMessage, setCreateMessage] = useState("");
  const [updateMessage, setUpdateMessage] = useState("");

  const createErrors = {
    name: createForm.name.trim() ? "" : "Class name is required.",
    role: createForm.role ? "" : "Select a role archetype.",
    lore: createForm.lore.trim() ? "" : "Provide lore for the class.",
    baseHp:
      createForm.baseHp && Number(createForm.baseHp) > 0
        ? ""
        : "Enter a positive HP value.",
    baseMp:
      createForm.baseMp && Number(createForm.baseMp) >= 0
        ? ""
        : "Enter a non-negative MP value.",
    speed:
      createForm.speed && Number(createForm.speed) > 0
        ? ""
        : "Enter a positive speed value.",
    progressionJson: isValidJson(createForm.progressionJson),
    tranceJson: isValidJson(createForm.tranceJson)
  };

  const updateErrors = {
    target: updateForm.target.trim() ? "" : "Select a class to update.",
    patchHp:
      !updateForm.patchHp || Number(updateForm.patchHp) > 0
        ? ""
        : "Enter a positive HP value.",
    patchMp:
      !updateForm.patchMp || Number(updateForm.patchMp) >= 0
        ? ""
        : "Enter a non-negative MP value.",
    unlocksJson: isValidJson(updateForm.unlocksJson),
    tranceJson: isValidJson(updateForm.tranceJson)
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
        <WizardSection
          title="Class Creation"
          badge="Wizard Draft"
          description="Capture class fantasy, base stats, and progression milestones."
        >
          <div className="grid gap-4">
            <FormField
              label="Class name"
              htmlFor="class-name"
              error={createTouched ? createErrors.name : undefined}
            >
              <input
                id="class-name"
                className={inputClassName}
                value={createForm.name}
                onChange={(event) => setCreateForm({ ...createForm, name: event.target.value })}
                placeholder="Skyward Knight"
              />
            </FormField>
            <div className="grid gap-4 md:grid-cols-2">
              <FormField
                label="Role archetype"
                htmlFor="class-role"
                error={createTouched ? createErrors.role : undefined}
              >
                <select
                  id="class-role"
                  className={inputClassName}
                  value={createForm.role}
                  onChange={(event) => setCreateForm({ ...createForm, role: event.target.value })}
                >
                  <option value="">Select role</option>
                  <option value="tank">Tank</option>
                  <option value="support">Support</option>
                  <option value="damage">Damage</option>
                  <option value="hybrid">Hybrid</option>
                </select>
              </FormField>
              <FormField label="Visual identity" htmlFor="class-style">
                <select
                  id="class-style"
                  className={inputClassName}
                  value={createForm.style}
                  onChange={(event) =>
                    setCreateForm({ ...createForm, style: event.target.value })
                  }
                >
                  <option value="regal">Regal</option>
                  <option value="arcane">Arcane</option>
                  <option value="rogue">Rogue</option>
                  <option value="mystic">Mystic</option>
                </select>
              </FormField>
            </div>
            <FormField
              label="Lore description"
              htmlFor="class-lore"
              error={createTouched ? createErrors.lore : undefined}
            >
              <textarea
                id="class-lore"
                className={textareaClassName}
                value={createForm.lore}
                onChange={(event) => setCreateForm({ ...createForm, lore: event.target.value })}
                placeholder="Story beat for the codex entry."
              />
            </FormField>
            <div className="grid gap-4 md:grid-cols-3">
              <FormField
                label="Base HP"
                htmlFor="class-hp"
                error={createTouched ? createErrors.baseHp : undefined}
              >
                <input
                  id="class-hp"
                  type="number"
                  className={inputClassName}
                  value={createForm.baseHp}
                  onChange={(event) =>
                    setCreateForm({ ...createForm, baseHp: event.target.value })
                  }
                />
              </FormField>
              <FormField
                label="Base MP"
                htmlFor="class-mp"
                error={createTouched ? createErrors.baseMp : undefined}
              >
                <input
                  id="class-mp"
                  type="number"
                  className={inputClassName}
                  value={createForm.baseMp}
                  onChange={(event) =>
                    setCreateForm({ ...createForm, baseMp: event.target.value })
                  }
                />
              </FormField>
              <FormField
                label="Speed"
                htmlFor="class-speed"
                error={createTouched ? createErrors.speed : undefined}
              >
                <input
                  id="class-speed"
                  type="number"
                  className={inputClassName}
                  value={createForm.speed}
                  onChange={(event) =>
                    setCreateForm({ ...createForm, speed: event.target.value })
                  }
                />
              </FormField>
            </div>
            <FormField
              label="Ability progression"
              hint="JSON"
              error={createTouched ? createErrors.progressionJson : undefined}
            >
              <JsonEditor
                value={createForm.progressionJson}
                onChange={(value) => setCreateForm({ ...createForm, progressionJson: value })}
                invalid={createTouched && Boolean(createErrors.progressionJson)}
              />
            </FormField>
            <FormField
              label="Trance variants"
              hint="JSON"
              error={createTouched ? createErrors.tranceJson : undefined}
            >
              <JsonEditor
                value={createForm.tranceJson}
                onChange={(value) => setCreateForm({ ...createForm, tranceJson: value })}
                invalid={createTouched && Boolean(createErrors.tranceJson)}
              />
            </FormField>
          </div>
          <WizardActions
            message={createMessage}
            onSaveDraft={() => handleCreateAction("Draft saved for class creation.")}
            onPublish={() => handleCreateAction("Class creation draft queued for publish.")}
          />
        </WizardSection>

        <WizardSection
          title="Class Update"
          badge="Wizard Draft"
          description="Patch baselines, unlocks, and trance behavior for existing classes."
        >
          <div className="grid gap-4">
            <FormField
              label="Target class"
              htmlFor="class-target"
              error={updateTouched ? updateErrors.target : undefined}
            >
              <input
                id="class-target"
                className={inputClassName}
                value={updateForm.target}
                onChange={(event) => setUpdateForm({ ...updateForm, target: event.target.value })}
                placeholder="Search by class name"
              />
            </FormField>
            <div className="grid gap-4 md:grid-cols-2">
              <FormField
                label="Patch HP"
                htmlFor="class-patch-hp"
                error={updateTouched ? updateErrors.patchHp : undefined}
              >
                <input
                  id="class-patch-hp"
                  type="number"
                  className={inputClassName}
                  value={updateForm.patchHp}
                  onChange={(event) =>
                    setUpdateForm({ ...updateForm, patchHp: event.target.value })
                  }
                  placeholder="Optional"
                />
              </FormField>
              <FormField
                label="Patch MP"
                htmlFor="class-patch-mp"
                error={updateTouched ? updateErrors.patchMp : undefined}
              >
                <input
                  id="class-patch-mp"
                  type="number"
                  className={inputClassName}
                  value={updateForm.patchMp}
                  onChange={(event) =>
                    setUpdateForm({ ...updateForm, patchMp: event.target.value })
                  }
                  placeholder="Optional"
                />
              </FormField>
            </div>
            <FormField
              label="Unlock progression"
              hint="JSON"
              error={updateTouched ? updateErrors.unlocksJson : undefined}
            >
              <JsonEditor
                value={updateForm.unlocksJson}
                onChange={(value) => setUpdateForm({ ...updateForm, unlocksJson: value })}
                invalid={updateTouched && Boolean(updateErrors.unlocksJson)}
              />
            </FormField>
            <FormField
              label="Trance patch"
              hint="JSON"
              error={updateTouched ? updateErrors.tranceJson : undefined}
            >
              <JsonEditor
                value={updateForm.tranceJson}
                onChange={(value) => setUpdateForm({ ...updateForm, tranceJson: value })}
                invalid={updateTouched && Boolean(updateErrors.tranceJson)}
              />
            </FormField>
          </div>
          <WizardActions
            message={updateMessage}
            onSaveDraft={() => handleUpdateAction("Draft saved for class update.")}
            onPublish={() => handleUpdateAction("Class update draft queued for publish.")}
          />
        </WizardSection>
      </section>
    </div>
  );
}
