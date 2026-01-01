
import { StudyNote, StudyNoteType } from '../types';

const STORAGE_KEY = 'lumina_study_notes';

export const getStudyNotes = (bookId?: string): StudyNote[] => {
  const stored = localStorage.getItem(STORAGE_KEY);
  const allNotes: StudyNote[] = stored ? JSON.parse(stored) : [];
  if (bookId) {
    return allNotes.filter(n => n.bookId === bookId);
  }
  return allNotes;
};

export const saveStudyNote = (note: Partial<StudyNote> & { bookId: string }): StudyNote => {
  const allNotes = getStudyNotes();
  const now = new Date().toISOString();
  
  if (note.id) {
    const index = allNotes.findIndex(n => n.id === note.id);
    if (index !== -1) {
      const updated = { ...allNotes[index], ...note, updatedAt: now } as StudyNote;
      allNotes[index] = updated;
      localStorage.setItem(STORAGE_KEY, JSON.stringify(allNotes));
      return updated;
    }
  }
  
  const newNote: StudyNote = {
    ...note,
    id: 'sn-' + Math.random().toString(36).substr(2, 9),
    type: note.type || 'note',
    reference: note.reference || 'General',
    content: note.content || '',
    tags: note.tags || [],
    createdAt: now,
    updatedAt: now,
  } as StudyNote;

  allNotes.unshift(newNote);
  localStorage.setItem(STORAGE_KEY, JSON.stringify(allNotes));
  return newNote;
};

export const deleteStudyNote = (id: string): void => {
  const allNotes = getStudyNotes().filter(n => n.id !== id);
  localStorage.setItem(STORAGE_KEY, JSON.stringify(allNotes));
};

export const getReferences = (bookId: string): string[] => {
  const notes = getStudyNotes(bookId);
  const refs = Array.from(new Set(notes.map(n => n.reference)));
  return refs.sort();
};
