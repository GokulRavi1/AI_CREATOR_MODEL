import { useState, useEffect } from 'react';
import api from '../api';

export function useModels() {
    const [models, setModels] = useState({ checkpoints: [], loras: [] });
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        const fetchModels = async () => {
            setLoading(true);
            try {
                const res = await api.get('/models');
                setModels(res.data);
            } catch (err) {
                console.error("Failed to fetch models", err);
            } finally {
                setLoading(false);
            }
        };
        fetchModels();
    }, []);

    return { models, loading };
}
