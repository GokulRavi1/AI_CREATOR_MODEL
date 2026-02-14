import { useState, useCallback, useEffect, useRef } from 'react';
import api from '../api';
import { useApp } from '../context/AppContext';

function buildDefaultConfig(character) {
    // base_description should be ONLY the physical description —
    // the engine wraps it in "close-up portrait of {base_description}" and
    // handles trigger word, quality boosters, and negative prompts separately.
    const desc = character?.description || 'a person';
    return {
        base_description: desc,
        lora_trigger: character?.trigger_word || '',
        lora_strength: character?.lora_weight || 0.8,
        limit: 4,
        checkpoint: '',
        character_lora: '',
        width: 512,
        height: 768,
        steps: 25,
        cfg_scale: 7.0,
    };
}

export function useDiscovery(character) {
    const characterName = character?.name;
    const { addToast } = useApp();
    const [results, setResults] = useState([]);
    const [loading, setLoading] = useState(false);
    const [config, setConfig] = useState(() => buildDefaultConfig(character));

    // Reset config when character changes
    useEffect(() => {
        setConfig(buildDefaultConfig(character));
        setResults([]);
    }, [characterName]);

    const pollInterval = useRef(null);

    const fetchResults = useCallback(async () => {
        if (!characterName) return;
        try {
            const res = await api.get(`/discovery/face/${characterName}`);
            const data = res.data;
            if (data && data.found && data.manifest) {
                // Flatten image_urls from all results entries
                const allImages = (data.manifest.results || [])
                    .flatMap(r => r.image_urls || r.images || []);
                if (allImages.length > 0) {
                    setResults(allImages);
                    setLoading(false);
                }
            }
        } catch (err) {
            // 404 = no results yet, not an error
            if (err.response?.status !== 404) {
                console.error("Failed to fetch discovery results:", err);
            }
        }
    }, [characterName]);

    // Initial fetch
    useEffect(() => {
        fetchResults();
    }, [fetchResults]);

    const generate = useCallback(async () => {
        if (!characterName) return;
        setLoading(true);
        addToast('Starting Face Discovery...', 'info');

        try {
            const payload = {
                character_name: characterName,
                lora_name: config.character_lora,
                ...config
            };

            const res = await api.post('/discovery/face', payload);

            if (res.data.success) {
                addToast('Discovery task queued', 'success');
                // Start polling
                if (pollInterval.current) clearInterval(pollInterval.current);
                pollInterval.current = setInterval(fetchResults, 2000);

                // Auto-stop polling after 60s (safety)
                setTimeout(() => {
                    if (pollInterval.current) {
                        clearInterval(pollInterval.current);
                        pollInterval.current = null;
                        setLoading(false);
                    }
                }, 60000);
            }
        } catch (err) {
            console.error(err);
            addToast(err.response?.data?.detail || 'Generation failed', 'error');
            setLoading(false);
        }
    }, [characterName, config, addToast, fetchResults]);

    // Cleanup
    useEffect(() => {
        return () => {
            if (pollInterval.current) clearInterval(pollInterval.current);
        }
    }, []);

    const [selectedIndices, setSelectedIndices] = useState([]);

    const toggleSelection = useCallback((index) => {
        setSelectedIndices(prev => {
            if (prev.includes(index)) {
                return prev.filter(i => i !== index);
            } else {
                return [...prev, index];
            }
        });
    }, []);

    const saveIdentity = useCallback(async () => {
        if (!characterName || selectedIndices.length === 0) return;
        try {
            const res = await api.post(`/discovery/face/${characterName}/select`, {
                selected_indices: selectedIndices
            });
            if (res.data.success) {
                addToast(`Saved ${res.data.saved_count} images to dataset`, 'success');
                setSelectedIndices([]);
            }
        } catch (err) {
            addToast('Failed to save identity', 'error');
            console.error(err);
        }
    }, [characterName, selectedIndices, addToast]);

    return {
        results,
        config,
        setConfig,
        generate,
        loading,
        selectedIndices,
        toggleSelection,
        saveIdentity
    };
}
