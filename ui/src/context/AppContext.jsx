import { createContext, useContext, useState, useCallback } from 'react';

const AppContext = createContext();

export function AppProvider({ children }) {
    const [activeTab, setActiveTab] = useState('identity'); // 'identity' or 'studio'
    const [activeSubTab, setActiveSubTab] = useState('discovery'); // identity: discovery/consistency, studio: gallery/canvas
    const [toasts, setToasts] = useState([]);

    const addToast = useCallback((message, type = 'info') => {
        // Safely convert non-string messages (e.g. FastAPI validation error arrays)
        let safeMessage = message;
        if (Array.isArray(message)) {
            safeMessage = message.map(e => e?.msg || JSON.stringify(e)).join('; ');
        } else if (typeof message === 'object' && message !== null) {
            safeMessage = message?.msg || message?.message || JSON.stringify(message);
        }
        const id = Date.now();
        setToasts(prev => [...prev, { id, message: String(safeMessage), type }]);
        setTimeout(() => removeToast(id), 3000);
    }, []);

    const removeToast = useCallback((id) => {
        setToasts(prev => prev.filter(t => t.id !== id));
    }, []);

    const value = {
        activeTab,
        setActiveTab,
        activeSubTab,
        setActiveSubTab,
        toasts,
        addToast,
        removeToast
    };

    return (
        <AppContext.Provider value={value}>
            {children}
        </AppContext.Provider>
    );
}

export function useApp() {
    const context = useContext(AppContext);
    if (!context) {
        throw new Error('useApp must be used within an AppProvider');
    }
    return context;
}
