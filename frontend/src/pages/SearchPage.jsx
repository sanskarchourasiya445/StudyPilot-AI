import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, FileText, Video, MessageSquare, BookOpen, Layers, ArrowRight, Loader2, Sparkles } from 'lucide-react';
import { useResources } from '../hooks/useResources';
import { useConversations } from '../hooks/useConversations';
import { searchApi } from '../services/searchApi';
import { AppLayout } from '../components/layout/AppLayout';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Badge } from '../components/ui/Badge';

export function SearchPage() {
  const navigate = useNavigate();
  const { data: resources = [] } = useResources();
  const { data: conversations = [] } = useConversations();

  const [query, setQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('all'); // 'all' | 'materials' | 'threads' | 'deep'
  const [selectedResourceId, setSelectedResourceId] = useState('');
  const [deepResults, setDeepResults] = useState([]);
  const [isDeepSearching, setIsDeepSearching] = useState(false);

  const filteredMaterials = resources.filter(
    (r) =>
      !query ||
      (r.title || '').toLowerCase().includes(query.toLowerCase()) ||
      (r.source || '').toLowerCase().includes(query.toLowerCase())
  );

  const filteredConversations = conversations.filter(
    (c) => !query || (c.title || '').toLowerCase().includes(query.toLowerCase())
  );

  const handleDeepVectorSearch = async (e) => {
    e?.preventDefault();
    if (!query.trim() || !selectedResourceId) return;
    setIsDeepSearching(true);
    try {
      const results = await searchApi.searchResourceChunks(selectedResourceId, query.trim());
      setDeepResults(results || []);
      setSelectedCategory('deep');
    } catch (err) {
      setDeepResults([]);
    } finally {
      setIsDeepSearching(false);
    }
  };

  return (
    <AppLayout title="Search Workspace">
      {/* Search Header Banner */}
      <div className="mb-6">
        <h2 className="text-xl font-bold text-[#f5f7fa]">Study Materials Search</h2>
        <p className="text-xs text-[#9ca8ba] mt-0.5">
          Filter study materials, saved chat threads, or perform deep RAG vector chunk search.
        </p>
      </div>

      {/* Main Search Controls Card */}
      <Card className="mb-6 space-y-4">
        <div className="flex flex-col md:flex-row items-center gap-3">
          <div className="w-full md:flex-1">
            <Input
              type="text"
              placeholder="Search by topic, document title, or question..."
              icon={Search}
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
          </div>

          <div className="w-full md:w-64 flex items-center gap-2">
            <select
              value={selectedResourceId}
              onChange={(e) => setSelectedResourceId(e.target.value)}
              className="w-full bg-[#0a0f18] border border-white/[0.08] text-[#f5f7fa] text-xs rounded-xl p-2.5 font-semibold focus:outline-none focus:border-blue-500"
            >
              <option value="">Deep Vector Target...</option>
              {resources.map((r, idx) => {
                const resId = r.resource_id || r.id || `res-${idx}`;
                return (
                  <option key={resId} value={resId}>
                    {r.source_type === 'pdf' ? '📄' : '🎥'} {r.title || r.source}
                  </option>
                );
              })}
            </select>
            {selectedResourceId && (
              <Button
                variant="primary"
                size="sm"
                icon={Sparkles}
                onClick={handleDeepVectorSearch}
                isLoading={isDeepSearching}
                className="shrink-0"
              >
                Deep RAG Search
              </Button>
            )}
          </div>
        </div>

        {/* Filter Category Tabs */}
        <div className="flex border-b border-white/[0.07] pt-2 gap-4 text-xs font-semibold">
          <button
            onClick={() => setSelectedCategory('all')}
            className={`pb-2 border-b-2 transition-colors ${
              selectedCategory === 'all'
                ? 'border-blue-500 text-blue-400'
                : 'border-transparent text-slate-400 hover:text-white'
            }`}
          >
            All Results ({filteredMaterials.length + filteredConversations.length})
          </button>

          <button
            onClick={() => setSelectedCategory('materials')}
            className={`pb-2 border-b-2 transition-colors ${
              selectedCategory === 'materials'
                ? 'border-blue-500 text-blue-400'
                : 'border-transparent text-slate-400 hover:text-white'
            }`}
          >
            Materials ({filteredMaterials.length})
          </button>

          <button
            onClick={() => setSelectedCategory('threads')}
            className={`pb-2 border-b-2 transition-colors ${
              selectedCategory === 'threads'
                ? 'border-blue-500 text-blue-400'
                : 'border-transparent text-slate-400 hover:text-white'
            }`}
          >
            Saved Threads ({filteredConversations.length})
          </button>

          {deepResults.length > 0 && (
            <button
              onClick={() => setSelectedCategory('deep')}
              className={`pb-2 border-b-2 transition-colors ${
                selectedCategory === 'deep'
                  ? 'border-blue-500 text-blue-400'
                  : 'border-transparent text-slate-400 hover:text-white'
              }`}
            >
              Deep Vector Chunks ({deepResults.length})
            </button>
          )}
        </div>
      </Card>

      {/* Results Rendering */}
      {selectedCategory === 'deep' && deepResults.length > 0 ? (
        <div className="space-y-4">
          <h3 className="text-sm font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-teal-500" />
            <span>Retrieved RAG Vector Chunks ({deepResults.length})</span>
          </h3>
          {deepResults.map((chunk, idx) => (
            <Card key={chunk.id || `chunk-${idx}`} className="border-l-4 border-l-teal-500">
              <div className="flex items-center justify-between gap-2 mb-2">
                <span className="text-xs font-bold text-slate-900 dark:text-slate-100">
                  Chunk #{idx + 1}
                </span>
                {chunk.score && (
                  <Badge variant="teal">{(chunk.score * 100).toFixed(0)}% relevance match</Badge>
                )}
              </div>
              <p className="text-xs text-slate-700 dark:text-slate-300 leading-relaxed whitespace-pre-wrap">
                "{chunk.text || chunk.content}"
              </p>
            </Card>
          ))}
        </div>
      ) : (
        <div className="space-y-6">
          {/* Materials Section */}
          {(selectedCategory === 'all' || selectedCategory === 'materials') && (
            <div>
              <h3 className="text-sm font-bold text-[#f5f7fa] mb-3 flex items-center gap-2">
                <FileText className="w-4 h-4 text-blue-400" />
                <span>Study Materials ({filteredMaterials.length})</span>
              </h3>
              {filteredMaterials.length === 0 ? (
                <p className="text-xs text-slate-500">No matching study materials found.</p>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {filteredMaterials.map((r, idx) => {
                    const resKey = r.resource_id || r.id || `mat-${idx}`;
                    return (
                      <Card
                        key={resKey}
                        hoverable
                        onClick={() => navigate(`/resources/${r.resource_id || r.id}`)}
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2.5 min-w-0">
                            <div className="w-8 h-8 rounded-lg bg-blue-600/10 text-blue-400 border border-blue-500/20 flex items-center justify-center shrink-0">
                              <FileText className="w-4 h-4" />
                            </div>
                            <span className="text-xs font-bold text-[#f5f7fa] truncate">
                              {r.title || r.source}
                            </span>
                          </div>
                          <ArrowRight className="w-4 h-4 text-slate-400 shrink-0" />
                        </div>
                      </Card>
                    );
                  })}
                </div>
              )}
            </div>
          )}

          {/* Conversations Section */}
          {(selectedCategory === 'all' || selectedCategory === 'threads') && (
            <div>
              <h3 className="text-sm font-bold text-[#f5f7fa] mb-3 flex items-center gap-2">
                <MessageSquare className="w-4 h-4 text-blue-400" />
                <span>Saved Chat Threads ({filteredConversations.length})</span>
              </h3>
              {filteredConversations.length === 0 ? (
                <p className="text-xs text-slate-500">No matching conversation threads found.</p>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {filteredConversations.map((c, idx) => {
                    const convKey = c.conversation_id || c.id || `conv-${idx}`;
                    return (
                      <Card
                        key={convKey}
                        hoverable
                        onClick={() => navigate(`/workspace?conversation_id=${c.conversation_id || c.id}`)}
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2.5 min-w-0">
                            <div className="w-8 h-8 rounded-lg bg-blue-600/10 text-blue-400 border border-blue-500/20 flex items-center justify-center shrink-0">
                              <MessageSquare className="w-4 h-4" />
                            </div>
                            <span className="text-xs font-bold text-[#f5f7fa] truncate">
                              {c.title || 'Untitled Conversation'}
                            </span>
                          </div>
                          <ArrowRight className="w-4 h-4 text-slate-400 shrink-0" />
                        </div>
                      </Card>
                    );
                  })}
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </AppLayout>
  );
}
