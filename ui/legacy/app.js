/**
 * AI Character Studio — Frontend Application
 * 
 * Handles API communication, UI interactions, and dynamic content rendering.
 */

const API_BASE = '';

// ── State ──────────────────────────────────────────────────────
const state = {
    connected: false,
    presets: { camera_styles: [], lighting_styles: [], voice_models: [] },
    models: { loras: [], checkpoints: [] },
    characters: [],
    activeCharacter: null,
    studio: { ratio: '2:3', controlImage: null },
    bodyConsistency: { controlImage: null },
};

// ── DOM Helpers ────────────────────────────────────────────────
const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => document.querySelectorAll(sel);

// ── Toast Notifications ────────────────────────────────────────
function showToast(message, type = 'info', duration = 4000) {
    const container = $('#toastContainer');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;

    const icons = { success: '✓', error: '✕', info: '◆' };
    toast.innerHTML = `<span>${icons[type] || '◆'}</span><span>${message}</span>`;

    container.appendChild(toast);

    setTimeout(() => {
        toast.style.animation = 'toast-out 0.3s ease-in forwards';
        setTimeout(() => toast.remove(), 300);
    }, duration);
}

// ── API Calls ──────────────────────────────────────────────────
async function apiCall(endpoint, method = 'GET', body = null) {
    try {
        const opts = {
            method,
            headers: { 'Content-Type': 'application/json' },
        };
        if (body) opts.body = JSON.stringify(body);

        const res = await fetch(`${API_BASE}${endpoint}`, opts);
        if (!res.ok) throw new Error(`HTTP ${res.status}: ${res.statusText}`);
        return await res.json();
    } catch (err) {
        console.error(`API Error [${endpoint}]:`, err);
        showToast(`API Error: ${err.message}`, 'error');
        throw err;
    }
}

// ── Health Check ───────────────────────────────────────────────
async function checkHealth() {
    try {
        const data = await apiCall('/api/health');
        state.connected = true;

        const dot = $('.status-dot');
        const text = $('.status-text');
        dot.className = 'status-dot online';
        text.textContent = 'Connected';

        // Update system info
        $('#infoServer').textContent = `v${data.version} — Running`;
        const comfyText = data.comfyui?.connected ? '✅ Connected' : '❌ Not connected';
        $('#infoComfyUI').textContent = comfyText;
        $('#infoVoice').textContent = data.config?.voice_engine || '—';
        $('#infoAvatar').textContent = data.config?.avatar_engine || '—';

        // Update ComfyUI status bar in Characters tab
        updateComfyUIStatus(data.comfyui);

        showToast('Connected to AI Character Studio', 'success');
    } catch {
        state.connected = false;
        const dot = $('.status-dot');
        const text = $('.status-text');
        dot.className = 'status-dot offline';
        text.textContent = 'Disconnected';
    }
}

// ── Load Variations ────────────────────────────────────────────
async function loadVariations() {
    try {
        const data = await apiCall('/api/discovery/variations');

        // Populate Body Outfits
        const outfitContainer = $('#bodyOutfits');
        if (outfitContainer && data.body?.outfits) {
            outfitContainer.innerHTML = data.body.outfits.map(outfit => `
                <label class="checkbox-pill">
                    <input type="checkbox" value="${outfit}" checked>
                    ${outfit.charAt(0).toUpperCase() + outfit.slice(1)}
                </label>
            `).join('');
        }
    } catch (err) {
        console.warn('Could not load variations:', err);
    }
}

// ── Load Presets ───────────────────────────────────────────────
async function loadPresets() {
    await loadVariations();
    try {
        const data = await apiCall('/api/presets');
        state.presets = data;

        // Populate camera styles
        const cameraSelect = $('#cameraStyle');
        data.camera_styles.forEach(style => {
            const opt = document.createElement('option');
            opt.value = style;
            opt.textContent = style.charAt(0).toUpperCase() + style.slice(1);
            cameraSelect.appendChild(opt);
        });

        // Populate lighting styles
        const lightingSelect = $('#lightingStyle');
        data.lighting_styles.forEach(style => {
            const opt = document.createElement('option');
            opt.value = style;
            opt.textContent = style.charAt(0).toUpperCase() + style.slice(1);
            lightingSelect.appendChild(opt);
        });
    } catch {
        console.warn('Could not load presets');
    }
}

