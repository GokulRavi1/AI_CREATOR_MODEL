import { useDiscovery } from '../../hooks/useDiscovery';
import ModelSelector from '../Shared/ModelSelector';
import { Loader2, Play, Settings2, CheckCircle2, Save } from 'lucide-react';
import { useState } from 'react';

export default function FaceDiscovery({ character }) {
    const {
        results,
        generate,
        loading,
        config,
        setConfig,
        selectedIndices,
        toggleSelection,
        saveIdentity
    } = useDiscovery(character);

    const [showAdvanced, setShowAdvanced] = useState(false);

    if (!character) return null;

    return (
        <div className="flex h-full gap-6">
            {/* Left Controls */}
            <div className="w-[320px] flex-shrink-0 flex flex-col gap-4 h-full overflow-y-auto pr-2">
                <div className="panel-section p-5 rounded-[var(--radius-lg)]">
                    <h4 className="section-title flex items-center gap-2 mb-4">
                        <Settings2 size={16} className="text-[var(--accent-primary)]" />
                        Discovery Settings
                    </h4>

                    <ModelSelector
                        value={config.checkpoint}
                        onChange={(val) => setConfig(prev => ({ ...prev, checkpoint: val }))}
                        label="SD Checkpoint"
                    />

                    <ModelSelector
                        value={config.character_lora}
                        onChange={(val) => setConfig(prev => ({ ...prev, character_lora: val }))}
                        type="loras"
                        label="Character LoRA"
                    />

                    <div className="form-group mt-4">
                        <label className="text-xs font-semibold text-[var(--text-secondary)] mb-1.5 block">Base Prompt</label>
                        <textarea
                            className="input-textarea w-full"
                            rows={5}
                            value={config.base_description}
                            onChange={(e) => setConfig(prev => ({ ...prev, base_description: e.target.value }))}
                            placeholder="Describe the character's base appearance..."
                        />
                    </div>

                    <div className="form-row mt-4 flex gap-3">
                        <div className="form-group flex-1">
                            <label className="text-xs font-semibold text-[var(--text-secondary)] mb-1.5 block">Batch Size</label>
                            <input
                                type="number" className="input-number w-full"
                                value={config.limit}
                                onChange={(e) => setConfig(prev => ({ ...prev, limit: Number(e.target.value) }))}
                                min={1} max={100}
                            />
                        </div>
                    </div>

                    <button
                        onClick={() => setShowAdvanced(!showAdvanced)}
                        className="text-xs text-[var(--accent-primary)] mt-3 hover:underline"
                    >
                        {showAdvanced ? "- Hide Advanced" : "+ Show Advanced"}
                    </button>

                    {showAdvanced && (
                        <div className="mt-3 p-3 bg-[var(--bg-tertiary)] rounded border border-[var(--border-color)] animate-in slide-in-from-top-2">
                            <div className="form-group mb-3">
                                <label className="text-xs text-[var(--text-secondary)] mb-1 block">Steps</label>
                                <input
                                    type="number" className="input-number w-full"
                                    value={config.steps}
                                    onChange={(e) => setConfig(prev => ({ ...prev, steps: Number(e.target.value) }))}
                                />
                            </div>
                            <div className="form-group">
                                <label className="text-xs text-[var(--text-secondary)] mb-1 block">CFG Scale</label>
                                <input
                                    type="number" className="input-number w-full"
                                    value={config.cfg_scale}
                                    step={0.5}
                                    onChange={(e) => setConfig(prev => ({ ...prev, cfg_scale: Number(e.target.value) }))}
                                />
                            </div>
                        </div>
                    )}

                    <button
                        onClick={generate}
                        className="btn btn-primary mt-6 w-full py-2.5"
                        disabled={loading}
                    >
                        {loading ? <Loader2 className="animate-spin" /> : <Play size={16} fill="currentColor" />}
                        {loading ? 'Processing...' : 'Start Discovery'}
                    </button>
                </div>
            </div>

            {/* Right Grid */}
            <div className="flex-1 flex flex-col h-full bg-[var(--bg-primary)]">
                <div className="flex justify-between items-center mb-4 min-h-[40px]">
                    <h3 className="section-title mb-0">Discovery Results</h3>
                    <div className="flex gap-3">
                        {results.length > 0 && (
                            <span className="text-xs text-[var(--text-muted)] mt-2">
                                Select the best images to define this identity.
                            </span>
                        )}
                        {selectedIndices.length > 0 && (
                            <button
                                onClick={saveIdentity}
                                className="btn btn-primary px-4 py-1.5 text-xs animate-in fade-in zoom-in"
                            >
                                <Save size={14} /> Save {selectedIndices.length} to Identity
                            </button>
                        )}
                    </div>
                </div>

                {results.length === 0 ? (
                    <div className="gallery-empty h-full panel-section bg-[var(--bg-tertiary)]/20 border-dashed border-2 border-[var(--border-color)] rounded-[var(--radius-lg)] flex flex-col items-center justify-center text-[var(--text-muted)] p-8">
                        <div className="text-4xl mb-4 opacity-50">🔍</div>
                        <p className="font-medium text-lg">No discovery images yet</p>
                        <p className="text-sm opacity-70 mt-1">Adjust settings and click "Start Discovery"</p>
                    </div>
                ) : (
                    <div className="discovery-grid grid grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4 overflow-y-auto pb-6">
                        {results.map((img, i) => {
                            const isSelected = selectedIndices.includes(i);
                            return (
                                <div
                                    key={i}
                                    className={`discovery-item group relative aspect-square rounded-lg overflow-hidden cursor-pointer border-2 transition-all ${isSelected ? 'border-[var(--accent-primary)] ring-2 ring-[var(--accent-primary)]/30' : 'border-transparent hover:border-[var(--border-color)]'}`}
                                    onClick={() => toggleSelection(i)}
                                >
                                    <img
                                        src={img.startsWith('/api') ? img : `/api/view?path=${encodeURIComponent(img)}`}
                                        alt={`Variation ${i + 1}`}
                                        className="w-full h-full object-cover"
                                        loading="lazy"
                                    />
                                    {isSelected && (
                                        <div className="absolute top-2 right-2 bg-[var(--accent-primary)] text-white rounded-full p-1 shadow-lg animate-in zoom-in duration-200">
                                            <CheckCircle2 size={16} />
                                        </div>
                                    )}
                                    <div className="absolute inset-0 bg-black/0 group-hover:bg-black/10 transition-colors" />
                                </div>
                            );
                        })}
                    </div>
                )}
            </div>
        </div>
    );
}
