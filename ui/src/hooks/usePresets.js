import { useState, useEffect, useCallback } from 'react';
import api from '../api';

export function usePresets() {
    const [cameraStyles, setCameraStyles] = useState([]);
    const [lightingStyles, setLightingStyles] = useState([]);
    const [voiceModels, setVoiceModels] = useState([]);
    const [outfits, setOutfits] = useState([]);
    const [loading, setLoading] = useState(false);

    const fetchPresets = useCallback(async () => {
        setLoading(true);
        try {
            const res = await api.get('/presets');
            setCameraStyles(res.data.camera_styles || []);
            setLightingStyles(res.data.lighting_styles || []);
            setVoiceModels(res.data.voice_models || []);
        } catch (err) {
            console.warn('Could not load presets:', err);
        } finally {
            setLoading(false);
        }
    }, []);

    const fetchVariations = useCallback(async () => {
        try {
            const res = await api.get('/discovery/variations');
            if (res.data?.body?.outfits) {
                setOutfits(res.data.body.outfits);
            }
        } catch (err) {
            console.warn('Could not load variations:', err);
        }
    }, []);

    useEffect(() => {
        fetchPresets();
        fetchVariations();
    }, [fetchPresets, fetchVariations]);

    return { cameraStyles, lightingStyles, voiceModels, outfits, loading, refresh: fetchPresets };
}
