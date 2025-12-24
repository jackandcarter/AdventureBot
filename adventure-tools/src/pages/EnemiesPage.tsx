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

type EnemyCreateForm = {
  name: string;
  role: string;
  difficulty: string;
  description: string;
  hp: string;
  mp: string;
  attack: string;
  abilitiesJson: string;
  resistancesJson: string;
  dropsJson: string;
};

type EnemyUpdateForm = {
  target: string;
  patchHp: string;
  patchAttack: string;
  behaviorJson: string;
  rewardsJson: string;
};

const initialCreateForm: EnemyCreateForm = {
  name: "",
  role: "",
  difficulty: "",
  description: "",
  hp: "",
  mp: "",
  attack: "",
  abilitiesJson: "{\n  \"rotation\": []\n}",
  resistancesJson: "{\n  \"fire\": \"weak\",\n  \"ice\": \"neutral\"\n}",
  dropsJson: "{\n  \"loot\": []\n}"
};

const initialUpdateForm: EnemyUpdateForm = {
  target: "",
  patchHp: "",
  patchAttack: "",
  behaviorJson: "{\n  \"rotation\": []\n}",
  rewardsJson: "{\n  \"gil\": 0,\n  \"xp\": 0\n}"
};

export function EnemiesPage() {
  const [createForm, setCreateForm] = useState(initialCreateForm);
  const [updateForm, setUpdateForm] = useState(initialUpdateForm);
  const [createTouched, setCreateTouched] = useState(false);
  const [updateTouched, setUpdateTouched] = useState(false);
  const [createMessage, setCreateMessage] = useState("");
  const [updateMessage, setUpdateMessage] = useState("");

  const createErrors = {
    name: createForm.name.trim() ? "" : "Enemy name is required.",
    role: createForm.role ? "" : "Select a role.",
    difficulty: createForm.difficulty ? "" : "Select a difficulty tier.",
    description: createForm.description.trim() ? "" : "Provide a short description.",
    hp:
      createForm.hp && Number(createForm.hp) > 0
        ? ""
        : "Enter a positive HP value.",
    mp:
      createForm.mp && Number(createForm.mp) >= 0
        ? ""
        : "Enter a non-negative MP value.",
    attack:
      createForm.attack && Number(createForm.attack) > 0
        ? ""
        : "Enter a positive attack value.",
    abilitiesJson: isValidJson(createForm.abilitiesJson),
    resistancesJson: isValidJson(createForm.resistancesJson),
    dropsJson: isValidJson(createForm.dropsJson)
  };

  const updateErrors = {
    target: updateForm.target.trim() ? "" : "Choose an enemy to update.",
    patchHp:
      !updateForm.patchHp || Number(updateForm.patchHp) > 0
        ? ""
        : "Enter a positive HP value.",
    patchAttack:
      !updateForm.patchAttack || Number(updateForm.patchAttack) > 0
        ? ""
        : "Enter a positive attack value.",
    behaviorJson: isValidJson(updateForm.behaviorJson),
    rewardsJson: isValidJson(updateForm.rewardsJson)
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
            <h2 className="text-3xl font-display">Enemy Authoring</h2>
            <p className="mt-2 text-sm text-slate-300 max-w-2xl">
              Create and revise enemy content with the wizard flows below.
            </p>
          </div>
          <div className="text-right text-xs text-slate-400">
            <p>Database</p>
            <p className="text-aurora-cyan">adventure.enemies</p>
          </div>
        </div>
      </section>

      <section className="grid lg:grid-cols-2 gap-6">
        <WizardSection
          title="Enemy Creation"
          badge="Wizard Draft"
          description="Capture the base identity, stats, and behavior blueprint for new enemies."
        >
          <div className="grid gap-4">
            <FormField
              label="Enemy name"
              htmlFor="enemy-name"
              error={createTouched ? createErrors.name : undefined}
            >
              <input
                id="enemy-name"
                className={inputClassName}
                value={createForm.name}
                onChange={(event) => setCreateForm({ ...createForm, name: event.target.value })}
                placeholder="Clockwork Basilisk"
              />
            </FormField>
            <div className="grid gap-4 md:grid-cols-2">
              <FormField
                label="Role"
                htmlFor="enemy-role"
                error={createTouched ? createErrors.role : undefined}
              >
                <select
                  id="enemy-role"
                  className={inputClassName}
                  value={createForm.role}
                  onChange={(event) => setCreateForm({ ...createForm, role: event.target.value })}
                >
                  <option value="">Select a role</option>
                  <option value="bruiser">Bruiser</option>
                  <option value="mage">Mage</option>
                  <option value="support">Support</option>
                  <option value="assassin">Assassin</option>
                </select>
              </FormField>
              <FormField
                label="Difficulty tier"
                htmlFor="enemy-difficulty"
                error={createTouched ? createErrors.difficulty : undefined}
              >
                <select
                  id="enemy-difficulty"
                  className={inputClassName}
                  value={createForm.difficulty}
                  onChange={(event) =>
                    setCreateForm({ ...createForm, difficulty: event.target.value })
                  }
                >
                  <option value="">Select tier</option>
                  <option value="common">Common</option>
                  <option value="elite">Elite</option>
                  <option value="boss">Boss</option>
                </select>
              </FormField>
            </div>
            <FormField
              label="Narrative description"
              htmlFor="enemy-description"
              error={createTouched ? createErrors.description : undefined}
            >
              <textarea
                id="enemy-description"
                className={textareaClassName}
                value={createForm.description}
                onChange={(event) =>
                  setCreateForm({ ...createForm, description: event.target.value })
                }
                placeholder="Short lore hook used in the codex."
              />
            </FormField>
            <div className="grid gap-4 md:grid-cols-3">
              <FormField
                label="Base HP"
                htmlFor="enemy-hp"
                error={createTouched ? createErrors.hp : undefined}
              >
                <input
                  id="enemy-hp"
                  type="number"
                  className={inputClassName}
                  value={createForm.hp}
                  onChange={(event) => setCreateForm({ ...createForm, hp: event.target.value })}
                />
              </FormField>
              <FormField
                label="Base MP"
                htmlFor="enemy-mp"
                error={createTouched ? createErrors.mp : undefined}
              >
                <input
                  id="enemy-mp"
                  type="number"
                  className={inputClassName}
                  value={createForm.mp}
                  onChange={(event) => setCreateForm({ ...createForm, mp: event.target.value })}
                />
              </FormField>
              <FormField
                label="Attack"
                htmlFor="enemy-attack"
                error={createTouched ? createErrors.attack : undefined}
              >
                <input
                  id="enemy-attack"
                  type="number"
                  className={inputClassName}
                  value={createForm.attack}
                  onChange={(event) =>
                    setCreateForm({ ...createForm, attack: event.target.value })
                  }
                />
              </FormField>
            </div>
            <FormField
              label="Ability rotation"
              hint="JSON"
              error={createTouched ? createErrors.abilitiesJson : undefined}
            >
              <JsonEditor
                value={createForm.abilitiesJson}
                onChange={(value) => setCreateForm({ ...createForm, abilitiesJson: value })}
                invalid={createTouched && Boolean(createErrors.abilitiesJson)}
              />
            </FormField>
            <FormField
              label="Resistances map"
              hint="JSON"
              error={createTouched ? createErrors.resistancesJson : undefined}
            >
              <JsonEditor
                value={createForm.resistancesJson}
                onChange={(value) => setCreateForm({ ...createForm, resistancesJson: value })}
                invalid={createTouched && Boolean(createErrors.resistancesJson)}
              />
            </FormField>
            <FormField
              label="Drop table"
              hint="JSON"
              error={createTouched ? createErrors.dropsJson : undefined}
            >
              <JsonEditor
                value={createForm.dropsJson}
                onChange={(value) => setCreateForm({ ...createForm, dropsJson: value })}
                invalid={createTouched && Boolean(createErrors.dropsJson)}
              />
            </FormField>
          </div>
          <WizardActions
            message={createMessage}
            onSaveDraft={() => handleCreateAction("Draft saved for enemy creation.")}
            onPublish={() => handleCreateAction("Enemy creation draft queued for publish.")}
          />
        </WizardSection>

        <WizardSection
          title="Enemy Update"
          badge="Wizard Draft"
          description="Locate an existing enemy and patch stats, behaviors, and rewards."
        >
          <div className="grid gap-4">
            <FormField
              label="Target enemy"
              htmlFor="enemy-target"
              error={updateTouched ? updateErrors.target : undefined}
            >
              <input
                id="enemy-target"
                className={inputClassName}
                value={updateForm.target}
                onChange={(event) => setUpdateForm({ ...updateForm, target: event.target.value })}
                placeholder="Search by name or ID"
              />
            </FormField>
            <div className="grid gap-4 md:grid-cols-2">
              <FormField
                label="Patch HP"
                htmlFor="enemy-patch-hp"
                error={updateTouched ? updateErrors.patchHp : undefined}
              >
                <input
                  id="enemy-patch-hp"
                  type="number"
                  className={inputClassName}
                  value={updateForm.patchHp}
                  onChange={(event) =>
                    setUpdateForm({ ...updateForm, patchHp: event.target.value })
                  }
                  placeholder="Leave empty to keep current"
                />
              </FormField>
              <FormField
                label="Patch Attack"
                htmlFor="enemy-patch-attack"
                error={updateTouched ? updateErrors.patchAttack : undefined}
              >
                <input
                  id="enemy-patch-attack"
                  type="number"
                  className={inputClassName}
                  value={updateForm.patchAttack}
                  onChange={(event) =>
                    setUpdateForm({ ...updateForm, patchAttack: event.target.value })
                  }
                  placeholder="Leave empty to keep current"
                />
              </FormField>
            </div>
            <FormField
              label="Behavior overrides"
              hint="JSON"
              error={updateTouched ? updateErrors.behaviorJson : undefined}
            >
              <JsonEditor
                value={updateForm.behaviorJson}
                onChange={(value) => setUpdateForm({ ...updateForm, behaviorJson: value })}
                invalid={updateTouched && Boolean(updateErrors.behaviorJson)}
              />
            </FormField>
            <FormField
              label="Rewards delta"
              hint="JSON"
              error={updateTouched ? updateErrors.rewardsJson : undefined}
            >
              <JsonEditor
                value={updateForm.rewardsJson}
                onChange={(value) => setUpdateForm({ ...updateForm, rewardsJson: value })}
                invalid={updateTouched && Boolean(updateErrors.rewardsJson)}
              />
            </FormField>
          </div>
          <WizardActions
            message={updateMessage}
            onSaveDraft={() => handleUpdateAction("Draft saved for enemy update.")}
            onPublish={() => handleUpdateAction("Enemy update draft queued for publish.")}
          />
        </WizardSection>
      </section>
    </div>
  );
}
