// Codex Service - API persistence for Journal entries and Manuscripts
import api from '@/services/api'

// ============ JOURNAL ENTRIES ============

export const getJournalEntries = async () => {
  const response = await api.get('/codex/journal/')
  return (response.data.results || response.data).map(transformEntry)
}

export const saveJournalEntry = async (entry) => {
  const payload = {
    title: entry.title || 'Untitled Reflection',
    content: entry.content || '',
    mood: entry.mood || 'serene',
    tags: entry.tags || [],
    is_locked: entry.isLocked || false,
    book: entry.bookReferenceId || null,
  }

  let response
  if (entry.id) {
    response = await api.put(`/codex/journal/${entry.id}/`, payload)
  } else {
    response = await api.post('/codex/journal/', payload)
  }
  return transformEntry(response.data)
}

export const deleteJournalEntry = async (entryId) => {
  await api.delete(`/codex/journal/${entryId}/`)
}

export const getTrashEntries = async () => {
  const response = await api.get('/codex/journal/trash/')
  return (response.data.results || response.data).map(transformEntry)
}

export const restoreJournalEntry = async (entryId) => {
  const response = await api.post(`/codex/journal/${entryId}/restore/`)
  return transformEntry(response.data)
}

export const exportJournal = async () => {
  const response = await api.get('/codex/journal/export/', { responseType: 'blob' })
  return response
}

// ============ MANUSCRIPTS ============

export const getManuscripts = async () => {
  const response = await api.get('/codex/manuscripts/')
  return (response.data.results || response.data).map(transformManuscriptList)
}

export const getManuscript = async (id) => {
  const response = await api.get(`/codex/manuscripts/${id}/`)
  return transformManuscriptDetail(response.data)
}

export const createManuscript = async (data = {}) => {
  const payload = {
    title: data.title || 'Untitled Manuscript',
    subtitle: data.subtitle || '',
    genre: data.genre || 'Fiction',
    cover_color: data.coverColor || '#6366f1',
    target_word_count: data.targetWordCount || 50000,
  }
  const response = await api.post('/codex/manuscripts/', payload)
  return transformManuscriptDetail(response.data)
}

export const saveManuscript = async (manuscript) => {
  const payload = {
    title: manuscript.title,
    subtitle: manuscript.subtitle || '',
    genre: manuscript.genre,
    cover_color: manuscript.coverColor,
    target_word_count: manuscript.targetWordCount,
  }
  const response = await api.put(`/codex/manuscripts/${manuscript.id}/`, payload)
  return transformManuscriptDetail(response.data)
}

export const deleteManuscript = async (manuscriptId) => {
  await api.delete(`/codex/manuscripts/${manuscriptId}/`)
}

export const getTrashManuscripts = async () => {
  const response = await api.get('/codex/manuscripts/trash/')
  return (response.data.results || response.data).map(transformManuscriptList)
}

export const restoreManuscript = async (manuscriptId) => {
  const response = await api.post(`/codex/manuscripts/${manuscriptId}/restore/`)
  return transformManuscriptDetail(response.data)
}

export const exportManuscript = async (manuscriptId, format = 'txt') => {
  const response = await api.get(`/codex/manuscripts/${manuscriptId}/export/`, {
    params: { format },
    responseType: 'blob',
  })
  return response
}

export const toggleManuscriptShare = async (manuscriptId) => {
  const response = await api.post(`/codex/manuscripts/${manuscriptId}/toggle_share/`)
  return transformManuscriptDetail(response.data)
}

export const getSharedManuscript = async (token) => {
  const response = await api.get(`/codex/manuscripts/shared/${token}/`)
  return transformManuscriptDetail(response.data)
}

// ============ CHAPTERS ============

export const addChapter = async (manuscriptId, title) => {
  const response = await api.post(`/codex/manuscripts/${manuscriptId}/add_chapter/`, {
    title: title || undefined
  })
  return transformChapter(response.data)
}

export const saveChapter = async (chapter) => {
  const payload = {
    title: chapter.title,
    content: chapter.content || '',
    order: chapter.order,
  }
  const response = await api.put(`/codex/chapters/${chapter.id}/`, payload)
  return transformChapter(response.data)
}

export const deleteChapter = async (chapterId) => {
  await api.delete(`/codex/chapters/${chapterId}/`)
}

// ============ TRANSFORMERS (snake_case -> camelCase) ============

function transformEntry(data) {
  return {
    id: data.id,
    date: data.created_at,
    title: data.title,
    content: data.content,
    mood: data.mood,
    tags: data.tags || [],
    isLocked: data.is_locked,
    bookReferenceId: data.book,
    wordCount: data.word_count,
    deletedAt: data.deleted_at,
    updatedAt: data.updated_at,
  }
}

function transformManuscriptList(data) {
  return {
    id: data.id,
    title: data.title,
    subtitle: data.subtitle,
    genre: data.genre,
    coverColor: data.cover_color,
    targetWordCount: data.target_word_count,
    currentWordCount: data.current_word_count,
    completionPercentage: data.completion_percentage,
    chapterCount: data.chapter_count,
    isShared: data.is_shared,
    shareToken: data.share_token,
    deletedAt: data.deleted_at,
    updatedAt: data.updated_at,
  }
}

function transformManuscriptDetail(data) {
  return {
    id: data.id,
    title: data.title,
    subtitle: data.subtitle,
    genre: data.genre,
    coverColor: data.cover_color,
    targetWordCount: data.target_word_count,
    currentWordCount: data.current_word_count,
    completionPercentage: data.completion_percentage,
    chapters: (data.chapters || []).map(transformChapter),
    isShared: data.is_shared,
    shareToken: data.share_token,
    updatedAt: data.updated_at,
  }
}

function transformChapter(data) {
  return {
    id: data.id,
    title: data.title,
    content: data.content,
    order: data.order,
    wordCount: data.word_count,
    lastEdited: data.updated_at,
  }
}

export default {
  getJournalEntries,
  saveJournalEntry,
  deleteJournalEntry,
  getTrashEntries,
  restoreJournalEntry,
  exportJournal,
  getManuscripts,
  getManuscript,
  createManuscript,
  saveManuscript,
  deleteManuscript,
  getTrashManuscripts,
  restoreManuscript,
  exportManuscript,
  toggleManuscriptShare,
  getSharedManuscript,
  addChapter,
  saveChapter,
  deleteChapter,
}
