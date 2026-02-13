import React, { useState } from 'react';
import { useCharacters } from '../../hooks/useCharacters';
import { User, Plus, Trash2, Zap, X } from 'lucide-react';

export default function CharacterManager({ onClose }) {
    const { characters, activeCharacter, selectCharacter, createCharacter, deleteCharacter, loading } = useCharacters();
    const [showForm, setShowForm] = useState(false);
    const [form, setForm] = useState({ name: '', trigger_word: '', description: '' });
    const [saving, setSaving] = useState(false);

    const handleCreate = async () => {
        if (!form.name.trim() || !form.trigger_word.trim()) return;
        setSaving(true);
        const ok = await createCharacter(form.name.trim(), form.trigger_word.trim(), form.description.trim());
        setSaving(false);
        if (ok) {
            setForm({ name: '', trigger_word: '', description: '' });
            setShowForm(false);
        }
    };

    const handleDelete = async (name) => {
        if (!window.confirm(`Delete character '${name}'? This cannot be undone.`)) return;
        await deleteCharacter(name);
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm" onClick={onClose}>
            <div
                className="bg-[var(--bg-secondary)] border border-[var(--border-color)] rounded-[var(--radius-lg)] w-full max-w-lg mx-4 shadow-2xl"
                onClick={e => e.stopPropagation()}
            >
                {/* Header */}
                <div className="flex items-center justify-between p-5 border-b border-[var(--border-color)]">
                    <h2 className="text-lg font-bold text-[var(--text-primary)] flex items-center gap-2">
                        <User size={20} className="text-[var(--accent-primary)]" />
                        Character Manager
                    </h2>
                    <button onClick={onClose} className="text-[var(--text-muted)] hover:text-white transition-colors p-1">
                        <X size={20} />
                    </button>
                </div>

                {/* Character List */}
                <div className="p-5 max-h-[400px] overflow-y-auto">
                    {characters.length === 0 ? (
                        <div className="text-center py-8 text-[var(--text-muted)]">
                            <User size={40} className="mx-auto mb-3 opacity-30" />
                            <p className="text-sm">No characters yet — create one below</p>
                        </div>
                    ) : (
                        <div className="space-y-2">
                            {characters.map(char => (
                                <div
                                    key={char.name}
                                    className={`flex items-center justify-between p-3 rounded-[var(--radius-md)] border transition-all cursor-pointer group ${activeCharacter?.name === char.name
                                            ? 'bg-[var(--accent-primary)]/10 border-[var(--accent-primary)]/30'
                                            : 'bg-[var(--bg-tertiary)]/50 border-[var(--border-color)] hover:border-[var(--border-hover)]'
                                        }`}
                                    onClick={() => selectCharacter(char)}
                                >
                                    <div className="flex items-center gap-3">
                                        <div className={`w-9 h-9 rounded-full flex items-center justify-center text-xs font-bold ${activeCharacter?.name === char.name
                                                ? 'bg-[var(--accent-primary)] text-white'
                                                : 'bg-[var(--bg-tertiary)] text-[var(--text-muted)]'
                                            }`}>
                                            {char.name.substring(0, 2).toUpperCase()}
                                        </div>
                                        <div>
                                            <div className="font-semibold text-sm text-[var(--text-primary)]">{char.name}</div>
                                            <div className="text-xs text-[var(--text-muted)] flex items-center gap-2">
                                                <span>{char.trigger_word}</span>
                                                {char.lora_path && <span className="text-[10px] bg-green-500/20 text-green-400 px-1.5 rounded">LoRA</span>}
                                                {activeCharacter?.name === char.name && <span className="text-[10px] bg-[var(--accent-primary)]/20 text-[var(--accent-secondary)] px-1.5 rounded">Active</span>}
                                            </div>
                                        </div>
                                    </div>
                                    <button
                                        onClick={(e) => { e.stopPropagation(); handleDelete(char.name); }}
                                        className="opacity-0 group-hover:opacity-100 text-[var(--text-muted)] hover:text-red-400 transition-all p-1.5 rounded hover:bg-red-500/10"
                                        title="Delete character"
                                    >
                                        <Trash2 size={14} />
                                    </button>
                                </div>
                            ))}
                        </div>
                    )}
                </div>

                {/* Create Form */}
                <div className="p-5 border-t border-[var(--border-color)]">
                    {!showForm ? (
                        <button
                            onClick={() => setShowForm(true)}
                            className="btn btn-secondary w-full py-2.5 text-sm gap-2"
                        >
                            <Plus size={16} /> Create New Character
                        </button>
                    ) : (
                        <div className="space-y-3">
                            <div className="grid grid-cols-2 gap-3">
                                <div className="form-group">
                                    <label>Name</label>
                                    <input
                                        type="text"
                                        className="input-text w-full"
                                        value={form.name}
                                        onChange={e => setForm(prev => ({ ...prev, name: e.target.value }))}
                                        placeholder="e.g. alex_model"
                                    />
                                </div>
                                <div className="form-group">
                                    <label>Trigger Word</label>
                                    <input
                                        type="text"
                                        className="input-text w-full"
                                        value={form.trigger_word}
                                        onChange={e => setForm(prev => ({ ...prev, trigger_word: e.target.value }))}
                                        placeholder="e.g. ohm_alex"
                                    />
                                </div>
                            </div>
                            <div className="form-group">
                                <label>Description</label>
                                <input
                                    type="text"
                                    className="input-text w-full"
                                    value={form.description}
                                    onChange={e => setForm(prev => ({ ...prev, description: e.target.value }))}
                                    placeholder="e.g. young man with brown hair and blue eyes"
                                />
                            </div>
                            <div className="flex gap-2">
                                <button onClick={handleCreate} disabled={saving} className="btn btn-primary flex-1 py-2 text-sm">
                                    {saving ? 'Creating...' : 'Create'}
                                </button>
                                <button onClick={() => setShowForm(false)} className="btn btn-ghost px-4 py-2 text-sm">
                                    Cancel
                                </button>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
