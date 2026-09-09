import { useState, useMemo, useCallback } from 'react';
import { DISCOURSE_DATA } from '../data/discourses';

/**
 * useDiscourseSearch
 * Fast in-memory keyword & category filter across transcripts, titles, and tags,
 * plus keyboard arrow navigation.
 */
export function useDiscourseSearch() {
  const [query, setQuery] = useState('');
  const [activeCategory, setActiveCategory] = useState('All');
  const [selectedIndex, setSelectedIndex] = useState(0);

  // In-Memory Normalized Filtering
  const filteredResults = useMemo(() => {
    const q = query.trim().toLowerCase();

    return DISCOURSE_DATA.filter((item) => {
      // Category check
      const matchesCategory =
        activeCategory === 'All' || item.category === activeCategory;
      if (!matchesCategory) return false;

      if (!q) return true;

      // Full text search across both languages & tags
      const inTitleHi = item.titleHindi.toLowerCase().includes(q);
      const inTitleEn = item.titleEnglish.toLowerCase().includes(q);
      const inSnippetHi = item.snippetHindi.toLowerCase().includes(q);
      const inSnippetEn = item.snippetEnglish.toLowerCase().includes(q);
      const inTags = item.tags.some((t) => t.toLowerCase().includes(q));

      return inTitleHi || inTitleEn || inSnippetHi || inSnippetEn || inTags;
    });
  }, [query, activeCategory]);

  // Navigate with arrows
  const handleKeyNavigation = useCallback(
    (e, onSelect) => {
      if (filteredResults.length === 0) return;

      if (e.key === 'ArrowDown') {
        e.preventDefault();
        setSelectedIndex((prev) => (prev + 1) % filteredResults.length);
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        setSelectedIndex(
          (prev) => (prev - 1 + filteredResults.length) % filteredResults.length
        );
      } else if (e.key === 'Enter') {
        e.preventDefault();
        if (filteredResults[selectedIndex] && onSelect) {
          onSelect(filteredResults[selectedIndex]);
        }
      }
    },
    [filteredResults, selectedIndex]
  );

  return {
    query,
    setQuery,
    activeCategory,
    setActiveCategory,
    filteredResults,
    selectedIndex,
    setSelectedIndex,
    handleKeyNavigation
  };
}