// ── Load Models ────────────────────────────────────────────────
async function loadModels() {
    try {
        const data = await apiCall('/api/models');
        state.models = data;

        // Populate LoRA select
        const loraSelect = $('#loraSelect');
        if (loraSelect) {
            data.loras.forEach(model => {
                const opt = document.createElement('option');
                opt.value = model.name;
                opt.textContent = `${model.name} (${model.size_mb} MB)`;
                loraSelect.appendChild(opt);
            });
        }

        // Update model list in system tab
        const modelList = $('#modelList');
        const allModels = [...data.loras, ...data.checkpoints];

        if (allModels.length === 0) {
            modelList.innerHTML = '<p class="empty-hint">No models found. Add .safetensors files to models/loras/</p>';
        } else {
            modelList.innerHTML = allModels.map(m => `
                <div class="model-item">
                    <span class="model-name">${m.name}</span>
                    <span class="model-size">${m.size_mb} MB</span>
                </div>
            `).join('');
        }
    } catch {
        console.warn('Could not load models');
    }
}

// ── Generate Image ─────────────────────────────────────────────
async function handleGenerateImage() {
    const btn = $('#btnGenerateImage');
    btn.disabled = true;
    btn.classList.add('loading');

    try {
        const body = {
            prompt: $('#scenePrompt').value || 'portrait photo, beautiful lighting',
            character_lora: $('#loraSelect').value || null,
            lora_weight: parseFloat($('#loraWeight').value),
            width: parseInt($('#imgWidth').value),
            height: parseInt($('#imgHeight').value),
            steps: parseInt($('#steps').value),
            cfg_scale: parseFloat($('#cfgScale').value),
            seed: parseInt($('#seed').value),
            negative_prompt: $('#negativePrompt').value || null,
            camera_style: $('#cameraStyle').value || null,
            lighting: $('#lightingStyle').value || null,
        };

        const data = await apiCall('/api/generate/image', 'POST', body);
        const status = data.result.status;
        showToast(status === 'success' ? 'Image generated!' : `Image: ${status}`, status === 'success' ? 'success' : 'info');

        // Add to gallery
        addGalleryItem({
            type: 'image',
            prompt: data.result.prompt_used,
            seed: data.result.seed,
            time: data.result.timestamp,
            status: data.result.status,
        });
    } catch (err) {
        showToast(`Generation failed: ${err.message}`, 'error');
    } finally {
        btn.disabled = false;
        btn.classList.remove('loading');
    }
}

// ── Generate Video ─────────────────────────────────────────────
async function handleGenerateVideo() {
    const btn = $('#btnGenerateVideo');
    btn.disabled = true;
    btn.classList.add('loading');

    try {
        const body = {
            source_image: 'latest_generated.png',
            prompt: $('#scenePrompt').value || '',
            frames: 16,
            fps: 8,
        };

        const data = await apiCall('/api/generate/video', 'POST', body);
        showToast(`Video generated: ${data.result.duration_seconds}s (stub)`, 'success');

        addGalleryItem({
            type: 'video',
            prompt: body.prompt,
            time: data.result.timestamp,
            status: data.result.status,
        });
    } catch (err) {
        showToast(`Video generation failed: ${err.message}`, 'error');
    } finally {
        btn.disabled = false;
        btn.classList.remove('loading');
    }
}

// ── Generate Avatar ────────────────────────────────────────────
async function handleGenerateAvatar() {
    const btn = $('#btnGenerateAvatar');
    btn.disabled = true;
    btn.classList.add('loading');

    try {
        const body = {
            face_image: 'latest_face.png',
            audio_path: 'latest_audio.wav',
            engine: 'sadtalker',
        };

        const data = await apiCall('/api/generate/avatar', 'POST', body);
        showToast('Talking avatar generated (stub)', 'success');

        addGalleryItem({
            type: 'avatar',
            prompt: 'Talking avatar',
            time: data.result.timestamp,
            status: data.result.status,
        });
    } catch (err) {
        showToast(`Avatar generation failed: ${err.message}`, 'error');
    } finally {
        btn.disabled = false;
        btn.classList.remove('loading');
    }
}

// ── Build Prompt Preview ───────────────────────────────────────
async function handleBuildPrompt() {
    try {
        const body = {
            character: $('#loraSelect').value || null,
            lora_name: $('#loraSelect').value || null,
            lora_weight: parseFloat($('#loraWeight').value),
            location: $('#scenePrompt').value || '',
            camera_style: $('#cameraStyle').value || null,
            lighting: $('#lightingStyle').value || null,
        };

        const data = await apiCall('/api/prompt/build', 'POST', body);

        $('#promptPreviewText').textContent = data.prompt;
        $('#negativePreviewText').textContent = data.negative_prompt;

        // Switch to prompt tab
        switchTab('prompt');
        showToast('Prompt preview updated', 'info');
    } catch (err) {
        showToast(`Prompt build failed: ${err.message}`, 'error');
    }
}

