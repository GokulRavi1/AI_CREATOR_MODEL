import React, { useState } from 'react';
import { useCharacters } from '../../hooks/useCharacters';
import { User, Sparkles, Layers, Binary, Plus } from 'lucide-react';
import FaceDiscovery from './FaceDiscovery';
import BodyConsistency from './BodyConsistency';
import TrainingLab from './TrainingLab';
import CharacterManager from './CharacterManager';

export default function IdentityLab() {
    const { characters, activeCharacter, selectCharacter, loading } = useCharacters();
    const [tab, setTab] = useState('discovery');
    const [showManager, setShowManager] = useState(false);

    if (loading && characters.length === 0) {
        return (
            <div className="flex items-center justify-center h-full text-[var(--text-muted)] animate-pulse">
                <div className="flex flex-col items-center gap-4">
                    <div className="w-16 h-16 rounded-full bg-[var(--bg-tertiary)] flex items-center justify-center">
                        <User size={32} className="opacity-20" />
                    </div>
                    <p className="text-sm tracking-wider uppercase font-medium">Loading Identity Lab...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="flex flex-col h-full bg-[var(--bg-primary)] relative overflow-hidden">
            {/* Background Ambient Glow */}
            <div className="absolute top-0 left-0 right-0 h-64 bg-gradient-to-b from-[var(--accent-glow)] to-transparent pointer-events-none opacity-20" />

            {/* ── Character Header ── */}
            <div className="relative z-10 px-8 py-6 flex items-end justify-between border-b border-[var(--border-color)] bg-[var(--bg-primary)]/50 backdrop-blur-sm">
                <div className="flex items-center gap-5">
                    <div className="relative">
                        <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-[var(--accent-primary)] to-[var(--accent-secondary)] p-0.5 shadow-2xl shadow-[var(--accent-primary)]/20">
                            <div className="w-full h-full bg-[var(--bg-secondary)] rounded-[14px] flex items-center justify-center text-white overflow-hidden">
                                {activeCharacter ? (
                                    <span className="text-2xl font-bold">{activeCharacter.name.substring(0, 2).toUpperCase()}</span>
                                ) : (
                                    <User size={24} />
                                )}
                            </div>
                        </div>
                        <div className="absolute -bottom-1 -right-1 w-5 h-5 bg-green-500 rounded-full border-4 border-[var(--bg-primary)]"></div>
                    </div>

                    <div>
                        <h2 className="text-3xl font-bold text-[var(--text-primary)] tracking-tight leading-none mb-1">
                            {activeCharacter?.name || 'No Identity Selected'}
                        </h2>
                        <div className="flex items-center gap-2 text-[var(--text-secondary)] text-sm font-medium">
                            <span className="bg-[var(--bg-tertiary)] px-2 py-0.5 rounded text-[10px] uppercase tracking-widest text-[var(--text-muted)] border border-[var(--border-color)]">
                                Fixed Identity
                            </span>
                            <span>•</span>
                            <span>{characters.length} Available</span>
                        </div>
                    </div>
                </div>

                {/* Character Selector */}
                <div className="flex items-center gap-3">
                    <div className="flex -space-x-2 mr-4">
                        {characters.slice(0, 5).map(char => (
                            <button
                                key={char.name}
                                onClick={() => selectCharacter(char)}
                                title={char.name}
                                className={`w-8 h-8 rounded-full border-2 border-[var(--bg-primary)] flex items-center justify-center text-[10px] font-bold text-white transition-transform hover:scale-110 hover:z-10
                                    ${activeCharacter?.name === char.name
                                        ? 'bg-[var(--accent-primary)] ring-2 ring-[var(--accent-primary)]/30'
                                        : 'bg-[var(--bg-tertiary)] text-[var(--text-muted)] hover:bg-[var(--bg-hover)]'}
                                `}
                            >
                                {char.name.substring(0, 1).toUpperCase()}
                            </button>
                        ))}
                        <button
                            onClick={() => setShowManager(true)}
                            className="w-8 h-8 rounded-full border-2 border-[var(--bg-primary)] bg-[var(--bg-tertiary)] flex items-center justify-center text-[var(--text-muted)] hover:text-white hover:bg-[var(--bg-hover)] transition-colors"
                            title="Manage characters"
                        >
                            <Plus size={12} />
                        </button>
                    </div>
                </div>
            </div>

            {/* ── Tabs ── */}
            <div className="relative z-10 px-8 flex gap-8 border-b border-[var(--border-color)] bg-[var(--bg-primary)]/50 backdrop-blur-sm">
                <button
                    className={`pb-3 pt-4 text-sm font-medium border-b-2 transition-all flex items-center gap-2 ${tab === 'discovery' ? 'text-[var(--accent-primary)] border-[var(--accent-primary)]' : 'text-[var(--text-secondary)] border-transparent hover:text-[var(--text-primary)]'}`}
                    onClick={() => setTab('discovery')}
                >
                    <Sparkles size={16} />
                    Face Discovery
                </button>
                <button
                    className={`pb-3 pt-4 text-sm font-medium border-b-2 transition-all flex items-center gap-2 ${tab === 'consistency' ? 'text-[var(--accent-primary)] border-[var(--accent-primary)]' : 'text-[var(--text-secondary)] border-transparent hover:text-[var(--text-primary)]'}`}
                    onClick={() => setTab('consistency')}
                >
                    <Layers size={16} />
                    Body Consistency
                </button>
                <button
                    className={`pb-3 pt-4 text-sm font-medium border-b-2 transition-all flex items-center gap-2 ${tab === 'training' ? 'text-[var(--accent-primary)] border-[var(--accent-primary)]' : 'text-[var(--text-secondary)] border-transparent hover:text-[var(--text-primary)]'}`}
                    onClick={() => setTab('training')}
                >
                    <Binary size={16} />
                    Training
                </button>
            </div>

            {/* ── Content Area ── */}
            <div className="flex-1 overflow-y-auto p-6 bg-[var(--bg-primary)] relative z-0">
                {tab === 'discovery' ? (
                    <FaceDiscovery character={activeCharacter} />
                ) : tab === 'consistency' ? (
                    <BodyConsistency character={activeCharacter} />
                ) : (
                    <TrainingLab character={activeCharacter} />
                )}
            </div>

            {/* Character Manager Modal */}
            {showManager && <CharacterManager onClose={() => setShowManager(false)} />}
        </div>
    );
}
