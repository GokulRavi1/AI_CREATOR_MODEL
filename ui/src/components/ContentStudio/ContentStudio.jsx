import { useStudio } from '../../hooks/useStudio';
import { usePresets } from '../../hooks/usePresets';
import ModelSelector from '../Shared/ModelSelector';
import { Loader2, Play, Settings2, Image as ImageIcon, Upload, X, Wand2, Film, UserCircle, Eye, RectangleHorizontal, RectangleVertical, Square } from 'lucide-react';
import React, { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { useApp } from '../../context/AppContext';
import api from '../../api';

const ASPECT_RATIOS = [
    { label: '9:16', icon: RectangleVertical, w: 576, h: 1024 },
    { label: '2:3', icon: RectangleVertical, w: 683, h: 1024 },
    { label: '1:1', icon: Square, w: 1024, h: 1024 },
    { label: '16:9', icon: RectangleHorizontal, w: 1024, h: 576 },
];

export default function ContentStudio() {
    const {
        config,
        updateConfig,
        generate,
        loading,
        results,
        controlImageFile,
        uploadControlImage,
        removeControlImage
    } = useStudio();

    const { cameraStyles, lightingStyles } = usePresets();
    const { addToast } = useApp();
    const [showAdvanced, setShowAdvanced] = useState(false);
    const [promptPreview, setPromptPreview] = useState(null);
    const [generatingVideo, setGeneratingVideo] = useState(false);
    const [generatingAvatar, setGeneratingAvatar] = useState(false);

    // Dropzone logic for ControlNet
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

    const activeRatio = ASPECT_RATIOS.find(r => r.w === config.width && r.h === config.height);

    const handlePreviewPrompt = async () => {
        try {
            const res = await api.post('/prompt/build', {
                prompt: config.prompt,
                negative_prompt: config.negative_prompt,
                camera_style: config.camera_style,
                lighting_style: config.lighting_style,
            });
            setPromptPreview(res.data);
        } catch (err) {
            addToast('Could not build prompt preview', 'error');
        }
    };

    const handleGenerateVideo = async () => {
        setGeneratingVideo(true);
        addToast('Starting video generation...', 'info');
        try {
            const res = await api.post('/generate/video', {
                prompt: config.prompt,
                negative_prompt: config.negative_prompt,
                width: config.width,
                height: config.height,
                lora_name: config.lora_name,
                lora_strength: config.lora_strength,
            });
            if (res.data.success) addToast('Video generated!', 'success');
            else addToast('Video generation returned no result', 'warning');
        } catch (err) {
            addToast(err.response?.data?.detail || 'Video generation failed', 'error');
        } finally {
            setGeneratingVideo(false);
        }
    };

    const handleGenerateAvatar = async () => {
        setGeneratingAvatar(true);
        addToast('Starting avatar generation...', 'info');
        try {
            const res = await api.post('/generate/avatar', {
                prompt: config.prompt,
                lora_name: config.lora_name,
            });
            if (res.data.success) addToast('Avatar generated!', 'success');
            else addToast('Avatar generation returned no result', 'warning');
        } catch (err) {
            addToast(err.response?.data?.detail || 'Avatar generation failed', 'error');
        } finally {
            setGeneratingAvatar(false);
        }
    };

    return (
        <div className="flex h-full gap-6 p-6 relative overflow-hidden bg-[var(--bg-primary)]">
            {/* Background Ambient Glow */}
            <div className="absolute top-0 left-0 right-0 h-96 bg-gradient-to-br from-[var(--bg-primary)] via-[rgba(124,58,237,0.05)] to-transparent pointer-events-none" />

            {/* Left Controls */}
            <div className="w-[370px] flex-shrink-0 flex flex-col gap-4 h-full overflow-y-auto pr-2 z-10">
                <div className="panel-section bg-[var(--bg-secondary)]/80 p-5 rounded-[var(--radius-lg)] border border-[var(--border-color)]">
                    <h4 className="section-title flex items-center gap-2 mb-4">
                        <div className="p-1.5 bg-[var(--accent-primary)]/10 rounded text-[var(--accent-primary)]">
                            <Wand2 size={16} />
                        </div>
                        Studio Settings
                    </h4>

                    <ModelSelector
                        value={config.checkpoint}
                        onChange={(val) => updateConfig('checkpoint', val)}
                        label="SD Checkpoint"
                    />

                    <div className="form-group mt-5">
                        <label>Prompt</label>
                        <textarea
                            className="input-textarea w-full h-32 text-sm leading-relaxed"
                            value={config.prompt}
                            onChange={(e) => updateConfig('prompt', e.target.value)}
                            placeholder="Describe your scene..."
                        />
                    </div>

                    <div className="form-group mt-3">
                        <label>Negative Prompt</label>
                        <textarea
                            className="input-textarea w-full text-xs text-[var(--text-muted)]"
                            rows={2}
                            value={config.negative_prompt}
                            onChange={(e) => updateConfig('negative_prompt', e.target.value)}
                            placeholder="What to avoid..."
                        />
                    </div>

                    {/* Aspect Ratio Selector */}
                    <div className="mt-4">
                        <label className="text-xs font-semibold text-[var(--text-secondary)] mb-2 block">Aspect Ratio</label>
                        <div className="grid grid-cols-4 gap-2">
                            {ASPECT_RATIOS.map(r => {
                                const Icon = r.icon;
                                const isActive = activeRatio?.label === r.label;
                                return (
                                    <button
                                        key={r.label}
                                        onClick={() => { updateConfig('width', r.w); updateConfig('height', r.h); }}
                                        className={`flex flex-col items-center gap-1 py-2 rounded-[var(--radius-md)] border text-xs font-medium transition-all ${isActive
                                                ? 'bg-[var(--accent-primary)]/15 border-[var(--accent-primary)] text-[var(--accent-primary)]'
                                                : 'bg-[var(--bg-tertiary)]/50 border-[var(--border-color)] text-[var(--text-muted)] hover:border-[var(--border-hover)] hover:text-[var(--text-primary)]'
                                            }`}
                                    >
                                        <Icon size={16} />
                                        {r.label}
                                    </button>
                                );
                            })}
                        </div>
                    </div>

                    {/* Camera & Lighting Styles */}
                    {(cameraStyles.length > 0 || lightingStyles.length > 0) && (
                        <div className="mt-4 grid grid-cols-2 gap-3">
                            {cameraStyles.length > 0 && (
                                <div className="form-group">
                                    <label>Camera Style</label>
                                    <select
                                        className="input-select w-full"
                                        value={config.camera_style || ''}
                                        onChange={(e) => updateConfig('camera_style', e.target.value)}
                                    >
                                        <option value="">Default</option>
                                        {cameraStyles.map(s => <option key={s} value={s}>{s}</option>)}
                                    </select>
                                </div>
                            )}
                            {lightingStyles.length > 0 && (
                                <div className="form-group">
                                    <label>Lighting</label>
                                    <select
                                        className="input-select w-full"
                                        value={config.lighting_style || ''}
                                        onChange={(e) => updateConfig('lighting_style', e.target.value)}
                                    >
                                        <option value="">Default</option>
                                        {lightingStyles.map(s => <option key={s} value={s}>{s}</option>)}
                                    </select>
                                </div>
                            )}
                        </div>
                    )}

                    {/* LoRA Selection */}
                    <div className="mt-4 p-4 bg-[var(--bg-tertiary)]/50 rounded-[var(--radius-md)] border border-[var(--border-color)]">
                        <ModelSelector
                            value={config.lora_name || ""}
                            onChange={(val) => updateConfig('lora_name', val)}
                            type="loras"
                            label="Add LoRA (Optional)"
                        />
                        {config.lora_name && (
                            <div className="form-group mt-3">
                                <label className="flex justify-between">
                                    <span>Strength</span>
                                    <span className="text-[var(--accent-primary)]">{config.lora_strength}</span>
                                </label>
                                <input
                                    type="range"
                                    min="0.1" max="1.5" step="0.1"
                                    value={config.lora_strength}
                                    onChange={(e) => updateConfig('lora_strength', Number(e.target.value))}
                                    className="w-full"
                                />
                            </div>
                        )}
                    </div>

                    {/* ControlNet Toggle */}
                    <div className="mt-6 border-t border-[var(--border-color)] pt-4">
                        <label className="checkbox-label flex items-center justify-between cursor-pointer mb-2">
                            <span className="text-sm font-semibold text-[var(--text-primary)]">Enable ControlNet</span>
                            <div className="relative inline-block w-10 h-5 align-middle select-none transition duration-200 ease-in">
                                <input
                                    type="checkbox"
                                    checked={config.controlnet_enabled}
                                    onChange={(e) => updateConfig('controlnet_enabled', e.target.checked)}
                                    className="toggle-checkbox absolute block w-5 h-5 rounded-full bg-white border-4 appearance-none cursor-pointer checked:right-0 right-5"
                                />
                                <label className={`toggle-label block overflow-hidden h-5 rounded-full cursor-pointer ${config.controlnet_enabled ? 'bg-[var(--accent-primary)]' : 'bg-[var(--bg-tertiary)]'}`}></label>
                            </div>
                        </label>

                        {config.controlnet_enabled && (
                            <div className="animate-in slide-in-from-top-2">
                                {!controlImageFile ? (
                                    <div {...getRootProps()} className={`mt-2 border-2 border-dashed rounded-[var(--radius-md)] p-6 text-center cursor-pointer transition-colors ${isDragActive ? 'border-[var(--accent-primary)] bg-[var(--accent-primary)]/10' : 'border-[var(--border-color)] hover:border-[var(--text-secondary)]'}`}>
                                        <input {...getInputProps()} />
                                        <Upload size={24} className="mx-auto mb-2 text-[var(--accent-primary)]" />
                                        <p className="text-xs text-[var(--text-primary)] font-medium">Click to upload reference</p>
                                        <p className="text-[10px] text-[var(--text-muted)] mt-1">Supports JPG, PNG</p>
                                    </div>
                                ) : (
                                    <div className="mt-2 relative rounded-[var(--radius-md)] overflow-hidden border border-[var(--border-color)] group shadow-lg">
                                        <img src={controlImageFile} alt="Control" className="w-full h-40 object-cover opacity-80 group-hover:opacity-100 transition-opacity" />
                                        <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent pointer-events-none" />
                                        <button
                                            onClick={(e) => { e.stopPropagation(); removeControlImage(); }}
                                            className="absolute top-2 right-2 bg-black/50 hover:bg-red-500 text-white p-1.5 rounded-full backdrop-blur-sm transition-colors cursor-pointer"
                                        >
                                            <X size={14} />
                                        </button>
                                        <span className="absolute bottom-2 left-2 text-[10px] font-medium text-white px-2 py-0.5 bg-black/40 rounded-full backdrop-blur-sm">Reference Image</span>
                                    </div>
                                )}
                            </div>
                        )}
                    </div>

                    {/* Advanced Settings */}
                    <button
                        onClick={() => setShowAdvanced(!showAdvanced)}
                        className="text-xs text-[var(--text-secondary)] mt-4 hover:text-[var(--accent-primary)] flex items-center gap-1 transition-colors"
                    >
                        <Settings2 size={12} /> {showAdvanced ? "Hide Advanced Settings" : "Show Advanced Settings"}
                    </button>

                    {showAdvanced && (
                        <div className="mt-3 p-4 bg-[var(--bg-tertiary)]/50 rounded-[var(--radius-md)] border border-[var(--border-color)] animate-in slide-in-from-top-2 space-y-3">
                            <div className="form-group">
                                <label>Seed</label>
                                <input
                                    type="number" className="input-number w-full"
                                    value={config.seed}
                                    onChange={(e) => updateConfig('seed', parseInt(e.target.value))}
                                    placeholder="-1 for random"
                                />
                            </div>
                            <div className="grid grid-cols-2 gap-3">
                                <div className="form-group">
                                    <label>Steps</label>
                                    <input
                                        type="number" className="input-number w-full"
                                        value={config.steps}
                                        onChange={(e) => updateConfig('steps', Number(e.target.value))}
                                    />
                                </div>
                                <div className="form-group">
                                    <label>CFG</label>
                                    <input
                                        type="number" className="input-number w-full"
                                        value={config.cfg_scale}
                                        step={0.5}
                                        onChange={(e) => updateConfig('cfg_scale', Number(e.target.value))}
                                    />
                                </div>
                            </div>
                            <div className="grid grid-cols-2 gap-3">
                                <div className="form-group">
                                    <label>Width</label>
                                    <input
                                        type="number" className="input-number w-full"
                                        value={config.width}
                                        onChange={(e) => updateConfig('width', Number(e.target.value))}
                                        step={64}
                                    />
                                </div>
                                <div className="form-group">
                                    <label>Height</label>
                                    <input
                                        type="number" className="input-number w-full"
                                        value={config.height}
                                        onChange={(e) => updateConfig('height', Number(e.target.value))}
                                        step={64}
                                    />
                                </div>
                            </div>
                            <label className="checkbox-label flex items-center gap-2 cursor-pointer p-2 rounded hover:bg-[var(--bg-primary)] transition-colors">
                                <input
                                    type="checkbox"
                                    checked={config.use_hires_fix}
                                    onChange={(e) => updateConfig('use_hires_fix', e.target.checked)}
                                />
                                <span className="text-xs text-[var(--text-primary)] font-medium">Hires. Fix (Upscale)</span>
                            </label>
                        </div>
                    )}

                    {/* Action Buttons */}
                    <div className="mt-6 space-y-2">
                        <button
                            onClick={generate}
                            className="btn btn-primary w-full py-3.5 text-sm font-bold shadow-lg shadow-[var(--accent-primary)]/20 uppercase tracking-widest"
                            disabled={loading}
                        >
                            {loading ? <Loader2 className="animate-spin" /> : <Play size={16} fill="currentColor" />}
                            {loading ? 'Generating...' : 'Generate Image'}
                        </button>

                        <div className="grid grid-cols-2 gap-2">
                            <button
                                onClick={handleGenerateVideo}
                                className="btn btn-secondary py-2 text-xs gap-1"
                                disabled={generatingVideo || loading}
                            >
                                <Film size={14} />
                                {generatingVideo ? 'Generating...' : 'Video / Reel'}
                            </button>
                            <button
                                onClick={handleGenerateAvatar}
                                className="btn btn-secondary py-2 text-xs gap-1"
                                disabled={generatingAvatar || loading}
                            >
                                <UserCircle size={14} />
                                {generatingAvatar ? 'Generating...' : 'Talking Avatar'}
                            </button>
                        </div>

                        <button
                            onClick={handlePreviewPrompt}
                            className="btn btn-ghost w-full py-2 text-xs gap-1 border border-[var(--border-color)]"
                        >
                            <Eye size={14} /> Preview Prompt
                        </button>
                    </div>
                </div>
            </div>

            {/* Right Gallery */}
            <div className="flex-1 flex flex-col h-full bg-[var(--bg-secondary)]/30 rounded-[var(--radius-lg)] border border-[var(--border-color)] overflow-hidden z-10 backdrop-blur-sm">
                <div className="p-4 border-b border-[var(--border-color)] flex justify-between items-center bg-[var(--bg-secondary)]/50">
                    <h3 className="font-bold text-[var(--text-primary)] flex items-center gap-2">
                        <ImageIcon size={18} className="text-[var(--accent-primary)]" />
                        Gallery
                    </h3>
                    {results.length > 0 && <span className="text-xs text-[var(--text-muted)] border border-[var(--border-color)] rounded-full px-2 py-0.5">{results.length} images</span>}
                </div>

                <div className="flex-1 p-5 overflow-y-auto">
                    {/* Prompt Preview Panel */}
                    {promptPreview && (
                        <div className="mb-4 p-4 bg-[var(--bg-tertiary)] rounded-[var(--radius-md)] border border-[var(--border-color)]">
                            <div className="flex justify-between items-center mb-2">
                                <h4 className="text-xs font-bold uppercase tracking-wider text-[var(--accent-primary)]">Prompt Preview</h4>
                                <button onClick={() => setPromptPreview(null)} className="text-[var(--text-muted)] hover:text-white">
                                    <X size={14} />
                                </button>
                            </div>
                            <pre className="text-xs text-[var(--text-primary)] whitespace-pre-wrap font-mono bg-[var(--bg-primary)] p-3 rounded overflow-x-auto">{promptPreview.full_prompt || JSON.stringify(promptPreview, null, 2)}</pre>
                            {promptPreview.negative_prompt && (
                                <pre className="text-xs text-red-300/70 whitespace-pre-wrap font-mono bg-[var(--bg-primary)] p-3 rounded mt-2 overflow-x-auto">{promptPreview.negative_prompt}</pre>
                            )}
                        </div>
                    )}

                    {results.length === 0 && !promptPreview ? (
                        <div className="flex flex-col items-center justify-center h-full text-[var(--text-muted)] opacity-50">
                            <Wand2 size={64} className="mb-4 text-[var(--bg-tertiary)]" />
                            <p className="font-medium">Your masterpieces will appear here</p>
                            <p className="text-sm">Configure settings and click Generate</p>
                        </div>
                    ) : (
                        <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-4 gap-4">
                            {results.map((img, i) => (
                                <div key={i} className="group relative aspect-[2/3] rounded-xl overflow-hidden bg-[var(--bg-card)] border border-[var(--border-color)] shadow-sm hover:shadow-xl hover:border-[var(--accent-primary)]/50 transition-all duration-300">
                                    <img
                                        src={`/api/view?path=${encodeURIComponent(img.image_path || img)}`}
                                        alt={`Result ${i}`}
                                        className="w-full h-full object-cover transform group-hover:scale-105 transition-transform duration-500"
                                        loading="lazy"
                                    />
                                    <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300 flex flex-col justify-end p-3">
                                        <div className="text-xs text-white/90 font-medium truncate w-full mb-1">
                                            {config.prompt.slice(0, 30)}...
                                        </div>
                                        <div className="flex justify-between items-center text-[10px] text-white/60">
                                            <span>{img.seed || 'Seed: N/A'}</span>
                                            <span className="uppercase tracking-wider">{config.width}x{config.height}</span>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