// ── Gallery ────────────────────────────────────────────────────
let galleryItems = [];

function addGalleryItem(item) {
    galleryItems.unshift(item);
    renderGallery();
}

function renderGallery() {
    const grid = $('#galleryGrid');

    if (galleryItems.length === 0) {
        grid.innerHTML = `
            <div class="gallery-empty">
                <div class="empty-icon">◇</div>
                <p>No outputs yet</p>
                <p class="empty-hint">Configure your character and scene, then click Generate</p>
            </div>
        `;
        return;
    }

    const typeIcons = { image: '🖼️', video: '🎥', avatar: '🗣️' };
    const typeColors = { image: '#7c3aed', video: '#22c55e', avatar: '#f59e0b' };

    grid.innerHTML = galleryItems.map((item, idx) => `
        <div class="gallery-card" style="border-left: 3px solid ${typeColors[item.type]}">
            <div style="
                aspect-ratio: 1;
                background: linear-gradient(135deg, ${typeColors[item.type]}22, ${typeColors[item.type]}08);
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 2.5rem;
            ">
                ${typeIcons[item.type]}
            </div>
            <div class="gallery-card-info">
                <div class="card-seed" style="color: ${typeColors[item.type]}">
                    ${item.type.toUpperCase()} ${item.seed ? '· Seed: ' + item.seed : ''}
                </div>
                <div class="card-time">${new Date(item.time).toLocaleTimeString()}</div>
                <div class="card-time" style="margin-top: 4px; font-size: 0.65rem; opacity: 0.7;">
                    ${item.status}
                </div>
            </div>
        </div>
    `).join('');
}

// ── Tabs ───────────────────────────────────────────────────────
function switchTab(tabName) {
    $$('.tab').forEach(t => t.classList.remove('active'));
    $$('.tab-content').forEach(c => c.classList.remove('active'));

    document.querySelector(`.tab[data-tab="${tabName}"]`).classList.add('active');
    document.getElementById(`${tabName}Content`).classList.add('active');
}

// ── LoRA Weight Slider ─────────────────────────────────────────
function setupSliders() {
    const slider = $('#loraWeight');
    const display = $('#loraWeightValue');

    slider.addEventListener('input', () => {
        display.textContent = parseFloat(slider.value).toFixed(2);
    });
}

// ── Character Management ───────────────────────────────────────

async function loadCharacters() {
    try {
        const data = await apiCall('/api/characters');
        state.characters = data.characters;
        state.activeCharacter = data.active;
        renderCharacterList();
        populateCharacterSelect();
    } catch {
        console.warn('Could not load characters');
    }
}

function populateCharacterSelect() {
    const select = $('#characterSelect');
    // Clear options except first
    while (select.options.length > 1) select.remove(1);

    state.characters.forEach(char => {
        const opt = document.createElement('option');
        opt.value = char.name;
        opt.textContent = char.name + (char.lora_path ? ' ✓' : '');
        if (char.name === state.activeCharacter) opt.selected = true;
        select.appendChild(opt);
    });
}

function renderCharacterList() {
    const list = $('#charList');
    if (!state.characters.length) {
        list.innerHTML = '<p class="empty-hint">No characters yet — create one above</p>';
        return;
    }

    list.innerHTML = state.characters.map(char => `
        <div class="char-card ${char.name === state.activeCharacter ? 'active' : ''}">
            <div class="char-card-header">
                <span class="char-name">${char.name}</span>
                <span class="char-trigger">${char.trigger_word}</span>
            </div>
            <div class="char-card-meta">
                ${char.lora_path ? '<span class="char-badge lora">LoRA</span>' : '<span class="char-badge no-lora">No LoRA</span>'}
                ${char.name === state.activeCharacter ? '<span class="char-badge active-badge">Active</span>' : ''}
            </div>
            <div class="char-card-actions">
                <button class="btn-mini" onclick="activateChar('${char.name}')">Activate</button>
                <button class="btn-mini btn-danger" onclick="deleteChar('${char.name}')">Delete</button>
            </div>
        </div>
    `).join('');
}

async function handleCreateCharacter() {
    const name = $('#newCharName').value.trim();
    const trigger = $('#newCharTrigger').value.trim();
    const desc = $('#newCharDesc').value.trim();

    if (!name || !trigger) {
        showToast('Name and trigger word are required', 'error');
        return;
    }

    try {
        await apiCall('/api/characters', 'POST', {
            name, trigger_word: trigger, description: desc,
        });
        showToast(`Character '${name}' created!`, 'success');
        $('#newCharName').value = '';
        $('#newCharTrigger').value = '';
        $('#newCharDesc').value = '';
        await loadCharacters();
    } catch (err) {
        showToast(`Failed: ${err.message}`, 'error');
    }
}

