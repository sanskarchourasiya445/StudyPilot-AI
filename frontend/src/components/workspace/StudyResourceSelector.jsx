import React, { useState, useRef, useEffect } from 'react';
import {
  ChevronDown,
  FileText,
  Video,
  Sparkles,
  Layers,
  Search,
  Check,
  X,
  CheckSquare,
  Square,
} from 'lucide-react';

export function StudyResourceSelector({
  resources = [],
  scope = { mode: 'all', resource_ids: [] },
  onChangeScope,
  // Backward compatibility fallback props
  selectedResourceId,
  onSelectResource,
}) {
  const [isOpen, setIsOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const popoverRef = useRef(null);

  // Normalize scope object
  const currentMode = scope?.mode || (selectedResourceId ? 'selected' : 'all');
  const currentResourceIds =
    scope?.resource_ids && scope.resource_ids.length > 0
      ? scope.resource_ids
      : selectedResourceId
      ? [selectedResourceId]
      : [];

  const isAllMode = currentMode === 'all';

  // Close popover when clicking outside
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (popoverRef.current && !popoverRef.current.contains(e.target)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const filteredResources = resources.filter((res) => {
    const title = res.title || res.display_source || res.source || '';
    return title.toLowerCase().includes(searchQuery.toLowerCase());
  });

  const handleSelectAllMode = () => {
    if (onChangeScope) {
      onChangeScope({ mode: 'all', resource_ids: [] });
    } else if (onSelectResource) {
      onSelectResource(null);
    }
  };

  const handleToggleResource = (resId) => {
    let newIds = [];
    if (isAllMode) {
      newIds = [resId];
    } else if (currentResourceIds.includes(resId)) {
      newIds = currentResourceIds.filter((id) => id !== resId);
    } else {
      newIds = [...currentResourceIds, resId];
    }

    if (newIds.length === 0) {
      handleSelectAllMode();
    } else {
      if (onChangeScope) {
        onChangeScope({ mode: 'selected', resource_ids: newIds });
      } else if (onSelectResource) {
        onSelectResource(newIds[0]);
      }
    }
  };

  const handleSelectAllResources = () => {
    const allIds = resources.map((r) => r.resource_id || r.id);
    if (onChangeScope) {
      onChangeScope({ mode: 'selected', resource_ids: allIds });
    }
  };

  const handleClearAll = () => {
    handleSelectAllMode();
  };

  const getCleanTitle = (res) => {
    if (!res) return 'Study Material';
    let clean = res.title || res.display_source;
    if (!clean || clean.startsWith('http://') || clean.startsWith('https://')) {
      if (res.source_type === 'youtube') clean = 'YouTube Video Lecture';
      else if (res.source) clean = res.source.split(/[/\\]/).pop();
      else clean = 'Study Material';
    }
    return clean;
  };

  // Button label formatting
  let triggerTitle = 'All Resources';
  let triggerIcon = <Layers className="w-4 h-4 text-blue-600 dark:text-blue-400" />;

  if (!isAllMode) {
    if (currentResourceIds.length === 1) {
      const singleRes = resources.find(
        (r) => (r.resource_id || r.id) === currentResourceIds[0]
      );
      triggerTitle = getCleanTitle(singleRes);
      triggerIcon =
        singleRes?.source_type === 'pdf' ? (
          <FileText className="w-4 h-4 text-blue-600 dark:text-blue-400" />
        ) : (
          <Video className="w-4 h-4 text-red-600 dark:text-red-400" />
        );
    } else if (currentResourceIds.length > 1) {
      triggerTitle = `${currentResourceIds.length} Resources Selected`;
      triggerIcon = <Sparkles className="w-4 h-4 text-teal-600 dark:text-teal-400" />;
    }
  }

  return (
    <div className="relative flex-1 max-w-sm sm:max-w-md" ref={popoverRef}>
      {/* Trigger Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between gap-2.5 p-2 px-3 rounded-xl bg-[#0d1420] border border-white/[0.08] hover:border-blue-500/60 transition-all text-left"
      >
        <div className="flex items-center gap-2.5 min-w-0 flex-1">
          <div className="w-7 h-7 rounded-lg bg-[#101827] flex items-center justify-center shrink-0 border border-white/[0.08]">
            {triggerIcon}
          </div>
          <div className="min-w-0 flex-1">
            <span className="font-bold text-xs text-[#f5f7fa] block truncate">
              {triggerTitle}
            </span>
            <span className="text-[10px] text-[#9ca8ba] font-medium block truncate -mt-0.5">
              {isAllMode
                ? 'Cross-library study active'
                : currentResourceIds.length === 1
                ? 'Single resource scope'
                : `Retrieving from ${currentResourceIds.length} selected materials`}
            </span>
          </div>
        </div>
        <ChevronDown className="w-4 h-4 text-slate-400 shrink-0" />
      </button>

      {/* Popover Menu */}
      {isOpen && (
        <div className="absolute left-0 mt-2 w-72 sm:w-80 bg-[#0d1420] rounded-2xl border border-white/[0.08] shadow-2xl p-3 z-50 animate-in fade-in zoom-in-95 duration-150">
          {/* Header Search Input */}
          <div className="relative flex items-center mb-2.5">
            <Search className="w-3.5 h-3.5 absolute left-3 text-slate-400" />
            <input
              type="text"
              placeholder="Search materials..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-[#0a0f18] border border-white/[0.08] text-xs text-[#f5f7fa] placeholder:text-slate-500 pl-8 pr-3 py-1.5 rounded-lg focus:outline-none focus:border-blue-500"
            />
          </div>

          {/* Quick Action Toolbar */}
          <div className="flex items-center justify-between pb-2 mb-2 border-b border-white/[0.06] text-[11px] font-bold">
            <button
              onClick={handleSelectAllMode}
              className={`flex items-center gap-1.5 px-2 py-1 rounded-md transition-colors ${
                isAllMode
                  ? 'bg-blue-600/20 text-blue-400 font-extrabold'
                  : 'text-[#9ca8ba] hover:text-[#f5f7fa]'
              }`}
            >
              <Layers className="w-3.5 h-3.5" />
              <span>All Resources</span>
            </button>

            <div className="flex items-center gap-2">
              <button
                onClick={handleSelectAllResources}
                className="text-blue-400 hover:underline"
              >
                Select All
              </button>
              <span className="text-white/20">•</span>
              <button
                onClick={handleClearAll}
                className="text-[#9ca8ba] hover:text-[#f5f7fa]"
              >
                Clear
              </button>
            </div>
          </div>

          {/* Checkbox List of Materials */}
          <div className="max-h-56 overflow-y-auto no-scrollbar space-y-1">
            {filteredResources.length === 0 ? (
              <p className="text-xs text-slate-400 text-center py-4">No materials found.</p>
            ) : (
              filteredResources.map((res) => {
                const resId = res.resource_id || res.id;
                const isSelected = !isAllMode && currentResourceIds.includes(resId);
                const title = getCleanTitle(res);
                const isPdf = res.source_type === 'pdf';

                return (
                  <div
                    key={resId}
                    onClick={() => handleToggleResource(resId)}
                    className={`flex items-center justify-between gap-2.5 p-2 rounded-xl text-xs cursor-pointer transition-colors ${
                      isSelected
                        ? 'bg-blue-600/15 text-blue-400 font-semibold'
                        : 'text-[#f5f7fa] hover:bg-white/[0.04]'
                    }`}
                  >
                    <div className="flex items-center gap-2 min-w-0">
                      <input
                        type="checkbox"
                        checked={isSelected}
                        onChange={() => {}} // handled by parent div
                        className="w-3.5 h-3.5 rounded text-blue-600 focus:ring-blue-500 cursor-pointer shrink-0"
                      />
                      <span className="shrink-0">
                        {isPdf ? '📄' : '🎥'}
                      </span>
                      <span className="truncate">{title}</span>
                    </div>

                    <span className="text-[10px] text-slate-400 uppercase font-mono shrink-0">
                      {res.source_type}
                    </span>
                  </div>
                );
              })
            )}
          </div>

          {/* Done / Apply Footer */}
          <div className="pt-2.5 mt-2 border-t border-white/[0.06] flex items-center justify-between text-xs">
            <span className="text-[11px] text-[#9ca8ba] font-medium">
              {isAllMode ? 'All resources active' : `${currentResourceIds.length} selected`}
            </span>
            <button
              onClick={() => setIsOpen(false)}
              className="px-3 py-1 bg-blue-600 hover:bg-blue-500 text-white font-semibold rounded-lg shadow-2xs transition-colors"
            >
              Done
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
