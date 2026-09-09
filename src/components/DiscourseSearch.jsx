import React, { useRef, useEffect } from 'react';
import { Search, X, CornerDownLeft, ArrowUp, ArrowDown, BookOpen, Clock, Tag } from 'lucide-react';
import { CATEGORIES } from '../data/discourses';
import { useDiscourseSearch } from '../hooks/useDiscourseSearch';

/**
 * DiscourseSearch
 * 21st.dev-inspired Command Palette (Cmd + K) dialog.
 * Instantaneous in-memory filtering across discourses, category chip selection,
 * keyboard navigation, and match highlights.
 */
export default function DiscourseSearch({
  isOpen,
  onClose,
  searchState,
  onSelectDiscourse
}) {
  const fallbackSearchState = useDiscourseSearch();
  const activeState = searchState || fallbackSearchState;
  const {
    query,
    setQuery,
    activeCategory,
    setActiveCategory,
    filteredResults,
    selectedIndex,
    setSelectedIndex,
    handleKeyNavigation
  } = activeState;

  const inputRef = useRef(null);
  const listRef = useRef(null);

  // Auto-focus input on modal open
  useEffect(() => {
    if (isOpen) {
      setTimeout(() => {
        if (inputRef.current) inputRef.current.focus();
      }, 50);
    } else {
      setQuery('');
      setSelectedIndex(0);
    }
  }, [isOpen, setQuery, setSelectedIndex]);

  // Keep selected item visible during arrow navigation
  useEffect(() => {
    if (listRef.current && listRef.current.children[selectedIndex]) {
      listRef.current.children[selectedIndex].scrollIntoView({
        block: 'nearest'
      });
    }
  }, [selectedIndex]);

  if (!isOpen) return null;

  // Helper to highlight matching text
  const highlightMatch = (text, q) => {
    if (!q || !text) return text;
    const regex = new RegExp(`(${q.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
    const parts = text.split(regex);
    return parts.map((part, i) =>
      regex.test(part) ? (
        <mark
          key={i}
          style={{
            backgroundColor: 'var(--color-yellow-soft)',
            color: 'var(--color-saffron-primary)',
            padding: '1px 3px',
            borderRadius: '2px',
            fontWeight: 600
          }}
        >
          {part}
        </mark>
      ) : (
        part
      )
    );
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-start justify-center pt-16 sm:pt-24 px-4 bg-black/60 backdrop-blur-sm transition-opacity"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
      role="dialog"
      aria-modal="true"
      aria-label="सत्संग खोज / Command Palette"
    >
      <div
        className="w-full max-w-[640px] bg-white rounded-lg border border-[var(--color-border-hairline)] shadow-2xl overflow-hidden flex flex-col max-h-[82vh] animate-in fade-in zoom-in-95 duration-150"
        onKeyDown={(e) => handleKeyNavigation(e, onSelectDiscourse)}
      >
        {/* Top Input Bar */}
        <div className="flex items-center px-4 h-14 border-b border-[var(--color-border-hairline)] bg-[var(--color-bg-surface)]">
          <Search className="w-5 h-5 text-[var(--color-text-muted)] mr-3 flex-shrink-0" />
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setSelectedIndex(0);
            }}
            placeholder="प्रवचन, संशय, अथवा विषय खोजें... (उदा: काम वासना, नाम जप)"
            className="w-full h-full bg-transparent border-none outline-none text-base text-[var(--color-text-primary)] placeholder:text-[var(--color-text-muted)] font-devanagari"
          />
          {query && (
            <button
              onClick={() => {
                setQuery('');
                if (inputRef.current) inputRef.current.focus();
              }}
              className="p-1 hover:bg-stone-100 rounded text-stone-400 hover:text-stone-700 transition-colors mr-2 cursor-pointer"
            >
              <X className="w-4 h-4" />
            </button>
          )}
          <button
            onClick={onClose}
            className="px-2 py-1 rounded bg-[var(--color-bg-subtle)] text-[11px] font-mono text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] transition-colors cursor-pointer"
          >
            ESC
          </button>
        </div>

        {/* Category Filter Chips */}
        <div className="flex items-center gap-1.5 px-4 py-2.5 bg-[var(--color-bg-base)] border-b border-[var(--color-border-hairline)] overflow-x-auto no-scrollbar">
          {CATEGORIES.map((cat) => {
            const isActive = activeCategory === cat;
            return (
              <button
                key={cat}
                onClick={() => {
                  setActiveCategory(cat);
                  setSelectedIndex(0);
                  if (inputRef.current) inputRef.current.focus();
                }}
                className={`px-3 py-1 text-xs rounded-full font-medium transition-colors cursor-pointer flex-shrink-0 ${
                  isActive
                    ? 'bg-[var(--color-saffron-primary)] text-white shadow-sm'
                    : 'bg-white text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] border border-[var(--color-border-hairline)]'
                }`}
              >
                {cat}
              </button>
            );
          })}
        </div>

        {/* Results List */}
        <div
          ref={listRef}
          className="flex-1 overflow-y-auto divide-y divide-[var(--color-border-hairline)] p-2"
        >
          {filteredResults.length > 0 ? (
            filteredResults.map((item, idx) => {
              const isSelected = idx === selectedIndex;
              return (
                <div
                  key={item.id}
                  onClick={() => onSelectDiscourse(item)}
                  onMouseEnter={() => setSelectedIndex(idx)}
                  className={`p-3.5 rounded transition-colors cursor-pointer ${
                    isSelected ? 'search-result-active' : 'hover:bg-[var(--color-bg-subtle)]'
                  }`}
                  role="option"
                  aria-selected={isSelected}
                >
                  <div className="flex items-start justify-between gap-3 mb-1">
                    <div className="flex items-center gap-2">
                      <span className="w-1.5 h-1.5 rounded-full bg-[var(--color-saffron-primary)]" />
                      <h4 className="font-semibold text-sm text-[var(--color-navy-shyam)] font-devanagari">
                        {highlightMatch(item.titleHindi, query)}
                      </h4>
                    </div>
                    <span className="text-[11px] font-mono text-[var(--color-text-muted)] flex items-center gap-1 flex-shrink-0">
                      <Clock className="w-3 h-3" /> {item.duration}
                    </span>
                  </div>

                  <p className="text-xs text-[var(--color-text-muted)] line-clamp-2 leading-relaxed mb-2 font-devanagari pl-3.5">
                    {highlightMatch(item.snippetHindi, query)}
                  </p>

                  <div className="flex flex-wrap items-center justify-between gap-2 pl-3.5 pt-1">
                    <div className="flex flex-wrap items-center gap-1.5">
                      <span className="text-[10px] font-mono uppercase bg-[var(--color-bg-subtle)] text-[var(--color-text-muted)] px-2 py-0.5 rounded">
                        {item.category}
                      </span>
                      {item.tags.slice(0, 3).map((tag, tIdx) => (
                        <span
                          key={tIdx}
                          className="text-[10px] font-devanagari text-[var(--color-text-muted)]"
                        >
                          #{tag}
                        </span>
                      ))}
                    </div>

                    {isSelected && (
                      <span className="text-[11px] font-mono text-[var(--color-saffron-primary)] flex items-center gap-1">
                        चुनें <CornerDownLeft className="w-3 h-3" />
                      </span>
                    )}
                  </div>
                </div>
              );
            })
          ) : (
            <div className="py-12 text-center text-[var(--color-text-muted)]">
              <BookOpen className="w-8 h-8 mx-auto mb-2 text-stone-400" />
              <p className="text-sm font-devanagari">
                कोई प्रवचन उपलब्ध नहीं हुआ: “{query}”
              </p>
              <p className="text-xs text-stone-400 mt-1">
                अन्य श्रेणी अथवा दूसरा शब्द लिखकर पुनः प्रयास करें।
              </p>
            </div>
          )}
        </div>

        {/* Footer Shortcut Bar */}
        <div className="px-4 py-2.5 bg-[var(--color-bg-base)] border-t border-[var(--color-border-hairline)] flex items-center justify-between text-[11px] font-mono text-[var(--color-text-muted)]">
          <div className="flex items-center gap-3">
            <span className="flex items-center gap-1">
              <ArrowUp className="w-3 h-3" />
              <ArrowDown className="w-3 h-3" /> नेविगेट
            </span>
            <span className="flex items-center gap-1">
              <CornerDownLeft className="w-3 h-3" /> खोलें
            </span>
          </div>
          <span>
            {filteredResults.length} परिणाम उपलब्ध • 21st.dev Index
          </span>
        </div>
      </div>
    </div>
  );
}