async function activateChar(name) {
    try {
        await apiCall(`/api/characters/${name}/activate`, 'POST');
        showToast(`Active character: ${name}`, 'success');
        await loadCharacters();
    } catch (err) {
        showToast(`Failed: ${err.message}`, 'error');
    }
}

async function deleteChar(name) {
    if (!confirm(`Delete character '${name}'? This cannot be undone.`)) return;
    try {
        await apiCall(`/api/characters/${name}`, 'DELETE');
        showToast(`Character '${name}' deleted`, 'info');
        await loadCharacters();
    } catch (err) {
        showToast(`Failed: ${err.message}`, 'error');
    }
}

// ── Dataset Tools ──────────────────────────────────────────────

function getSelectedCharName() {
    return $('#characterSelect').value || state.activeCharacter;
}

async function handleValidateDataset() {
    const name = getSelectedCharName();
    if (!name) { showToast('Select a character first', 'error'); return; }

    try {
        const data = await apiCall(`/api/dataset/validate?character_name=${name}`, 'POST');
        const el = $('#datasetResults');

        el.innerHTML = `
            <div class="dataset-report">
                <h4>${data.valid ? '✅ Dataset Ready' : '⚠️ Issues Found'}</h4>
                <p><strong>${data.total_images}</strong> images found</p>
                ${data.issues.length ? '<div class="issues">' + data.issues.map(i => `<p class="issue">❌ ${i}</p>`).join('') + '</div>' : ''}
                ${data.warnings.length ? '<div class="warnings">' + data.warnings.map(w => `<p class="warning">⚠️ ${w}</p>`).join('') + '</div>' : ''}
                ${data.suggestions.length ? '<div class="suggestions">' + data.suggestions.map(s => `<p class="suggestion">💡 ${s}</p>`).join('') + '</div>' : ''}
            </div>
        `;
        showToast('Dataset validated', 'success');
    } catch (err) {
        showToast(`Validation failed: ${err.message}`, 'error');
    }
}

async function handlePrepareDataset() {
    const name = getSelectedCharName();
    if (!name) { showToast('Select a character first', 'error'); return; }

    const char = state.characters.find(c => c.name === name);
    const trigger = char?.trigger_word || 'ohm_person';

    try {
        const data = await apiCall('/api/dataset/prepare', 'POST', {
            character_name: name,
            resolution: 512,
            trigger_word: trigger,
        });
        showToast(`Prepared: ${data.resize.processed} images resized, ${data.captions.created} captions created`, 'success');
    } catch (err) {
        showToast(`Preparation failed: ${err.message}`, 'error');
    }
}

async function handleGetGuide() {
    const name = getSelectedCharName();
    if (!name) { showToast('Select a character first', 'error'); return; }

    try {
        const data = await apiCall(`/api/dataset/guide/${name}`);
        const el = $('#datasetResults');
        const guide = data.guide;

        el.innerHTML = `
            <div class="dataset-report">
                <h4>📋 Photography Guide</h4>
                <p>${guide.overview}</p>
                <h5>Face Shots (${guide.face.required.count} required)</h5>
                <ul>${guide.face.required.shots.map(s => `<li>${s.shot}</li>`).join('')}</ul>
                <h5>Body Shots (${guide.body.required.count} required)</h5>
                <ul>${guide.body.required.shots.map(s => `<li>${s.shot}</li>`).join('')}</ul>
                <p class="hint-text">Full guide saved to: ${data.saved_to}</p>
            </div>
        `;
        showToast('Photography guide loaded', 'success');
    } catch (err) {
        showToast(`Failed: ${err.message}`, 'error');
    }
}

// ── ComfyUI Status ─────────────────────────────────────────────

function updateComfyUIStatus(status) {
    const dot = $('#comfyuiDot');
    const text = $('#comfyuiStatusText');
    if (!dot || !text) return;

    if (status?.connected) {
        dot.className = 'status-dot online';
        text.textContent = `ComfyUI Connected (${status.url})`;
    } else {
        dot.className = 'status-dot offline';
        text.textContent = `ComfyUI Not Connected — ${status?.error || 'Start ComfyUI on port 8188'}`;
    }
}

