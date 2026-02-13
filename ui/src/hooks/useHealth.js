import { useState, useEffect, useCallback, useRef } from 'react';
import api from '../api';

export function useHealth(pollIntervalMs = 30000) {
    const [health, setHealth] = useState({
        connected: false,
        version: null,
        comfyui: null,
        voiceEngine: null,
        avatarEngine: null,
    });
    const [models, setModels] = useState({ loras: [], checkpoints: [] });
    const interval = useRef(null);

    const checkHealth = useCallback(async () => {
        try {
            const res = await api.get('/health');
            setHealth({
                connected: true,
                version: res.data.version,
                comfyui: res.data.comfyui,
                voiceEngine: res.data.config?.voice_engine || null,
                avatarEngine: res.data.config?.avatar_engine || null,
            });
        } catch {
            setHealth(prev => ({ ...prev, connected: false }));
        }
    }, []);

    const fetchModels = useCallback(async () => {
        try {
            const res = await api.get('/models');
            setModels({
                loras: res.data.loras || [],
                checkpoints: res.data.checkpoints || [],
            });
        } catch {
            console.warn('Could not load models');
        }
    }, []);

    useEffect(() => {
        checkHealth();
        fetchModels();
        interval.current = setInterval(checkHealth, pollIntervalMs);
        return () => { if (interval.current) clearInterval(interval.current); };
    }, [checkHealth, fetchModels, pollIntervalMs]);

    return { health, models, checkHealth, fetchModels };
}
