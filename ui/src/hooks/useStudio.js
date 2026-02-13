import { useState, useCallback, useEffect, useRef } from 'react';
import api from '../api';
import { useApp } from '../context/AppContext';

export function useStudio() {
    const { addToast } = useApp();
    const [results, setResults] = useState([]);
    const [loading, setLoading] = useState(false);

    // We need a way to track the control image file for preview
    const [controlImageFile, setControlImageFile] = useState(null);

    const [config, setConfig] = useState({
        prompt: "A cinematic shot of a futuristic city, neon lights, rain, 8k, highly detailed",
        negative_prompt: "text, watermark, low quality, blurred, distorted, ugly",
        width: 1024,
        height: 1024,
        steps: 30,
        cfg_scale: 7.0,
        checkpoint: "RealVisXL_V4.0.safetensors",
        lora_name: "",
        lora_strength: 0.8,
        seed: -1,
        use_hires_fix: false,
        // ControlNet
        controlnet_enabled: false,
        controlnet_name: "controlnet-canny-sdxl-1.0",
        control_image_name: null
    });

    const pollInterval = useRef(null);

    // Poll for general results? 
    // The backend doesn't have a specific "get studio results" endpoint that persists like discovery
    // Usually studio just returns the result or we poll a general "latest" endpoint?
    // Checking main.py... `/api/studio/generate` returns the result directly?
    // No, `content_engine.generate` is async in ComfyUI but synchronous locally?
    // Let's assume it returns the result for now based on `main.py` lines 771-821.
    // Wait, `api_studio_generate` calls `content_engine.generate` which returns `result`.
    // If `content_engine` waits for ComfyUI, then it is synchronous HTTP response (long polling).

    const generate = useCallback(async () => {
        setLoading(true);
        addToast('Starting Studio Generation...', 'info');

        try {
            // If ControlNet is enabled but no image
            if (config.controlnet_enabled && !config.control_image_name) {
                addToast('ControlNet enabled but no reference image selected', 'warning');
                setLoading(false);
                return;
            }

            const res = await api.post('/studio/generate', config);

            if (res.data.success && res.data.images) {
                setResults(prev => [...res.data.images, ...prev]);
                addToast('Generation complete', 'success');
            } else {
                addToast('Generation finished but no images returned', 'warning');
            }
        } catch (err) {
            console.error(err);
            addToast(err.response?.data?.detail || 'Generation failed', 'error');
        } finally {
            setLoading(false);
        }
    }, [config, addToast]);

    const uploadControlImage = useCallback(async (file) => {
        const formData = new FormData();
        formData.append('file', file);
        try {
            const res = await api.post('/upload/image', formData);
            if (res.data.filename) {
                setConfig(prev => ({ ...prev, control_image_name: res.data.filename }));
                setControlImageFile(URL.createObjectURL(file));
                addToast('Control image set', 'success');
            }
        } catch (err) {
            addToast('Upload failed', 'error');
        }
    }, [addToast]);

    const removeControlImage = useCallback(() => {
        setConfig(prev => ({ ...prev, control_image_name: null }));
        setControlImageFile(null);
    }, []);

    const updateConfig = useCallback((key, value) => {
        setConfig(prev => ({ ...prev, [key]: value }));
    }, []);

    return {
        results,
        config,
        updateConfig,
        generate,
        loading,
        uploadControlImage,
        controlImageFile,
        removeControlImage
    };
}
