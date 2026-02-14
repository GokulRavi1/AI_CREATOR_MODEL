import { useState, useCallback, useEffect, useRef } from 'react';
import api from '../api';
import { useApp } from '../context/AppContext';

export function useTraining(character) {
    const characterName = character?.name;
    const { addToast } = useApp();
    const [loading, setLoading] = useState(false);

    // Dataset State
    const [validation, setValidation] = useState(null);
    const [preparation, setPreparation] = useState(null);
    const [guide, setGuide] = useState(null);

    // Training State
    const [config, setConfig] = useState(() => ({
        character_name: characterName || '',
        trigger_word: character?.trigger_word || 'ohm_person',
        pretrained_model: "runwayml/stable-diffusion-v1-5",
        network_rank: 32,
        network_alpha: 32,
        resolution: 512,
        batch_size: 1,
        epochs: 10,
        learning_rate: 1e-4,
        gpu_vram_gb: 4,
        use_recommended: true
    }));

    // Reset config when character changes
    useEffect(() => {
        setConfig(prev => ({
            ...prev,
            character_name: characterName || '',
            trigger_word: character?.trigger_word || 'ohm_person',
        }));
        setValidation(null);
        setPreparation(null);
    }, [characterName]);

    const [trainingStatus, setTrainingStatus] = useState(null); // 'idle', 'running', 'completed', 'failed', 'manual_action_required'
    const [trainingProgress, setTrainingProgress] = useState(null);
    const [trainingOutput, setTrainingOutput] = useState(null);
    const [logs, setLogs] = useState([]);
    const pollInterval = useRef(null);

    // ── Dataset Actions ──────────────────────────────────────────────

    const validateDataset = useCallback(async () => {
        if (!characterName) return;
        setLoading(true);
        try {
            const res = await api.post(`/dataset/validate?character_name=${characterName}`);
            setValidation(res.data);
            if (res.data.valid) {
                addToast('Dataset is valid!', 'success');
            } else {
                addToast(`Dataset issues found: ${res.data.issues.length}`, 'warning');
            }
        } catch (err) {
            addToast('Validation failed', 'error');
            console.error(err);
        } finally {
            setLoading(false);
        }
    }, [characterName, addToast]);

    const prepareDataset = useCallback(async (options = {}) => {
        if (!characterName) return;
        setLoading(true);
        try {
            // Options: maintain_aspect, resolution
            const payload = {
                character_name: characterName,
                trigger_word: config.trigger_word,
                resolution: 512,
                maintain_aspect: false,
                ...options
            };
            const res = await api.post('/dataset/prepare', payload);
            setPreparation(res.data);
            addToast('Dataset resized & captioned', 'success');
        } catch (err) {
            addToast('Preparation failed', 'error');
            console.error(err);
        } finally {
            setLoading(false);
        }
    }, [characterName, config.trigger_word, addToast]);

    // ── Training Actions ─────────────────────────────────────────────

    const generateConfig = useCallback(async () => {
        if (!characterName) return;
        setLoading(true);
        try {
            const payload = { ...config, character_name: characterName };
            const res = await api.post('/training/config', payload);
            addToast('Training config generated', 'success');
            // If recommended was used, maybe update local config? 
            // The backend returns the generated kohya config, but maybe not the internal one.
        } catch (err) {
            addToast('Config generation failed', 'error');
            console.error(err);
        } finally {
            setLoading(false);
        }
    }, [characterName, config, addToast]);

    const startTraining = useCallback(async () => {
        if (!characterName) return;
        setLoading(true);
        try {
            const payload = { ...config, character_name: characterName };
            const res = await api.post('/training/start', payload);
            if (res.data.success) {
                if (res.data.command) {
                    setTrainingOutput(res.data);
                    addToast('Training command generated', 'success');
                    setTrainingStatus('manual_action_required');
                } else {
                    addToast('Training started!', 'success');
                    setTrainingStatus('running');
                    startPolling();
                }
            }
        } catch (err) {
            addToast('Failed to start training', 'error');
            console.error(err);
            setLoading(false);
        }
    }, [characterName, config, addToast]);

    const stopTraining = useCallback(async () => {
        try {
            await api.post('/training/stop');
            addToast('Training stopped', 'info');
            setTrainingStatus('failed'); // or stopped
            stopPolling();
        } catch (err) {
            console.error(err);
        }
    }, []);

    const fetchStatus = useCallback(async () => {
        try {
            const res = await api.get('/training/status');
            const status = res.data;
            // Assuming status structure from backend: { status: 'running', logs: [], ... }
            // Actually implementation of backend `get_training_status` might differ.
            // Let's assume standard interaction.
            if (status.status !== 'running' && trainingStatus === 'running') {
                if (status.status === 'completed') addToast('Training finished!', 'success');
                if (status.status === 'failed') addToast('Training failed', 'error');
                stopPolling();
            }
            setTrainingStatus(status.status);
            setTrainingProgress(status);
            // setLogs(status.logs); // If logs are returned
        } catch (err) {
            console.error(err);
        }
    }, [trainingStatus, addToast]);

    const startPolling = () => {
        if (pollInterval.current) clearInterval(pollInterval.current);
        pollInterval.current = setInterval(fetchStatus, 2000);
    };

    const stopPolling = () => {
        if (pollInterval.current) clearInterval(pollInterval.current);
        pollInterval.current = null;
        setLoading(false);
    };

    useEffect(() => {
        return () => stopPolling();
    }, []);

    return {
        // State
        loading,
        validation,
        preparation,
        config,
        setConfig,
        config,
        setConfig,
        trainingStatus,
        trainingProgress,
        trainingOutput,

        // Actions
        validateDataset,
        prepareDataset,
        generateConfig,
        startTraining,
        stopTraining
    };
}
