export function WizardActions({
  onSaveDraft,
  onPublish,
  message
}: {
  onSaveDraft: () => void;
  onPublish: () => void;
  message?: string;
}) {
  return (
    <div className="border-t border-white/10 pt-4 flex flex-wrap items-center justify-between gap-4">
      {message ? <p className="text-xs text-slate-300">{message}</p> : <span />}
      <div className="flex items-center gap-3">
        <button
          type="button"
          className="px-4 py-2 rounded-full border border-white/10 bg-white/5 text-sm text-white"
          onClick={onSaveDraft}
        >
          Save draft
        </button>
        <button
          type="button"
          className="px-4 py-2 rounded-full bg-aurora-violet/80 text-sm text-white shadow-glow"
          onClick={onPublish}
        >
          Publish
        </button>
      </div>
    </div>
  );
}
