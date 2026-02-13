import { useState, useCallback, useEffect, useRef } from 'react';
import api from '../api';
import { useApp } from '../context/AppContext';

function buildBodyConfig(character) {
    // base_description should be ONLY the physical description —
    // the engine wraps it in its own prompt structure.
    const desc = character?.description || 'a person';
    return {
        base_description: desc,
        lora_trigger: character?.trigger_word || '',
        lora_strength: character?.lora_weight || 0.8,
        limit: 2,
        checkpoint: '',
        width: 512,
        height: 768,
        steps: 25,
        cfg_scale: 7.0,
    };
}

export function useBodyConsistency(character) {
    const characterName = character?.name;
    const { addToast } = useApp();
    const [results, setResults] = useState([]);
    const [loading, setLoading] = useState(false);
    const [controlImage, setControlImage] = useState(null); // Backend filename
    const [controlImageFile, setControlImageFile] = useState(null); // Local preview URL

    const [config, setConfig] = useState(() => buildBodyConfig(character));

    // Reset config when character changes
    useEffect(() => {
        setConfig(buildBodyConfig(character));
        setResults([]);
    }, [characterName]);

    const [selectedIndices, setSelectedIndices] = useState([]);

    const pollInterval = useRef(null);

    const fetchResults = useCallback(async () => {
        if (!characterName) return;
        try {
            const res = await api.get(`/discovery/body/${characterName}`);
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
                console.error("Failed to fetch body results:", err);
            }
        }
    }, [characterName]);

    useEffect(() => {
        fetchResults();
    }, [fetchResults]);

    const uploadControlImage = useCallback(async (file) => {
        const formData = new FormData();
        formData.append('file', file);
        try {
            const res = await api.post('/upload/image', formData);
            if (res.data.filename) {
                setControlImage(res.data.filename);
                setControlImageFile(URL.createObjectURL(file));
                addToast('Reference image uploaded', 'success');
            }
        } catch (err) {
            console.error(err);
            addToast('Upload failed', 'error');
        }
    }, [addToast]);

    const removeControlImage = useCallback(() => {
        setControlImage(null);
        setControlImageFile(null);
    }, []);

    const toggleSelection = useCallback((index) => {
        setSelectedIndices(prev => {
            if (prev.includes(index)) {
                return prev.filter(i => i !== index);
            } else {
                return [...prev, index];
            }
        });
    }, []);

    const saveToDataset = useCallback(async () => {
        if (!characterName) return;
        // If no selection, backend might assume "all" or fail. 
        // For safety, warn if empty, unless backend supports "all".
        // Backend doc says "indices = body.selected_indices if body else None".
        // If None, it copies ALL images.

        try {
            const payload = selectedIndices.length > 0 ? { selected_indices: selectedIndices } : {};
            const res = await api.post(`/discovery/body/${characterName}/select`, payload);
            if (res.data.success) {
                addToast(`Saved ${res.data.saved_count} images to dataset`, 'success');
                setSelectedIndices([]);
            }
        } catch (err) {
            addToast('Failed to save to dataset', 'error');
            console.error(err);
        }
    }, [characterName, selectedIndices, addToast]);

    const generate = useCallback(async () => {
        if (!characterName) return;
        if (!controlImage) {
            addToast('Please upload a reference image first', 'warning');
            return;
        }
        setLoading(true);
        addToast('Starting Body Consistency...', 'info');

        try {
            const payload = {
                character_name: characterName,
                control_image_name: controlImage,
                ...config
            };

            const res = await api.post('/discovery/body', payload);

            if (res.data.success) {
                addToast('Body consistency task queued', 'success');

                if (pollInterval.current) clearInterval(pollInterval.current);
                pollInterval.current = setInterval(fetchResults, 2000);

                // Auto-stop polling after 90s
                setTimeout(() => {
                    if (pollInterval.current) {
                        clearInterval(pollInterval.current);
                        pollInterval.current = null;
                        setLoading(false);
                    }
                }, 90000);
            }
        } catch (err) {
            console.error(err);
            addToast(err.response?.data?.detail || 'Generation failed', 'error');
            setLoading(false);
        }
    }, [characterName, controlImage, config, addToast, fetchResults]);

    // Cleanup
    useEffect(() => {
        return () => {
            if (pollInterval.current) clearInterval(pollInterval.current);
        }
    }, []);

    return {
        results,
        config,
        setConfig,
        generate,
        loading,
        uploadControlImage,
        controlImageFile,
        removeControlImage,
        selectedIndices,
        toggleSelection,
        saveToDataset
    };
}
