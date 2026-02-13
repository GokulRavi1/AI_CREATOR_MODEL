import { useApp } from '../../context/AppContext';
import { User, Palette, Monitor, Calendar } from 'lucide-react';

export default function Sidebar() {
    const { activeTab, setActiveTab } = useApp();

    return (
        <aside className="app-sidebar">
            <div className="nav-group">
                <div className="nav-label">APPS</div>
                <button
                    className={`nav-item ${activeTab === 'identity' ? 'active' : ''}`}
                    onClick={() => setActiveTab('identity')}
                >
                    <User size={20} />
                    <span>Identity Lab</span>
                </button>
                <button
                    className={`nav-item ${activeTab === 'studio' ? 'active' : ''}`}
                    onClick={() => setActiveTab('studio')}
                >
                    <Palette size={20} />
                    <span>Content Studio</span>
                </button>
                <button
                    className={`nav-item ${activeTab === 'history' ? 'active' : ''}`}
                    onClick={() => setActiveTab('history')}
                >
                    <Calendar size={20} />
                    <span>History</span>
                </button>
                <button
                    className={`nav-item ${activeTab === 'system' ? 'active' : ''}`}
                    onClick={() => setActiveTab('system')}
                >
                    <Monitor size={20} />
                    <span>System</span>
                </button>
            </div>

            <div className="sidebar-footer">
                <div className="user-info">
                    <div className="user-avatar">
                        <span>AI</span>
                    </div>
                    <div className="user-details">
                        <span className="user-name">Admin User</span>
                        <span className="user-role">Pro Plan</span>
                    </div>
                </div>
            </div>
        </aside>
    );
}
