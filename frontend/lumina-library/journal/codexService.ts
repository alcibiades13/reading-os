
import { JournalEntry, Manuscript, Mood } from '../types';

const JOURNAL_KEY = 'vellux_journal';
const MANUSCRIPT_KEY = 'vellux_manuscripts';

export const getJournalEntries = (): JournalEntry[] => {
  const stored = localStorage.getItem(JOURNAL_KEY);
  if (!stored) return [
    {
      id: 'j-1',
      date: new Date().toISOString(),
      title: 'Morning Reflections on Aurelius',
      content: 'Today I woke up thinking about the concept of the Inner Citadel. It seems more relevant than ever in this digital chaos...',
      mood: 'contemplative',
      tags: ['stoicism', 'morning'],
      isLocked: false
    }
  ];
  return JSON.parse(stored);
};

export const saveJournalEntry = (entry: Partial<JournalEntry>): JournalEntry => {
  const entries = getJournalEntries();
  const newEntry = {
    id: entry.id || Math.random().toString(36).substr(2, 9),
    date: entry.date || new Date().toISOString(),
    title: entry.title || 'Untitled Reflection',
    content: entry.content || '',
    mood: entry.mood || 'serene',
    tags: entry.tags || [],
    isLocked: entry.isLocked || false
  } as JournalEntry;

  const existingIndex = entries.findIndex(e => e.id === newEntry.id);
  if (existingIndex > -1) {
    entries[existingIndex] = newEntry;
  } else {
    entries.unshift(newEntry);
  }

  localStorage.setItem(JOURNAL_KEY, JSON.stringify(entries));
  return newEntry;
};

export const getManuscripts = (): Manuscript[] => {
  const stored = localStorage.getItem(MANUSCRIPT_KEY);
  if (!stored) return [
    {
      id: 'm-1',
      title: 'The Silent Library',
      subtitle: 'A journey through forgotten knowledge',
      genre: 'Speculative Fiction',
      coverColor: '#6366f1',
      targetWordCount: 50000,
      currentWordCount: 12400,
      chapters: [
        { id: 'ch-1', title: 'The Threshold', content: 'It started with a whisper in the stacks...', wordCount: 2200, order: 1, lastEdited: new Date().toISOString() },
        { id: 'ch-2', title: 'Dust and Echoes', content: 'The air was thick with the scent of old parchment...', wordCount: 1800, order: 2, lastEdited: new Date().toISOString() }
      ]
    }
  ];
  return JSON.parse(stored);
};

export const saveManuscript = (manuscript: Manuscript): void => {
  const manuscripts = getManuscripts();
  const idx = manuscripts.findIndex(m => m.id === manuscript.id);
  if (idx > -1) manuscripts[idx] = manuscript;
  else manuscripts.push(manuscript);
  localStorage.setItem(MANUSCRIPT_KEY, JSON.stringify(manuscripts));
};