async function checkComfyUI() {
    try {
        const data = await apiCall('/api/comfyui/status');
        updateComfyUIStatus(data);

        // Populate checkpoint dropdowns
        if (data.connected && data.checkpoints) {
            const faceCP = $('#faceCheckpoint');
            if (faceCP && faceCP.options.length <= 1) {
                data.checkpoints.forEach(cp => {
                    const opt = document.createElement('option');
                    opt.value = cp;
                    opt.textContent = cp;
                    faceCP.appendChild(opt);
                });
            }
        }

        // Populate LoRA dropdowns for body
        if (data.connected && data.loras) {
            const bodyLora = $('#bodyLoraName');
            if (bodyLora && bodyLora.options.length <= 1) {
                data.loras.forEach(l => {
                    const opt = document.createElement('option');
                    opt.value = l;
                    opt.textContent = l;
                    bodyLora.appendChild(opt);
                });
            }
        }
    } catch {
        updateComfyUIStatus(null);
    }
}

// ── Face Discovery ─────────────────────────────────────────────

async function handleRunFaceDiscovery() {
    const name = getSelectedCharName();
    if (!name) { showToast('Select a character first', 'error'); return; }

    const char = state.characters.find(c => c.name === name);
    const btn = $('#btnRunFaceDiscovery');
    btn.disabled = true;
    btn.textContent = '⏳ Generating...';

    try {
        const data = await apiCall('/api/discovery/face', 'POST', {
            character_name: name,
            base_description: char?.description || 'a person',
            checkpoint: $('#faceCheckpoint').value || '',
            lora_trigger: char?.trigger_word || '',
            steps: parseInt($('#faceSteps').value),
            cfg_scale: parseFloat($('#faceCfg').value),
        });

        showToast(`Generated ${data.generated}/${data.total} face images`, 'success');
        renderDiscoveryGrid('faceGrid', data.results, 'face');
        $('#faceSelectionActions').style.display = 'block';
    } catch (err) {
        showToast(`Face discovery failed: ${err.message}`, 'error');
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<span class="btn-icon">🎭</span> Generate Face Variations';
    }
}

async function handleLoadFaceResults() {
    const name = getSelectedCharName();
    if (!name) { showToast('Select a character first', 'error'); return; }

    try {
        const data = await apiCall(`/api/discovery/face/${name}`);
        if (data.found) {
            renderDiscoveryGrid('faceGrid', data.manifest.results, 'face');
            $('#faceSelectionActions').style.display = 'block';
            showToast(`Loaded ${data.manifest.results.length} face results`, 'info');
        } else {
            showToast('No previous results found', 'info');
        }
    } catch (err) {
        showToast(`Load failed: ${err.message}`, 'error');
    }
}

async function handleSelectFaces() {
    const name = getSelectedCharName();
    if (!name) return;

    const selected = getSelectedIndices('faceGrid');
    if (selected.length === 0) {
        showToast('Click on images to select them first', 'error');
        return;
    }

    try {
        const data = await apiCall(`/api/discovery/face/${name}/select`, 'POST', {
            selected_indices: selected,
        });
        showToast(`✅ ${data.selected_count} face images saved to dataset`, 'success');
    } catch (err) {
        showToast(`Selection failed: ${err.message}`, 'error');
    }
}

// ── Body Consistency ───────────────────────────────────────────

async function handleRunBodyConsistency() {
    const name = getSelectedCharName();
    if (!name) { showToast('Select a character first', 'error'); return; }

    const char = state.characters.find(c => c.name === name);
    const btn = $('#btnRunBodyConsistency');
    btn.disabled = true;
    btn.textContent = '⏳ Generating...';

    try {
        const data = await apiCall('/api/discovery/body', 'POST', {
            character_name: name,
            base_description: char?.description || 'a person',
            lora_trigger: char?.trigger_word || '',
            lora_name: $('#bodyLoraName').value || '',
            width: parseInt($('#bodyWidth').value),
            height: parseInt($('#bodyHeight').value),
            outfits: Array.from($$('#bodyOutfits input:checked')).map(cb => cb.value),
            control_image_name: state.bodyConsistency.controlImage,
        });

        showToast(`Generated ${data.generated}/${data.total} body images`, 'success');
        renderDiscoveryGrid('bodyGrid', data.results, 'body');
        $('#bodySelectionActions').style.display = 'block';
    } catch (err) {
        showToast(`Body generation failed: ${err.message}`, 'error');
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<span class="btn-icon">🧍</span> Generate Body Variations';
    }
}

async function handleLoadBodyResults() {
    const name = getSelectedCharName();
    if (!name) { showToast('Select a character first', 'error'); return; }

    try {
        const data = await apiCall(`/api/discovery/body/${name}`);
        if (data.found) {
            renderDiscoveryGrid('bodyGrid', data.manifest.results, 'body');
            $('#bodySelectionActions').style.display = 'block';
            showToast(`Loaded ${data.manifest.results.length} body results`, 'info');
        } else {
            showToast('No previous results found', 'info');
        }
    } catch (err) {
        showToast(`Load failed: ${err.message}`, 'error');
    }
}

