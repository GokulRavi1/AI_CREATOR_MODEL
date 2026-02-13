import { useModels } from '../../hooks/useModels';
import { Loader2 } from 'lucide-react';

export default function ModelSelector({ value, onChange, type = 'checkpoints', label = "Model" }) {
    const { models, loading } = useModels();

    const options = type === 'loras' ? models.loras : models.checkpoints;

    return (
        <div className="form-group">
            <label className="text-xs font-semibold text-[var(--text-secondary)] mb-1.5 block">{label}</label>
            <div className="relative">
                <select
                    className="input-select w-full"
                    value={value || ""}
                    onChange={(e) => onChange(e.target.value)}
                    disabled={loading}
                >
                    <option value="">Select {label}...</option>
                    {options.map((model) => (
                        <option key={model} value={model}>{model}</option>
                    ))}
                </select>
                {loading && (
                    <div className="absolute right-2 top-1/2 -translate-y-1/2 pointer-events-none">
                        <Loader2 size={14} className="animate-spin text-[var(--accent-primary)]" />
                    </div>
                )}
            </div>
        </div>
    );
}
