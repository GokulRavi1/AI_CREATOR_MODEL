import { useState, useEffect } from 'react';
import api from '../../api';
import { Loader2, Calendar, Copy, RotateCcw, Filter, Image as ImageIcon } from 'lucide-react';
import { useApp } from '../../context/AppContext';

export default function HistoryPanel() {
    const { addToast } = useApp();
    const [history, setHistory] = useState([]);
    const [loading, setLoading] = useState(true);
    const [page, setPage] = useState(0);
    const [hasMore, setHasMore] = useState(true);
    const [category, setCategory] = useState('');
    const [selectedImage, setSelectedImage] = useState(null);

    const fetchHistory = async (pageNum, reset = false) => {
        try {
            setLoading(true);
            const limit = 20;
            const offset = pageNum * limit;

            const params = { limit, offset };
            if (category) params.category = category;

            const res = await api.get('/history', { params });

            if (reset) {
                setHistory(res.data.items);
            } else {
                setHistory(prev => [...prev, ...res.data.items]);
            }

            setHasMore(res.data.items.length === limit);
            setLoading(false);
        } catch (err) {
            console.error(err);
            addToast('Failed to load history', 'error');
            setLoading(false);
        }
    };

    useEffect(() => {
        setPage(0);
        fetchHistory(0, true);
    }, [category]);

    const loadMore = () => {
        const nextPage = page + 1;
        setPage(nextPage);
        fetchHistory(nextPage, false);
    };

    const copyPrompt = (text) => {
        navigator.clipboard.writeText(text);
        addToast('Prompt copied!', 'success');
    };

    return (
        <div className="h-full flex flex-col p-6 animate-fade-in">
            <div className="flex justify-between items-center mb-6">
                <div>
                    <h1 className="text-2xl font-bold text-white flex items-center gap-2">
                        <Calendar className="text-[var(--accent-primary)]" />
                        Generation History
                    </h1>
                    <p className="text-[var(--text-secondary)]">Browse your past creations and reuse successful prompts</p>
                </div>

                <div className="flex gap-2">
                    {['', 'face_discovery', 'body_consistency'].map(cat => (
                        <button
                            key={cat}
                            onClick={() => setCategory(cat)}
                            className={`px-4 py-2 rounded-full text-sm font-medium transition-all ${category === cat
                                ? 'bg-[var(--accent-primary)] text-white'
                                : 'bg-[var(--bg-tertiary)] text-[var(--text-secondary)] hover:bg-[var(--bg-secondary)]'
                                }`}
                        >
                            {cat === '' ? 'All Items' : cat.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                        </button>
                    ))}
                </div>
            </div>

            <div className="flex-1 overflow-y-auto pr-2 custom-scrollbar">
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
                    {history.map((item) => (
                        <div
                            key={item.id}
                            onClick={() => setSelectedImage(item)}
                            className="group relative aspect-[2/3] rounded-xl overflow-hidden cursor-pointer bg-[var(--bg-secondary)] border border-[var(--border-color)] hover:border-[var(--accent-primary)] transition-all"
                        >
                            <img
                                src={`/api/dataset/image?path=${encodeURIComponent(item.image_path)}`}
                                alt={item.prompt}
                                className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110"
                                onError={(e) => {
                                    // Fallback if generic image endpoint doesn't work (using raw api/view if needed)
                                    e.target.src = `/api/view?path=${encodeURIComponent(item.image_path)}`;
                                }}
                            />

                            <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity flex flex-col justify-end p-3">
                                <div className="text-xs text-white font-medium truncate">
                                    {item.prompt}
                                </div>
                                <div className="flex justify-between items-center mt-2">
                                    <span className="text-[10px] text-gray-300 uppercase tracking-wider bg-black/40 px-1.5 py-0.5 rounded">
                                        {item.category?.replace('_', ' ') || 'IMG'}
                                    </span>
                                    <span className="text-[10px] text-gray-400">
                                        {new Date(item.created_at).toLocaleDateString()}
                                    </span>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>

                {loading && (
                    <div className="flex justify-center p-8">
                        <Loader2 className="animate-spin text-[var(--accent-primary)]" size={32} />
                    </div>
                )}

                {!loading && hasMore && (
                    <div className="flex justify-center p-8">
                        <button
                            onClick={loadMore}
                            className="btn btn-secondary"
                        >
                            Load More
                        </button>
                    </div>
                )}

                {!loading && history.length === 0 && (
                    <div className="flex flex-col items-center justify-center py-20 text-[var(--text-tertiary)]">
                        <ImageIcon size={48} className="mb-4 opacity-50" />
                        <p>No history found. Start generating images!</p>
                    </div>
                )}
            </div>

            {/* Modal for Details */}
            {selectedImage && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fade-in"
                    onClick={() => setSelectedImage(null)}>
                    <div className="bg-[var(--bg-secondary)] w-full max-w-4xl max-h-[90vh] rounded-2xl overflow-hidden flex shadow-2xl border border-[var(--border-color)]"
                        onClick={e => e.stopPropagation()}>

                        <div className="w-1/2 bg-black flex items-center justify-center">
                            <img
                                src={`/api/view?path=${encodeURIComponent(selectedImage.image_path)}`}
                                alt="Detail"
                                className="max-w-full max-h-full object-contain"
                            />
                        </div>

                        <div className="w-1/2 p-6 flex flex-col overflow-y-auto">
                            <div className="flex justify-between items-start mb-4">
                                <span className="px-2 py-1 bg-[var(--accent-primary)]/20 text-[var(--accent-primary)] text-xs rounded uppercase font-bold tracking-wider">
                                    {selectedImage.category?.replace('_', ' ')}
                                </span>
                                <button onClick={() => setSelectedImage(null)} className="text-[var(--text-tertiary)] hover:text-white">✕</button>
                            </div>

                            <div className="mb-6">
                                <label className="text-xs text-[var(--text-tertiary)] uppercase tracking-wider font-bold mb-1 block">Prompt</label>
                                <p className="text-sm text-[var(--text-primary)] bg-[var(--bg-tertiary)] p-3 rounded leading-relaxed border border-[var(--border-color)] relative group">
                                    {selectedImage.prompt}
                                    <button
                                        onClick={() => copyPrompt(selectedImage.prompt)}
                                        className="absolute top-2 right-2 p-1.5 bg-black/40 hover:bg-[var(--accent-primary)] rounded transition-colors opacity-0 group-hover:opacity-100"
                                        title="Copy Prompt"
                                    >
                                        <Copy size={12} className="text-white" />
                                    </button>
                                </p>
                            </div>

                            <div className="mb-6">
                                <label className="text-xs text-[var(--text-tertiary)] uppercase tracking-wider font-bold mb-1 block">Negative Prompt</label>
                                <p className="text-xs text-[var(--text-secondary)] bg-[var(--bg-tertiary)] p-3 rounded leading-relaxed border border-[var(--border-color)]">
                                    {selectedImage.negative_prompt || 'None'}
                                </p>
                            </div>

                            <div className="grid grid-cols-2 gap-4 mb-6">
                                <div className="bg-[var(--bg-tertiary)] p-3 rounded border border-[var(--border-color)]">
                                    <div className="text-xs text-[var(--text-tertiary)]">Steps</div>
                                    <div className="font-mono text-sm">{selectedImage.settings?.steps || 20}</div>
                                </div>
                                <div className="bg-[var(--bg-tertiary)] p-3 rounded border border-[var(--border-color)]">
                                    <div className="text-xs text-[var(--text-tertiary)]">CFG Scale</div>
                                    <div className="font-mono text-sm">{selectedImage.settings?.cfg || 7.0}</div>
                                </div>
                                <div className="bg-[var(--bg-tertiary)] p-3 rounded border border-[var(--border-color)]">
                                    <div className="text-xs text-[var(--text-tertiary)]">Seed</div>
                                    <div className="font-mono text-sm">{selectedImage.settings?.seed}</div>
                                </div>
                                <div className="bg-[var(--bg-tertiary)] p-3 rounded border border-[var(--border-color)]">
                                    <div className="text-xs text-[var(--text-tertiary)]">Model</div>
                                    <div className="font-mono text-sm truncate" title={selectedImage.settings?.model}>{selectedImage.settings?.model || 'Unknown'}</div>
                                </div>
                            </div>

                            <div className="mt-auto">
                                <button
                                    onClick={() => copyPrompt(selectedImage.prompt)}
                                    className="btn btn-primary w-full py-3 flex items-center justify-center gap-2"
                                >
                                    <RotateCcw size={16} />
                                    Copy Parameters (Remix)
                                </button>
                                <p className="text-xs text-center text-[var(--text-tertiary)] mt-2">
                                    Copies prompt to clipboard. Auto-fill coming soon.
                                </p>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