async function handleSelectBodies() {
    const name = getSelectedCharName();
    if (!name) return;

    const selected = getSelectedIndices('bodyGrid');
    if (selected.length === 0) {
        showToast('Click on images to select them first', 'error');
        return;
    }

    try {
        const data = await apiCall(`/api/discovery/body/${name}/select`, 'POST', {
            selected_indices: selected,
        });
        showToast(`✅ ${data.copied_files} body images added to dataset`, 'success');
    } catch (err) {
        showToast(`Selection failed: ${err.message}`, 'error');
    }
}

// ── Discovery Grid Rendering ───────────────────────────────────

function renderDiscoveryGrid(gridId, results, type) {
    const grid = $(`#${gridId}`);
    if (!results || results.length === 0) {
        grid.innerHTML = '<p class="empty-hint">No images generated yet</p>';
        return;
    }

    grid.innerHTML = results.map((r, idx) => {
        if (!r.success || !r.images?.length) {
            return `
                <div class="discovery-item failed">
                    <div class="discovery-placeholder">❌</div>
                    <div class="discovery-label">${r.label || 'error'}</div>
                </div>
            `;
        }

        const imgUrl = r.image_urls ? r.image_urls[0] : `/api/discovery/image?path=${encodeURIComponent(r.images[0])}`;
        const tags = r.tags ? Object.values(r.tags).join(' · ') : r.label;

        return `
            <div class="discovery-item" data-index="${r.index}" onclick="toggleDiscoveryItem(this)">
                <img src="${imgUrl}" alt="${type} ${idx}" loading="lazy" />
                <div class="discovery-label">${tags}</div>
            </div>
        `;
    }).join('');
}

function toggleDiscoveryItem(el) {
    el.classList.toggle('selected');
}

function getSelectedIndices(gridId) {
    const items = document.querySelectorAll(`#${gridId} .discovery-item.selected`);
    return Array.from(items).map(el => parseInt(el.dataset.index));
}

// ── Training ───────────────────────────────────────────────────

async function handleGenConfig() {
    const name = getSelectedCharName();
    if (!name) { showToast('Select a character first', 'error'); return; }

    const char = state.characters.find(c => c.name === name);

    try {
        const data = await apiCall('/api/training/config', 'POST', {
            character_name: name,
            trigger_word: char?.trigger_word || 'ohm_person',
            network_rank: parseInt($('#trainRank').value),
            epochs: parseInt($('#trainEpochs').value),
            resolution: parseInt($('#trainRes').value),
            gpu_vram_gb: parseInt($('#trainVram').value),
            use_recommended: $('#trainAutoConfig').checked,
        });

        $('#trainingStatus').innerHTML = `
            <div class="train-result">
                <p>✅ Config generated</p>
                <pre class="prompt-text">${data.config_path}</pre>
            </div>
        `;
        showToast('Training config generated', 'success');
    } catch (err) {
        showToast(`Config failed: ${err.message}`, 'error');
    }
}

async function handleStartTraining() {
    const name = getSelectedCharName();
    if (!name) { showToast('Select a character first', 'error'); return; }

    const char = state.characters.find(c => c.name === name);

    try {
        const data = await apiCall('/api/training/start', 'POST', {
            character_name: name,
            trigger_word: char?.trigger_word || 'ohm_person',
            network_rank: parseInt($('#trainRank').value),
            epochs: parseInt($('#trainEpochs').value),
            resolution: parseInt($('#trainRes').value),
            gpu_vram_gb: parseInt($('#trainVram').value),
        });

        const statusEl = $('#trainingStatus');
        if (data.success) {
            statusEl.innerHTML = `
                <div class="train-result">
                    <p>🚀 Training configured!</p>
                    <p class="hint-text">${data.instructions}</p>
                    <pre class="prompt-text">${data.command}</pre>
                </div>
            `;
            showToast('Training command ready', 'success');
        } else {
            showToast(data.error || 'Training failed', 'error');
        }
    } catch (err) {
        showToast(`Training failed: ${err.message}`, 'error');
    }
}

