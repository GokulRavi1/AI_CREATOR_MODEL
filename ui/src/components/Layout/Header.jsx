import { Zap } from 'lucide-react';
import { useHealth } from '../../hooks/useHealth';

export default function Header() {
    const { health } = useHealth();

    return (
        <header className="app-header">
            <div className="header-left">
                <div className="logo">
                    <Zap className="logo-icon" size={24} />
                    <h1>AI Character Studio</h1>
                </div>
                <span className="version-badge">v0.3.0 React</span>
            </div>
            <div className="header-right">
                <div className="flex items-center gap-4">
                    {/* ComfyUI Status */}
                    {health.comfyui && (
                        <div className="flex items-center gap-1.5 text-xs text-[var(--text-muted)]">
                            <div className={`w-2 h-2 rounded-full ${health.comfyui.connected ? 'bg-green-500' : 'bg-yellow-500'}`}></div>
                            ComfyUI
                        </div>
                    )}
                    {/* Server Status */}
                    <div className="status-indicator">
                        <div className={`status-dot ${health.connected ? 'online' : 'offline'}`}></div>
                        {health.connected ? 'Connected' : 'Disconnected'}
                    </div>
                </div>
            </div>
        </header>
    );
}
