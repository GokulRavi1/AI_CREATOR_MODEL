import React from 'react';
import { useHealth } from '../hooks/useHealth';
import { Server, Cpu, Mic, Video, Box, HardDrive, CheckCircle2, XCircle, RefreshCw } from 'lucide-react';

export default function SystemStatus() {
    const { health, models, checkHealth } = useHealth();

    const StatusCard = ({ icon: Icon, label, value, ok }) => (
        <div className="p-4 rounded-[var(--radius-md)] bg-[var(--bg-secondary)]/80 border border-[var(--border-color)]">
            <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2 text-sm font-semibold text-[var(--text-secondary)]">
                    <Icon size={16} className="text-[var(--accent-primary)]" />
                    {label}
                </div>
                {ok !== undefined && (
                    ok ? <CheckCircle2 size={16} className="text-green-400" /> : <XCircle size={16} className="text-red-400" />
                )}
            </div>
            <p className="text-sm text-[var(--text-primary)] font-medium">{value || '—'}</p>
        </div>
    );

    return (
        <div className="flex flex-col h-full bg-[var(--bg-primary)] p-6 overflow-y-auto">
            {/* Header */}
            <div className="flex items-center justify-between mb-6">
                <div>
                    <h2 className="text-2xl font-bold text-[var(--text-primary)] tracking-tight">System Status</h2>
                    <p className="text-sm text-[var(--text-muted)] mt-1">Monitor backend services and available models</p>
                </div>
                <button onClick={checkHealth} className="btn btn-secondary px-3 py-2 text-xs gap-1.5">
                    <RefreshCw size={14} /> Refresh
                </button>
            </div>

            {/* Status Cards Grid */}
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
                <StatusCard
                    icon={Server}
                    label="Server"
                    value={health.connected ? `v${health.version} — Running` : 'Disconnected'}
                    ok={health.connected}
                />
                <StatusCard
                    icon={Cpu}
                    label="ComfyUI"
                    value={health.comfyui?.connected ? `Connected (${health.comfyui.url || 'localhost:8188'})` : 'Not Connected'}
                    ok={health.comfyui?.connected}
                />
                <StatusCard
                    icon={Mic}
                    label="Voice Engine"
                    value={health.voiceEngine || 'Not configured'}
                    ok={!!health.voiceEngine}
                />
                <StatusCard
                    icon={Video}
                    label="Avatar Engine"
                    value={health.avatarEngine || 'Not configured'}
                    ok={!!health.avatarEngine}
                />
            </div>

            {/* Models Section */}
            <div className="flex-1">
                <h3 className="text-lg font-bold text-[var(--text-primary)] mb-4 flex items-center gap-2">
                    <Box size={18} className="text-[var(--accent-primary)]" />
                    Available Models
                </h3>

                {models.loras.length === 0 && models.checkpoints.length === 0 ? (
                    <div className="text-center py-12 text-[var(--text-muted)]">
                        <HardDrive size={40} className="mx-auto mb-3 opacity-30" />
                        <p className="text-sm">No models found. Add .safetensors files to models/loras/</p>
                    </div>
                ) : (
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                        {/* Checkpoints */}
                        {models.checkpoints.length > 0 && (
                            <div className="panel-section p-4 rounded-[var(--radius-md)]">
                                <h4 className="text-xs font-bold uppercase tracking-wider text-[var(--text-secondary)] mb-3">
                                    Checkpoints ({models.checkpoints.length})
                                </h4>
                                <div className="space-y-1.5">
                                    {models.checkpoints.map(m => {
                                        const name = typeof m === 'string' ? m : m.name;
                                        const size = typeof m === 'object' ? `${m.size_mb} MB` : null;
                                        return (
                                            <div key={name} className="flex justify-between items-center py-1.5 px-2 rounded text-sm hover:bg-[var(--bg-tertiary)]/50 transition-colors">
                                                <span className="text-[var(--text-primary)] truncate">{name}</span>
                                                {size && <span className="text-xs text-[var(--text-muted)] flex-shrink-0 ml-2">{size}</span>}
                                            </div>
                                        );
                                    })}
                                </div>
                            </div>
                        )}

                        {/* LoRAs */}
                        {models.loras.length > 0 && (
                            <div className="panel-section p-4 rounded-[var(--radius-md)]">
                                <h4 className="text-xs font-bold uppercase tracking-wider text-[var(--text-secondary)] mb-3">
                                    LoRA Models ({models.loras.length})
                                </h4>
                                <div className="space-y-1.5">
                                    {models.loras.map(m => {
                                        const name = typeof m === 'string' ? m : m.name;
                                        const size = typeof m === 'object' ? `${m.size_mb} MB` : null;
                                        return (
                                            <div key={name} className="flex justify-between items-center py-1.5 px-2 rounded text-sm hover:bg-[var(--bg-tertiary)]/50 transition-colors">
                                                <span className="text-[var(--text-primary)] truncate">{name}</span>
                                                {size && <span className="text-xs text-[var(--text-muted)] flex-shrink-0 ml-2">{size}</span>}
                                            </div>
                                        );
                                    })}
                                </div>
                            </div>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
}