// ── Initialize ─────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    // Tab switching
    $$('.tab').forEach(tab => {
        tab.addEventListener('click', () => switchTab(tab.dataset.tab));
    });

    // Sliders
    setupSliders();

    // Generation button handlers
    $('#btnGenerateImage').addEventListener('click', handleGenerateImage);
    $('#btnGenerateVideo').addEventListener('click', handleGenerateVideo);
    $('#btnGenerateAvatar').addEventListener('click', handleGenerateAvatar);
    $('#btnBuildPrompt').addEventListener('click', handleBuildPrompt);

    // Character handlers
    $('#btnCreateChar').addEventListener('click', handleCreateCharacter);
    $('#characterSelect').addEventListener('change', (e) => {
        if (e.target.value) activateChar(e.target.value);
    });

    // Face Discovery handlers
    $('#btnRunFaceDiscovery').addEventListener('click', handleRunFaceDiscovery);
    $('#btnLoadFaceResults').addEventListener('click', handleLoadFaceResults);
    $('#btnSelectFaces').addEventListener('click', handleSelectFaces);

    // Body Consistency handlers
    $('#btnRunBodyConsistency').addEventListener('click', handleRunBodyConsistency);
    $('#btnLoadBodyResults').addEventListener('click', handleLoadBodyResults);
    $('#btnSelectBodies').addEventListener('click', handleSelectBodies);

    // Dataset tool handlers
    $('#btnValidateDataset').addEventListener('click', handleValidateDataset);
    $('#btnPrepareDataset').addEventListener('click', handlePrepareDataset);
    $('#btnGetGuide').addEventListener('click', handleGetGuide);

    // Training handlers
    $('#btnGenConfig').addEventListener('click', handleGenConfig);
    $('#btnStartTraining').addEventListener('click', handleStartTraining);

    // Initial data load
    checkHealth();
    checkHealth();
    setupStudio();
    setupBodyConsistency();
    loadPresets();
    loadModels();
    loadCharacters();
    checkComfyUI();

    // Periodic health + ComfyUI check
    setInterval(checkHealth, 30000);
    setInterval(checkComfyUI, 30000);
});

// ── Phase 2: Content Studio ────────────────────────────────────

// State for Studio
state.studio = {
    controlImage: null, // filename on server
    ratio: '2:3',
};

function setupStudio() {
    setupModeSwitcher();
    setupDropzone();
    setupRatioSelector();

    const genBtn = $('#btnStudioGenerate');
    if (genBtn) genBtn.addEventListener('click', handleStudioGenerate);
}

function setupModeSwitcher() {
    const btns = $$('.mode-btn');
    btns.forEach(btn => {
        btn.addEventListener('click', () => {
            // Toggle buttons
            btns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            // Toggle panels
            const mode = btn.dataset.mode;
            if (mode === 'identity') {
                $('#modeIdentityControls').style.display = 'flex'; // Use flex to match CSS
                $('#modeStudioControls').style.display = 'none';
                $('#tabCharacters').style.display = 'block';
                $('#tabStudio').style.display = 'none';
                if ($('#tabStudio').classList.contains('active')) switchTab('gallery');
            } else {
                $('#modeIdentityControls').style.display = 'none';
                $('#modeStudioControls').style.display = 'flex';
                $('#tabCharacters').style.display = 'none';
                $('#tabStudio').style.display = 'block';
                // Switch to gallery or studio canvas
                switchTab('gallery');
            }
        });
    });
}

function setupDropzone() {
    const zone = $('#studioDropzone');
    const input = $('#studioRefImage');
    const preview = $('#studioRefPreview');
    const img = $('#refImg');
    const removeBtn = $('#btnRemoveRef');

    if (!zone) return;

    zone.addEventListener('click', () => input.click());

    input.addEventListener('change', (e) => {
        if (e.target.files.length) handleFile(e.target.files[0]);
    });

    zone.addEventListener('dragover', (e) => {
        e.preventDefault();
        zone.classList.add('dragover');
    });

    zone.addEventListener('dragleave', () => zone.classList.remove('dragover'));

    zone.addEventListener('drop', (e) => {
        e.preventDefault();
        zone.classList.remove('dragover');
        if (e.dataTransfer.files.length) handleFile(e.dataTransfer.files[0]);
    });

    removeBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        state.studio.controlImage = null;
        preview.style.display = 'none';
        zone.style.display = 'flex';
        input.value = '';
        $('#chkControlNet').checked = false;
    });

    async function handleFile(file) {
        // Preview
        const reader = new FileReader();
        reader.onload = (e) => {
            img.src = e.target.result;
            preview.style.display = 'block';
            zone.style.display = 'none';
        };
        reader.readAsDataURL(file);

        // Upload
        const formData = new FormData();
        formData.append('file', file);

        try {
            showToast('Uploading reference image...', 'info');
            const res = await fetch('/api/upload/image', {
                method: 'POST',
                body: formData
            });
            const data = await res.json();

            if (data.success) {
                state.studio.controlImage = data.filename;
                $('#chkControlNet').checked = true;
                showToast('Image uploaded. Pose Control enabled.', 'success');
            } else {
                throw new Error(data.detail || 'Upload failed');
            }
        } catch (err) {
            showToast(`Upload failed: ${err.message}`, 'error');
            console.error(err);
        }
    }
}

