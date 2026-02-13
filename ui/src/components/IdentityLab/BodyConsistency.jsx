import { useBodyConsistency } from '../../hooks/useBodyConsistency';
import { usePresets } from '../../hooks/usePresets';
import ModelSelector from '../Shared/ModelSelector';
import { Upload, X, Loader2, Play, Settings2, CheckCircle2, Save } from 'lucide-react';
import React, { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';

export default function BodyConsistency({ character }) {
    const {
        results,
        generate,
        loading,
        controlImageFile,
        uploadControlImage,
        removeControlImage,
        config,
        setConfig,
        selectedIndices,
        toggleSelection,
        saveToDataset
    } = useBodyConsistency(character);

    const { outfits } = usePresets();
    const [showAdvanced, setShowAdvanced] = useState(false);
    const [selectedOutfits, setSelectedOutfits] = useState([]);

    const toggleOutfit = (outfit) => {
        setSelectedOutfits(prev => {
            const next = prev.includes(outfit) ? prev.filter(o => o !== outfit) : [...prev, outfit];
            // Append selected outfits to the base description
            const base = config.base_description.split('\n')[0]; // Keep first line only
            const outfitStr = next.length > 0 ? `\nOutfits: ${next.join(', ')}` : '';
            setConfig(prev => ({ ...prev, base_description: base + outfitStr }));
            return next;
        });
    };

    // Dropzone logic
    const onDrop = useCallback(acceptedFiles => {
        if (acceptedFiles?.length > 0) {
            uploadControlImage(acceptedFiles[0]);
        }
    }, [uploadControlImage]);

    const { getRootProps, getInputProps, isDragActive } = useDropzone({
        onDrop,
        accept: { 'image/*': [] },
        multiple: false
    });

    if (!character) return null;

    return (
        <div className="flex h-full gap-6">
            {/* Left Controls */}
            <div className="w-[320px] flex-shrink-0 flex flex-col gap-4 h-full overflow-y-auto pr-2">
                <div className="panel-section p-5 rounded-[var(--radius-lg)]">
                    <h4 className="section-title flex items-center gap-2 mb-4">
                        <Settings2 size={16} className="text-[var(--accent-primary)]" />
                        Consistency Settings
                    </h4>

                    <ModelSelector
                        value={config.checkpoint}
                        onChange={(val) => setConfig(prev => ({ ...prev, checkpoint: val }))}
                        label="SD Checkpoint"
                    />

                    {/* Control Image Upload */}
                    <div className="form-group mt-4">
                        <label className="text-xs font-semibold text-[var(--text-secondary)] mb-1.5 block">Reference Pose</label>

                        {!controlImageFile ? (
                            <div {...getRootProps()} className={`border-2 border-dashed rounded-[var(--radius-md)] p-6 text-center cursor-pointer transition-colors ${isDragActive ? 'border-[var(--accent-primary)] bg-[var(--accent-primary)]/10' : 'border-[var(--border-color)] hover:border-[var(--text-secondary)]'}`}>
                                <input {...getInputProps()} />
                                <Upload size={24} className="mx-auto mb-2 text-[var(--text-muted)]" />
                                <p className="text-xs text-[var(--text-muted)]">Drop pose image here</p>
                            </div>
                        ) : (
                            <div className="relative rounded-[var(--radius-md)] overflow-hidden border border-[var(--border-color)] group">
                                <img src={controlImageFile} alt="Control" className="w-full h-48 object-cover opacity-80" />
                                <button
                                    onClick={(e) => { e.stopPropagation(); removeControlImage(); }}
                                    className="absolute top-2 right-2 bg-black/50 hover:bg-red-500 text-white p-1 rounded-full transition-colors"
                                >
                                    <X size={14} />
                                </button>
                                <div className="absolute bottom-0 inset-x-0 bg-black/60 p-2 text-xs text-white text-center">
                                    Using as reference
                                </div>
                            </div>
                        )}
                    </div>

                    <div className="form-group mt-4">
                        <label className="text-xs font-semibold text-[var(--text-secondary)] mb-1.5 block">Pose Description</label>
                        <textarea
                            className="input-textarea w-full"
                            rows={3}
                            value={config.base_description}
                            onChange={(e) => setConfig(prev => ({ ...prev, base_description: e.target.value }))}
                            placeholder="e.g. Standing, arms crossed, suit"
                        />
                    </div>

                    {/* Outfit Selector Pills */}
                    {outfits.length > 0 && (
                        <div className="mt-4">
                            <label className="text-xs font-semibold text-[var(--text-secondary)] mb-2 block">Outfit Variations</label>
                            <div className="flex flex-wrap gap-1.5">
                                {outfits.map(outfit => (
                                    <button
                                        key={outfit}
                                        onClick={() => toggleOutfit(outfit)}
                                        className={`text-[11px] px-2.5 py-1 rounded-full border transition-all ${selectedOutfits.includes(outfit)
                                            ? 'bg-[var(--accent-primary)]/15 border-[var(--accent-primary)] text-[var(--accent-primary)] font-medium'
                                            : 'bg-[var(--bg-tertiary)]/50 border-[var(--border-color)] text-[var(--text-muted)] hover:border-[var(--border-hover)]'
                                            }`}
                                    >
                                        {outfit}
                                    </button>
                                ))}
                            </div>
                        </div>
                    )}

                    <div className="form-row mt-4 flex gap-3">
                        <div className="form-group flex-1">
                            <label className="text-xs font-semibold text-[var(--text-secondary)] mb-1.5 block">Width</label>
                            <input
                                type="number" className="input-number w-full"
                                value={config.width}
                                onChange={(e) => setConfig(prev => ({ ...prev, width: Number(e.target.value) }))}
                                step={64}
                            />
                        </div>
                        <div className="form-group flex-1">
                            <label className="text-xs font-semibold text-[var(--text-secondary)] mb-1.5 block">Height</label>
                            <input
                                type="number" className="input-number w-full"
                                value={config.height}
                                onChange={(e) => setConfig(prev => ({ ...prev, height: Number(e.target.value) }))}
                                step={64}
                            />
                        </div>
                    </div>

                    <div className="form-row mt-3 flex gap-3">
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
                            <div className="form-group mb-3">
                                <label className="text-xs text-[var(--text-secondary)] mb-1 block">CFG Scale</label>
                                <input
                                    type="number" className="input-number w-full"
                                    value={config.cfg_scale}
                                    step={0.5}
                                    onChange={(e) => setConfig(prev => ({ ...prev, cfg_scale: Number(e.target.value) }))}
                                />
                            </div>
                            <div className="form-group">
                                <label className="text-xs text-[var(--text-secondary)] mb-1 block">LoRA Strength</label>
                                <input
                                    type="number" className="input-number w-full"
                                    value={config.lora_strength}
                                    step={0.1}
                                    onChange={(e) => setConfig(prev => ({ ...prev, lora_strength: Number(e.target.value) }))}
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
                        {loading ? 'Processing...' : 'Generate Poses'}
                    </button>
                </div>
            </div>

            {/* Right Grid */}
            <div className="flex-1 flex flex-col h-full bg-[var(--bg-primary)]">
                <div className="flex justify-between items-center mb-4 min-h-[40px]">
                    <h3 className="section-title mb-0">Generated Bodies</h3>
                    <div className="flex gap-3">
                        {selectedIndices.length > 0 && (
                            <button
                                onClick={saveToDataset}
                                className="btn btn-primary px-4 py-1.5 text-xs animate-in fade-in zoom-in"
                            >
                                <Save size={14} /> Add {selectedIndices.length} to Dataset
                            </button>
                        )}
                    </div>
                </div>

                {results.length === 0 ? (
                    <div className="gallery-empty h-full panel-section bg-[var(--bg-tertiary)]/20 border-dashed border-2 border-[var(--border-color)] rounded-[var(--radius-lg)] flex flex-col items-center justify-center text-[var(--text-muted)] p-8">
                        <div className="text-4xl mb-4 opacity-50">🔍</div>
                        <p className="font-medium text-lg">No consistency images yet</p>
                        <p className="text-sm opacity-70 mt-1">Adjust settings and click "Generate Poses"</p>
                    </div>
                ) : (
                    <div className="discovery-grid grid grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4 overflow-y-auto pb-6">
                        {results.map((img, i) => {
                            const isSelected = selectedIndices.includes(i);
                            return (
                                <div
                                    key={i}
                                    className={`discovery-item group relative aspect-[2/3] rounded-lg overflow-hidden cursor-pointer border-2 transition-all ${isSelected ? 'border-[var(--accent-primary)] ring-2 ring-[var(--accent-primary)]/30' : 'border-transparent hover:border-[var(--border-color)]'}`}
                                    onClick={() => toggleSelection(i)}
                                >
                                    <img
                                        src={img.startsWith('/api') ? img : `/api/view?path=${encodeURIComponent(img)}`}
                                        alt={`Pose ${i + 1}`}
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
