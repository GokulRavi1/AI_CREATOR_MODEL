import { useState, useEffect, useCallback } from 'react';
import api from '../api';
import { useApp } from '../context/AppContext';

export function useCharacters() {
    const { addToast } = useApp();
    const [characters, setCharacters] = useState([]);
    const [activeCharacter, setActiveCharacter] = useState(null);
    const [loading, setLoading] = useState(false);

    const fetchCharacters = useCallback(async () => {
        setLoading(true);
        try {
            const res = await api.get('/characters');
            setCharacters(res.data.characters || []);
            const activeName = res.data.active;
            const active = (res.data.characters || []).find(c => c.name === activeName) || (res.data.characters || [])[0];
            setActiveCharacter(active);
        } catch (err) {
            console.error("Failed to fetch characters:", err);
        } finally {
            setLoading(false);
        }
    }, []);

    const selectCharacter = useCallback(async (char) => {
        setActiveCharacter(char);
        try {
            await api.post(`/characters/${char.name}/activate`);
        } catch (err) {
            console.error("Failed to activate character:", err);
        }
    }, []);

    const createCharacter = useCallback(async (name, trigger_word, description) => {
        if (!name || !trigger_word) {
            addToast('Name and trigger word are required', 'error');
            return false;
        }
        try {
            await api.post('/characters', { name, trigger_word, description });
            addToast(`Character '${name}' created!`, 'success');
            await fetchCharacters();
            return true;
        } catch (err) {
            addToast(`Failed to create character: ${err.response?.data?.detail || err.message}`, 'error');
            return false;
        }
    }, [addToast, fetchCharacters]);

    const deleteCharacter = useCallback(async (name) => {
        try {
            await api.delete(`/characters/${name}`);
            addToast(`Character '${name}' deleted`, 'info');
            await fetchCharacters();
            return true;
        } catch (err) {
            addToast(`Failed to delete character: ${err.response?.data?.detail || err.message}`, 'error');
            return false;
        }
    }, [addToast, fetchCharacters]);

    useEffect(() => {
        fetchCharacters();
    }, [fetchCharacters]);

    return { characters, activeCharacter, selectCharacter, createCharacter, deleteCharacter, refresh: fetchCharacters, loading };
}