function setupRatioSelector() {
    const btns = $$('.ratio-btn');
    btns.forEach(btn => {
        btn.addEventListener('click', () => {
            btns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            state.studio.ratio = btn.dataset.ratio;
        });
    });
}

async function handleStudioGenerate() {
    const btn = $('#btnStudioGenerate');
    const prompt = $('#studioPrompt').value.trim();

    if (!prompt) {
        showToast('Please enter a prompt', 'error');
        return;
    }

    btn.disabled = true;
    const originalText = btn.innerHTML;
    btn.innerHTML = '<span class="btn-icon">✨</span> Generating...';

    // Calculate dimensions based on ratio
    let width = 512, height = 768;
    const ratio = state.studio.ratio;
    if (ratio === '9:16') { width = 512; height = 896; }
    if (ratio === '2:3') { width = 512; height = 768; }
    if (ratio === '1:1') { width = 512; height = 512; }
    if (ratio === '16:9') { width = 768; height = 432; }

    const body = {
        prompt: prompt,
        negative_prompt: $('#studioNegative').value || 'blurry, low quality, distorted, deformed, ugly, bad anatomy',
        width: width,
        height: height,
        steps: 25,
        cfg_scale: 7.0,
        seed: -1,
        // Reuse identity if selected
        checkpoint: $('#faceCheckpoint')?.value || '',
        lora_name: $('#loraSelect')?.value || '',
        lora_strength: parseFloat($('#loraWeight')?.value || 0.8),

        use_hires_fix: $('#chkHiresFix').checked,
        controlnet_enabled: $('#chkControlNet').checked,
        control_image_name: state.studio.controlImage,
        controlnet_name: 'control_v11p_sd15_openpose.pth'
    };

    try {
        const data = await apiCall('/api/studio/generate', 'POST', body);

        if (data.success) {
            showToast('Generation complete!', 'success');
            addGalleryItem({
                type: 'image',
                prompt: data.result.prompt_used || prompt,
                seed: data.result.seed,
                time: data.result.timestamp || new Date().toISOString(),
                status: 'success',
            });
            // Ideally trigger gallery refresh or load image
            // For now, gallery card appears. User sees 1 output in gallery.
        }
    } catch (err) {
        showToast(`Generation failed: ${err.message}`, 'error');
    } finally {
        btn.disabled = false;
        btn.innerHTML = originalText;
    }
}


function setupBodyConsistency() {
    setupBodyDropzone();
}

function setupBodyDropzone() {
    const zone = $('#bodyDropzone');
    const input = $('#bodyRefImage');
    const preview = $('#bodyRefPreview');
    const img = $('#bodyRefImg');
    const removeBtn = $('#btnRemoveBodyRef');

    if (!zone) return;

    zone.addEventListener('click', () => input.click());

    input.addEventListener('change', (e) => {
        if (e.target.files.length) handleBodyFile(e.target.files[0]);
    });

    zone.addEventListener('dragover', (e) => {
        e.preventDefault();
        zone.classList.add('dragover');
    });

    zone.addEventListener('dragleave', () => zone.classList.remove('dragover'));

    zone.addEventListener('drop', (e) => {
        e.preventDefault();
        zone.classList.remove('dragover');
        if (e.dataTransfer.files.length) handleBodyFile(e.dataTransfer.files[0]);
    });

    removeBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        state.bodyConsistency.controlImage = null;
        preview.style.display = 'none';
        zone.style.display = 'flex';
        input.value = '';
    });

    async function handleBodyFile(file) {
        // Preview
        const reader = new FileReader();
        reader.onload = (e) => {
            img.src = e.target.result;
            preview.style.display = 'block';
            zone.style.display = 'none';
        };
        reader.readAsDataURL(file);

        // Upload
        const formData = new FormData();
        formData.append('file', file);

        try {
            showToast('Uploading reference image...', 'info');
            const res = await fetch('/api/upload/image', {
                method: 'POST',
                body: formData
            });
            const data = await res.json();

            if (data.success) {
                state.bodyConsistency.controlImage = data.filename;
                showToast('Reference image ready', 'success');
            } else {
                throw new Error(data.detail || 'Upload failed');
            }
        } catch (err) {
            showToast(`Upload failed: ${err.message}`, 'error');
            console.error(err);
        }
    }
}
