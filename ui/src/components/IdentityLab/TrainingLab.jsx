import { useTraining } from '../../hooks/useTraining';
import { Loader2, CheckCircle2, FileText, Play, Save, Settings2, BookOpen } from 'lucide-react';
import { useState } from 'react';
import api from '../../api';
import { useApp } from '../../context/AppContext';

export default function TrainingLab({ character }) {
    const {
        loading,
        validation,
        preparation,
        config,
        setConfig,
        trainingStatus,
        validateDataset,
        prepareDataset,
        generateConfig,
        startTraining,
        stopTraining
    } = useTraining(character);

    const { addToast } = useApp();
    const [guide, setGuide] = useState(null);
    const [loadingGuide, setLoadingGuide] = useState(false);

    const fetchGuide = async () => {
        if (!character?.name) return;
        setLoadingGuide(true);
        try {
            const res = await api.get(`/dataset/guide/${character.name}`);
            setGuide(res.data);
            addToast('Photography guide loaded', 'success');
        } catch (err) {
            addToast('Could not load photo guide', 'error');
        } finally {
            setLoadingGuide(false);
        }
    };

    if (!character) return null;

    return (
        <div className="flex flex-col gap-6 h-full">
            <div className="flex gap-6 h-full">
                {/* ── Left: Dataset Tools ──────────────────────────────── */}
                <div className="w-1/3 flex flex-col gap-6">
                    <div className="panel-section p-5 rounded-[var(--radius-lg)] h-full">
                        <h4 className="section-title flex items-center gap-2 mb-4">
                            <FileText size={18} className="text-[var(--accent-primary)]" />
                            Dataset Preparation
                        </h4>

                        <p className="text-sm text-[var(--text-secondary)] mb-4">
                            Prepare your images for LoRA training. Ensure you have selected good images from Discovery.
                        </p>

                        <div className="flex flex-col gap-3">
                            <button
                                onClick={validateDataset}
                                disabled={loading}
                                className="btn btn-secondary w-full justify-between group"
                            >
                                <span>1. Validate Dataset</span>
                                {validation?.valid ? <CheckCircle2 size={16} className="text-green-500" /> : <Play size={14} className="opacity-50 group-hover:opacity-100" />}
                            </button>

                            {validation && !validation.valid && (
                                <div className="p-3 bg-red-500/10 border border-red-500/20 rounded text-xs text-red-200">
                                    <strong>Issues Found:</strong>
                                    <ul className="list-disc pl-4 mt-1 space-y-1">
                                        {validation.issues.slice(0, 3).map((issue, i) => (
                                            <li key={i}>{issue}</li>
                                        ))}
                                    </ul>
                                </div>
                            )}

                            {validation?.valid && (
                                <div className="p-3 bg-green-500/10 border border-green-500/20 rounded text-xs text-green-200 flex items-center gap-2">
                                    <CheckCircle2 size={14} />
                                    <span>Dataset ready! {validation.total_images} images found.</span>
                                </div>
                            )}

                            <div className="h-px bg-[var(--border-color)] my-2"></div>

                            <button
                                onClick={() => prepareDataset()}
                                disabled={loading}
                                className="btn btn-secondary w-full justify-between group"
                            >
                                <span>2. Resize & Caption</span>
                                <Play size={14} className="opacity-50 group-hover:opacity-100" />
                            </button>

                            <div className="h-px bg-[var(--border-color)] my-2"></div>

                            {/* Photo Guide Button */}
                            <button
                                onClick={fetchGuide}
                                disabled={loadingGuide}
                                className="btn btn-secondary w-full justify-between group"
                            >
                                <span className="flex items-center gap-1.5">
                                    <BookOpen size={14} />
                                    3. Photography Guide
                                </span>
                                {loadingGuide ? <Loader2 className="animate-spin" size={14} /> : <Play size={14} className="opacity-50 group-hover:opacity-100" />}
                            </button>

                            {guide && (
                                <div className="p-3 bg-[var(--bg-tertiary)] border border-[var(--border-color)] rounded text-xs text-[var(--text-primary)] max-h-48 overflow-y-auto">
                                    <h5 className="font-bold text-[var(--accent-primary)] mb-2">Photo Guide</h5>
                                    {typeof guide === 'object' ? (
                                        <pre className="whitespace-pre-wrap font-mono text-[11px]">{JSON.stringify(guide, null, 2)}</pre>
                                    ) : (
                                        <pre className="whitespace-pre-wrap font-mono text-[11px]">{guide}</pre>
                                    )}
                                </div>
                            )}
                        </div>
                    </div>
                </div>

                {/* ── Middle: Training Config ──────────────────────────── */}
                <div className="w-1/3 flex flex-col gap-6">
                    <div className="panel-section p-5 rounded-[var(--radius-lg)] h-full">
                        <h4 className="section-title flex items-center gap-2 mb-4">
                            <Settings2 size={18} className="text-[var(--accent-primary)]" />
                            Training Configuration
                        </h4>

                        <div className="flex flex-col gap-4">
                            <div className="form-group">
                                <label className="flex justify-between">
                                    <span>Trigger Word</span>
                                </label>
                                <input
                                    className="input-text w-full"
                                    value={config.trigger_word}
                                    onChange={(e) => setConfig({ ...config, trigger_word: e.target.value })}
                                />
                            </div>

                            <div className="form-row flex gap-4">
                                <div className="form-group flex-1">
                                    <label>Epochs</label>
                                    <input
                                        type="number" className="input-number w-full"
                                        value={config.epochs}
                                        onChange={(e) => setConfig({ ...config, epochs: parseInt(e.target.value) })}
                                    />
                                </div>
                                <div className="form-group flex-1">
                                    <label>Batch Size</label>
                                    <input
                                        type="number" className="input-number w-full"
                                        value={config.batch_size}
                                        onChange={(e) => setConfig({ ...config, batch_size: parseInt(e.target.value) })}
                                    />
                                </div>
                            </div>

                            <div className="form-row flex gap-4">
                                <div className="form-group flex-1">
                                    <label>Rank (Dim)</label>
                                    <input
                                        type="number" className="input-number w-full"
                                        value={config.network_rank}
                                        onChange={(e) => setConfig({ ...config, network_rank: parseInt(e.target.value) })}
                                    />
                                </div>
                                <div className="form-group flex-1">
                                    <label>Alpha</label>
                                    <input
                                        type="number" className="input-number w-full"
                                        value={config.network_alpha}
                                        onChange={(e) => setConfig({ ...config, network_alpha: parseInt(e.target.value) })}
                                    />
                                </div>
                            </div>

                            <div className="form-group">
                                <label className="flex justify-between">
                                    <span>GPU VRAM (GB)</span>
                                    <span className="text-[var(--accent-primary)] text-xs">{config.gpu_vram_gb}GB</span>
                                </label>
                                <input
                                    type="range"
                                    min="4" max="24" step="1"
                                    value={config.gpu_vram_gb}
                                    onChange={(e) => setConfig({ ...config, gpu_vram_gb: parseInt(e.target.value) })}
                                    className="w-full"
                                />
                            </div>

                            <label className="checkbox-label flex items-center gap-2 mt-2 p-2 rounded hover:bg-[var(--bg-tertiary)] cursor-pointer">
                                <input
                                    type="checkbox"
                                    checked={config.use_recommended}
                                    onChange={(e) => setConfig({ ...config, use_recommended: e.target.checked })}
                                />
                                <span className="text-sm">Auto-optimize settings (Recommended)</span>
                            </label>

                            <button
                                onClick={generateConfig}
                                disabled={loading}
                                className="btn btn-secondary mt-4 gap-2"
                            >
                                <Save size={16} /> Generate Config
                            </button>
                        </div>
                    </div>
                </div>

                {/* ── Right: Execution ─────────────────────────────────── */}
                <div className="w-1/3 flex flex-col gap-6">
                    <div className="panel-section p-5 rounded-[var(--radius-lg)] h-full flex flex-col">
                        <h4 className="section-title flex items-center gap-2 mb-4">
                            <Play size={18} className="text-[var(--accent-primary)]" />
                            Start Training
                        </h4>

                        <div className="flex-1 flex flex-col justify-center items-center gap-6 p-6 border-2 border-dashed border-[var(--border-color)] rounded-[var(--radius-md)] bg-[var(--bg-tertiary)] overflow-hidden">
                            {trainingStatus === 'running' ? (
                                <div className="text-center animate-pulse">
                                    <Loader2 size={48} className="animate-spin text-[var(--accent-primary)] mx-auto mb-4" />
                                    <h3 className="text-lg font-semibold text-white">Training in Progress...</h3>
                                    <p className="text-sm text-[var(--text-secondary)]">Please check the console for detailed logs.</p>
                                    <button
                                        onClick={stopTraining}
                                        className="btn btn-ghost border border-red-500/50 text-red-400 mt-4 px-4 py-1.5 text-xs hover:bg-red-500/10"
                                    >
                                        Stop Training
                                    </button>
                                </div>
                            ) : trainingStatus === 'manual_action_required' && trainingOutput ? (
                                <div className="text-left w-full h-full overflow-y-auto">
                                    <div className="flex items-center gap-2 mb-4 text-amber-400">
                                        <div className="p-2 rounded-full bg-amber-400/10">
                                            <BookOpen size={20} />
                                        </div>
                                        <h3 className="font-semibold">Manual Action Required</h3>
                                    </div>

                                    <p className="text-sm text-[var(--text-secondary)] mb-4">
                                        {trainingOutput.instructions}
                                    </p>

                                    <div className="bg-black/30 rounded p-3 mb-4 font-mono text-xs overflow-x-auto border border-[var(--border-color)]">
                                        <div className="text-[var(--text-tertiary)] mb-1"># Configuration saved to:</div>
                                        <div className="text-green-400 mb-4">{trainingOutput.config_path}</div>

                                        <div className="text-[var(--text-tertiary)] mb-1"># Run this command:</div>
                                        <div className="text-blue-300 break-all select-all">{trainingOutput.command}</div>
                                    </div>

                                    <button
                                        onClick={() => {
                                            navigator.clipboard.writeText(trainingOutput.command);
                                            addToast('Command copied to clipboard', 'success');
                                        }}
                                        className="btn btn-primary w-full py-2"
                                    >
                                        Copy Command
                                    </button>
                                </div>
                            ) : (
                                <div className="text-center">
                                    <div className="w-16 h-16 rounded-full bg-[var(--bg-primary)] flex items-center justify-center mx-auto mb-4 shadow-inner">
                                        <Play size={32} className="text-[var(--accent-primary)] ml-1" />
                                    </div>
                                    <h3 className="text-lg font-semibold text-[var(--text-primary)]">Ready to Train</h3>
                                    <p className="text-sm text-[var(--text-secondary)] mt-2 mb-6">
                                        This process will generate a command for Kohya SS.
                                    </p>
                                    <button
                                        onClick={startTraining}
                                        disabled={loading || trainingStatus === 'running'}
                                        className="btn btn-primary w-full py-3 shadow-[0_0_20px_rgba(124,58,237,0.3)] hover:shadow-[0_0_30px_rgba(124,58,237,0.5)] transition-all"
                                    >
                                        Generate Training Command
                                    </button>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
