<template>
  <div class="fixed inset-0 z-[100] bg-slate-950 flex flex-col animate-in fade-in duration-500">
    <!-- Header -->
    <header class="h-16 md:h-20 border-b border-slate-900 flex items-center justify-between px-4 md:px-8 glass sticky top-0 z-20">
      <div class="flex items-center gap-3 md:gap-6 min-w-0 flex-1">
        <button @click="handleBack" class="p-2 rounded-full hover:bg-slate-800 text-slate-400 transition-colors flex-shrink-0">
          <ArrowLeft :size="20" class="md:hidden" />
          <ArrowLeft :size="24" class="hidden md:block" />
        </button>
        <div class="h-6 md:h-8 w-px bg-slate-800 flex-shrink-0" />
        <div class="flex items-center gap-2 md:gap-3 min-w-0">
          <div class="w-8 h-8 md:w-10 md:h-10 rounded-xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center flex-shrink-0">
            <Brain class="text-indigo-400" :size="16" />
          </div>
          <div class="min-w-0 flex-1">
            <div class="flex items-center gap-2">
              <h1 class="text-xs md:text-sm font-black text-white uppercase tracking-widest truncate">{{ bookTitle }}</h1>
              <button
                @click="showBookSelector = true"
                class="p-1.5 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-indigo-400 transition-colors flex-shrink-0"
                title="Change book"
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M17 3a2.85 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z"/>
                  <path d="m15 5 4 4"/>
                </svg>
              </button>
            </div>
            <p class="text-[9px] md:text-[10px] font-bold text-slate-500 uppercase tracking-[0.2em] hidden md:block">Study Mode Active</p>
          </div>
        </div>
      </div>

      <div class="flex items-center gap-2 md:gap-4 flex-shrink-0">
        <button
          @click="exportToPDF"
          :disabled="notes.length === 0"
          class="hidden md:flex items-center gap-2 px-4 py-2 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-bold hover:bg-emerald-500/20 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
          title="Export study notes to PDF"
        >
          <Download :size="16" />
          Export PDF
        </button>
        <button @click="showSearch = !showSearch" class="md:hidden p-2 rounded-lg hover:bg-slate-800 text-slate-400 transition-colors">
          <Search :size="18" />
        </button>
        <div class="relative group hidden md:block">
          <Search class="absolute left-3 top-1/2 -translate-y-1/2 text-slate-600 group-focus-within:text-indigo-400 transition-colors" :size="16" />
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Search notes..."
            class="bg-slate-900/50 border border-slate-800 rounded-xl pl-10 pr-4 py-2 text-xs text-white outline-none focus:border-indigo-500 transition-all w-48"
          />
        </div>
      </div>
    </header>

    <!-- Mobile Search Bar -->
    <div v-if="showSearch" class="md:hidden p-4 border-b border-slate-900 bg-slate-950">
      <div class="relative">
        <Search class="absolute left-3 top-1/2 -translate-y-1/2 text-slate-600" :size="16" />
        <input
          v-model="searchQuery"
          type="text"
          placeholder="Search notes..."
          class="w-full bg-slate-900/50 border border-slate-800 rounded-xl pl-10 pr-4 py-2 text-xs text-white outline-none focus:border-indigo-500 transition-all"
        />
      </div>
    </div>

    <!-- Main Workspace -->
    <div class="flex-1 flex overflow-hidden">
      <!-- Sidebar: References List - Hidden on mobile, shown as drawer -->
      <aside :class="['border-r border-slate-900 flex flex-col bg-slate-950 transition-transform duration-300 z-10', showReferences ? 'fixed inset-y-0 left-0 w-64 md:w-72 shadow-2xl' : 'hidden md:flex md:w-72']">
        <div class="p-4 md:p-6">
          <div class="flex items-center justify-between mb-4">
            <h3 class="text-[10px] font-black text-slate-500 uppercase tracking-widest">References</h3>
            <button @click="showReferences = false" class="md:hidden p-1 rounded-lg hover:bg-slate-800 text-slate-500">
              <X :size="16" />
            </button>
          </div>
          <button
            @click="selectedRef = null; showReferences = false"
            :class="['w-full text-left px-4 py-3 rounded-xl text-xs font-bold transition-all mb-2', !selectedRef ? 'bg-indigo-500 text-white' : 'text-slate-400 hover:bg-slate-900']"
          >
            All References ({{ notes.length }})
          </button>
          <div class="space-y-1 overflow-y-auto max-h-[calc(100vh-200px)] custom-scrollbar">
            <button
              v-for="ref in references"
              :key="ref"
              @click="selectedRef = ref; showReferences = false"
              :class="['w-full text-left px-4 py-3 rounded-xl text-xs font-bold transition-all flex justify-between items-center', selectedRef === ref ? 'bg-slate-800 text-white' : 'text-slate-500 hover:bg-slate-900']"
            >
              <span class="truncate">{{ ref }}</span>
              <span class="text-[8px] bg-slate-900 px-1.5 py-0.5 rounded border border-slate-800">
                {{ notes.filter(n => n.reference === ref).length }}
              </span>
            </button>
          </div>
        </div>
      </aside>

      <!-- Backdrop for mobile drawer -->
      <div v-if="showReferences" @click="showReferences = false" class="md:hidden fixed inset-0 bg-black/50 z-[5]"></div>

      <!-- Notes Surface -->
      <main class="flex-1 overflow-y-auto custom-scrollbar bg-slate-950/20 p-4 md:p-8 lg:p-12">
        <div class="max-w-[1800px] mx-auto space-y-6 md:space-y-8">
          <!-- Mobile Reference Toggle + Type Filtering -->
          <div class="space-y-3">
            <!-- Mobile reference toggle button -->
            <button
              @click="showReferences = true"
              class="md:hidden w-full flex items-center justify-between px-4 py-3 rounded-xl bg-slate-900 border border-slate-800 text-sm font-bold text-white hover:bg-slate-800 transition-all"
            >
              <div class="flex items-center gap-2">
                <Filter :size="16" />
                <span>{{ selectedRef || 'All References' }}</span>
              </div>
              <span class="text-[10px] bg-slate-800 px-2 py-1 rounded border border-slate-700">
                {{ filteredNotes.length }}
              </span>
            </button>

            <!-- Type Filtering - Wrap on mobile -->
            <div class="flex items-center gap-2 flex-wrap">
              <button
                @click="activeType = 'all'"
                :class="['flex items-center gap-1.5 px-3 md:px-4 py-1.5 md:py-2 rounded-xl text-[10px] md:text-xs font-bold transition-all', activeType === 'all' ? 'bg-indigo-500 text-white shadow-lg shadow-indigo-500/10' : 'text-slate-500 hover:text-slate-300']"
              >
                <LayoutGrid :size="12" class="md:hidden" />
                <LayoutGrid :size="14" class="hidden md:block" />
                All
              </button>
              <button
                @click="activeType = 'quote'"
                :class="['flex items-center gap-1.5 px-3 md:px-4 py-1.5 md:py-2 rounded-xl text-[10px] md:text-xs font-bold transition-all', activeType === 'quote' ? 'bg-indigo-500 text-white shadow-lg shadow-indigo-500/10' : 'text-slate-500 hover:text-slate-300']"
              >
                <QuoteIcon :size="12" class="md:hidden" />
                <QuoteIcon :size="14" class="hidden md:block" />
                Quotes
              </button>
              <button
                @click="activeType = 'insight'"
                :class="['flex items-center gap-1.5 px-3 md:px-4 py-1.5 md:py-2 rounded-xl text-[10px] md:text-xs font-bold transition-all', activeType === 'insight' ? 'bg-indigo-500 text-white shadow-lg shadow-indigo-500/10' : 'text-slate-500 hover:text-slate-300']"
              >
                <Lightbulb :size="12" class="md:hidden" />
                <Lightbulb :size="14" class="hidden md:block" />
                Insights
              </button>
              <button
                @click="activeType = 'question'"
                :class="['flex items-center gap-1.5 px-3 md:px-4 py-1.5 md:py-2 rounded-xl text-[10px] md:text-xs font-bold transition-all', activeType === 'question' ? 'bg-indigo-500 text-white shadow-lg shadow-indigo-500/10' : 'text-slate-500 hover:text-slate-300']"
              >
                <HelpCircle :size="12" class="md:hidden" />
                <HelpCircle :size="14" class="hidden md:block" />
                Questions
              </button>
              <button
                @click="activeType = 'note'"
                :class="['flex items-center gap-1.5 px-3 md:px-4 py-1.5 md:py-2 rounded-xl text-[10px] md:text-xs font-bold transition-all', activeType === 'note' ? 'bg-indigo-500 text-white shadow-lg shadow-indigo-500/10' : 'text-slate-500 hover:text-slate-300']"
              >
                <MessageSquare :size="12" class="md:hidden" />
                <MessageSquare :size="14" class="hidden md:block" />
                Notes
              </button>
            </div>
          </div>

          <!-- Two-column masonry grid -->
          <div v-if="filteredNotes.length > 0" class="columns-1 md:columns-2 gap-6 space-y-6">
            <StudyNoteCard
              v-for="note in filteredNotes"
              :key="note.id"
              :note="note"
              @edit="handleEdit"
              @delete="handleDelete"
              @promote="handlePromote"
              @highlight="handleHighlight"
              @remove-highlight="handleRemoveHighlight"
              class="break-inside-avoid mb-6"
            />
          </div>
          <div v-else class="py-40 text-center">
            <div class="w-16 h-16 rounded-full bg-slate-900 border border-slate-800 flex items-center justify-center mx-auto mb-6 text-slate-700">
              <BookOpen :size="28" />
            </div>
            <h3 class="text-xl font-bold text-white mb-2">No notes here yet</h3>
            <p class="text-slate-500 text-sm">Start your study session using the capture bar below.</p>
          </div>
        </div>
      </main>
    </div>

    <!-- Quick Add Footer - Responsive -->
    <footer class="relative bg-slate-900/50 border-t border-slate-900 glass transition-all duration-300">
      <!-- Toggle Button -->
      <button
        @click="isFooterCollapsed = !isFooterCollapsed"
        class="absolute -top-10 right-6 p-2 rounded-t-lg bg-slate-900/80 border border-slate-800 border-b-0 text-slate-400 hover:text-indigo-400 hover:border-indigo-500/30 transition-all z-10"
        :aria-label="isFooterCollapsed ? 'Expand footer' : 'Collapse footer'"
      >
        <ChevronUp v-if="isFooterCollapsed" :size="16" />
        <ChevronDown v-else :size="16" />
      </button>

      <div v-show="!isFooterCollapsed" class="p-3 md:p-6">
        <div class="max-w-5xl mx-auto space-y-3">
        <!-- Desktop Layout: Type selector + Reference + Page + Chapter + Capture -->
        <div class="hidden md:flex items-center gap-4">
          <!-- Type selector -->
          <div class="flex items-center gap-1 p-1 bg-slate-950 rounded-xl border border-slate-800">
            <button
              @click="newNoteType = 'note'"
              :class="['flex items-center gap-2 px-3 py-2 rounded-lg text-[9px] font-black uppercase tracking-widest transition-all', newNoteType === 'note' ? 'bg-slate-800 text-white' : 'text-slate-600 hover:text-slate-400']"
            >
              <MessageSquare :size="12" />
              Note
            </button>
            <button
              @click="newNoteType = 'quote'"
              :class="['flex items-center gap-2 px-3 py-2 rounded-lg text-[9px] font-black uppercase tracking-widest transition-all', newNoteType === 'quote' ? 'bg-slate-800 text-white' : 'text-slate-600 hover:text-slate-400']"
            >
              <QuoteIcon :size="12" />
              Quote
            </button>
            <button
              @click="newNoteType = 'insight'"
              :class="['flex items-center gap-2 px-3 py-2 rounded-lg text-[9px] font-black uppercase tracking-widest transition-all', newNoteType === 'insight' ? 'bg-slate-800 text-white' : 'text-slate-600 hover:text-slate-400']"
            >
              <Lightbulb :size="12" />
              Insight
            </button>
            <button
              @click="newNoteType = 'question'"
              :class="['flex items-center gap-2 px-3 py-2 rounded-lg text-[9px] font-black uppercase tracking-widest transition-all', newNoteType === 'question' ? 'bg-slate-800 text-white' : 'text-slate-600 hover:text-slate-400']"
            >
              <HelpCircle :size="12" />
              Query
            </button>
          </div>

          <!-- Reference input -->
          <input
            v-model="newNoteRef"
            type="text"
            placeholder="Reference (e.g. John 3:16, Romans 8:28)"
            class="flex-1 bg-slate-950 border border-slate-800 rounded-xl px-4 py-2 text-xs text-white outline-none focus:border-indigo-500 transition-all"
          />

          <!-- Page Number input -->
          <input
            v-model="newNotePageNumber"
            type="number"
            placeholder="Page"
            class="w-20 bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white outline-none focus:border-indigo-500 transition-all"
          />

          <!-- Chapter input -->
          <input
            v-model="newNoteChapter"
            type="text"
            placeholder="Chapter"
            class="w-28 bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white outline-none focus:border-indigo-500 transition-all"
          />

          <!-- Capture button -->
          <button
            @click="handleSave"
            class="px-6 py-2 rounded-xl bg-indigo-500 text-white font-bold text-sm shadow-xl shadow-indigo-500/20 hover:bg-indigo-400 active:scale-95 transition-all flex items-center gap-2 whitespace-nowrap"
          >
            Capture
            <Plus :size="18" />
          </button>
        </div>

        <!-- Mobile Layout: Stacked -->
        <div class="md:hidden space-y-2">
          <!-- Type selector - Wrap instead of scroll -->
          <div class="flex items-center gap-1 flex-wrap">
            <button
              @click="newNoteType = 'note'"
              :class="['flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-[8px] font-black uppercase tracking-widest transition-all', newNoteType === 'note' ? 'bg-slate-800 text-white' : 'text-slate-600 bg-slate-950']"
            >
              <MessageSquare :size="10" />
              Note
            </button>
            <button
              @click="newNoteType = 'quote'"
              :class="['flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-[8px] font-black uppercase tracking-widest transition-all', newNoteType === 'quote' ? 'bg-slate-800 text-white' : 'text-slate-600 bg-slate-950']"
            >
              <QuoteIcon :size="10" />
              Quote
            </button>
            <button
              @click="newNoteType = 'insight'"
              :class="['flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-[8px] font-black uppercase tracking-widest transition-all', newNoteType === 'insight' ? 'bg-slate-800 text-white' : 'text-slate-600 bg-slate-950']"
            >
              <Lightbulb :size="10" />
              Insight
            </button>
            <button
              @click="newNoteType = 'question'"
              :class="['flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-[8px] font-black uppercase tracking-widest transition-all', newNoteType === 'question' ? 'bg-slate-800 text-white' : 'text-slate-600 bg-slate-950']"
            >
              <HelpCircle :size="10" />
              Query
            </button>
          </div>

          <!-- Reference full width -->
          <input
            v-model="newNoteRef"
            type="text"
            placeholder="Reference (e.g. John 3:16)"
            class="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white outline-none focus:border-indigo-500 transition-all"
          />

          <!-- Page + Chapter + Capture button row -->
          <div class="flex items-center gap-2">
            <input
              v-model="newNotePageNumber"
              type="number"
              placeholder="Page"
              class="flex-1 bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white outline-none focus:border-indigo-500 transition-all"
            />
            <input
              v-model="newNoteChapter"
              type="text"
              placeholder="Chapter"
              class="flex-1 bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white outline-none focus:border-indigo-500 transition-all"
            />
          </div>
        </div>

        <!-- Textarea - Full width on all screens -->
        <textarea
          v-model="newNoteContent"
          @keydown.meta.enter="handleSave"
          @keydown.ctrl.enter="handleSave"
          placeholder="What are you learning?"
          class="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 md:px-4 py-2 md:py-2.5 text-xs md:text-sm text-white outline-none focus:border-indigo-500 transition-all resize-none"
          :rows="5"
        />

        <!-- Mobile Capture button -->
        <button
          @click="handleSave"
          class="md:hidden w-full py-2 rounded-xl bg-indigo-500 text-white font-bold text-xs shadow-xl shadow-indigo-500/20 hover:bg-indigo-400 active:scale-95 transition-all flex items-center justify-center gap-2"
        >
          <Plus :size="16" />
          Capture
        </button>
        </div>
      </div>
    </footer>

    <!-- Edit Modal -->
    <Teleport to="body">
      <div
        v-if="showEditModal"
        class="fixed inset-0 bg-black/80 backdrop-blur-sm z-[100] flex items-center justify-center p-4"
        @click.self="handleCancelEdit"
      >
        <div class="bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl max-w-3xl w-full max-h-[90vh] overflow-y-auto">
          <!-- Modal Header -->
          <div class="p-6 border-b border-slate-800 flex items-center justify-between sticky top-0 bg-slate-900 z-10">
            <h2 class="text-xl font-bold text-white">Edit Study Note</h2>
            <button
              @click="handleCancelEdit"
              class="p-2 rounded-lg hover:bg-slate-800 text-slate-500 hover:text-white transition-colors"
            >
              <X :size="20" />
            </button>
          </div>

          <!-- Modal Body -->
          <div class="p-6 space-y-4">
            <!-- Type selector -->
            <div>
              <label class="block text-xs font-bold text-slate-400 uppercase tracking-widest mb-2">Type</label>
              <div class="flex items-center gap-2 p-1 bg-slate-950 rounded-xl border border-slate-800">
                <button
                  @click="editNoteType = 'note'"
                  :class="['flex items-center gap-2 px-3 py-2 rounded-lg text-[9px] font-black uppercase tracking-widest transition-all', editNoteType === 'note' ? 'bg-slate-800 text-white' : 'text-slate-600 hover:text-slate-400']"
                >
                  <MessageSquare :size="12" />
                  Note
                </button>
                <button
                  @click="editNoteType = 'quote'"
                  :class="['flex items-center gap-2 px-3 py-2 rounded-lg text-[9px] font-black uppercase tracking-widest transition-all', editNoteType === 'quote' ? 'bg-slate-800 text-white' : 'text-slate-600 hover:text-slate-400']"
                >
                  <QuoteIcon :size="12" />
                  Quote
                </button>
                <button
                  @click="editNoteType = 'insight'"
                  :class="['flex items-center gap-2 px-3 py-2 rounded-lg text-[9px] font-black uppercase tracking-widest transition-all', editNoteType === 'insight' ? 'bg-slate-800 text-white' : 'text-slate-600 hover:text-slate-400']"
                >
                  <Lightbulb :size="12" />
                  Insight
                </button>
                <button
                  @click="editNoteType = 'question'"
                  :class="['flex items-center gap-2 px-3 py-2 rounded-lg text-[9px] font-black uppercase tracking-widest transition-all', editNoteType === 'question' ? 'bg-slate-800 text-white' : 'text-slate-600 hover:text-slate-400']"
                >
                  <HelpCircle :size="12" />
                  Query
                </button>
              </div>
            </div>

            <!-- Reference input -->
            <div>
              <label class="block text-xs font-bold text-slate-400 uppercase tracking-widest mb-2">Reference</label>
              <input
                v-model="editNoteRef"
                type="text"
                placeholder="Reference (e.g. John 3:16, Romans 8:28)"
                class="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2 text-sm text-white outline-none focus:border-indigo-500 transition-all"
              />
            </div>

            <!-- Page and Chapter -->
            <div class="grid grid-cols-2 gap-4">
              <div>
                <label class="block text-xs font-bold text-slate-400 uppercase tracking-widest mb-2">Page</label>
                <input
                  v-model="editNotePageNumber"
                  type="number"
                  placeholder="Page number"
                  class="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2 text-sm text-white outline-none focus:border-indigo-500 transition-all"
                />
              </div>
              <div>
                <label class="block text-xs font-bold text-slate-400 uppercase tracking-widest mb-2">Chapter</label>
                <input
                  v-model="editNoteChapter"
                  type="text"
                  placeholder="Chapter"
                  class="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2 text-sm text-white outline-none focus:border-indigo-500 transition-all"
                />
              </div>
            </div>

            <!-- Content textarea -->
            <div>
              <label class="block text-xs font-bold text-slate-400 uppercase tracking-widest mb-2">Content</label>
              <textarea
                v-model="editNoteContent"
                placeholder="What are you learning?"
                class="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-white outline-none focus:border-indigo-500 transition-all resize-none"
                :rows="8"
              />
            </div>
          </div>

          <!-- Modal Footer -->
          <div class="p-6 border-t border-slate-800 flex items-center justify-end gap-3">
            <button
              @click="handleCancelEdit"
              class="px-6 py-2 rounded-xl bg-slate-800 text-white font-bold text-sm hover:bg-slate-700 transition-all"
            >
              Cancel
            </button>
            <button
              @click="handleSaveEdit"
              class="px-6 py-2 rounded-xl bg-indigo-500 text-white font-bold text-sm shadow-xl shadow-indigo-500/20 hover:bg-indigo-400 transition-all"
            >
              Save Changes
            </button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Book Selector Modal -->
    <Teleport to="body">
      <div v-if="showBookSelector" class="fixed inset-0 z-[200] flex items-center justify-center p-4 bg-black/80 animate-in fade-in duration-200" @click.self="showBookSelector = false">
        <div class="w-full max-w-2xl bg-slate-900 rounded-2xl shadow-2xl border border-slate-800 animate-in zoom-in-95 duration-200">
          <!-- Modal Header -->
          <div class="p-6 border-b border-slate-800">
            <div class="flex items-center justify-between mb-4">
              <h2 class="text-lg font-black text-white uppercase tracking-widest">Select Book</h2>
              <button @click="showBookSelector = false" class="p-2 rounded-lg hover:bg-slate-800 text-slate-400 transition-colors">
                <X :size="20" />
              </button>
            </div>
            <!-- Search -->
            <div class="relative">
              <Search class="absolute left-3 top-1/2 -translate-y-1/2 text-slate-600" :size="18" />
              <input
                v-model="bookSearchQuery"
                type="text"
                placeholder="Search by title or author..."
                class="w-full bg-slate-950 border border-slate-800 rounded-xl pl-11 pr-4 py-3 text-sm text-white outline-none focus:border-indigo-500 transition-all"
                autofocus
              />
            </div>
          </div>

          <!-- Books List -->
          <div class="p-4 max-h-[60vh] overflow-y-auto custom-scrollbar">
            <div v-if="filteredBooks.length === 0" class="py-12 text-center">
              <BookOpen :size="48" class="mx-auto mb-4 text-slate-700" />
              <p class="text-slate-500 text-sm">No books found</p>
            </div>
            <div v-else class="space-y-2">
              <button
                v-for="userBook in filteredBooks"
                :key="userBook.id"
                @click="selectBook(userBook)"
                class="w-full flex items-center gap-4 p-4 rounded-xl hover:bg-slate-800 transition-all group text-left"
              >
                <!-- Book Cover -->
                <div class="w-12 h-16 rounded-lg overflow-hidden bg-slate-800 flex-shrink-0 flex items-center justify-center">
                  <img
                    v-if="userBook.book?.cover_image"
                    :src="userBook.book.cover_image"
                    :alt="userBook.book.title"
                    class="w-full h-full object-cover"
                  />
                  <BookOpen v-else :size="20" class="text-slate-600" />
                </div>

                <!-- Book Info -->
                <div class="flex-1 min-w-0">
                  <h3 class="font-bold text-white text-sm truncate group-hover:text-indigo-400 transition-colors">
                    {{ userBook.book?.title }}
                  </h3>
                  <p class="text-slate-500 text-xs truncate">
                    {{ userBook.book?.authors?.map(a => a.name).join(', ') || 'Unknown Author' }}
                  </p>
                </div>

                <!-- Active indicator -->
                <div v-if="userBook.book?.id == bookId" class="flex-shrink-0">
                  <div class="w-2 h-2 rounded-full bg-indigo-500"></div>
                </div>
              </button>
            </div>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useStudyNotesStore } from '@/stores/studyNotesStore'
import { useQuotesStore } from '@/stores/quotesStore'
import { useUserBooksStore } from '@/stores/userBooksStore'
import StudyNoteCard from '@/components/StudyNoteCard.vue'
import {
  ArrowLeft,
  Brain,
  Search,
  Plus,
  BookOpen,
  MessageSquare,
  HelpCircle,
  Lightbulb,
  Quote as QuoteIcon,
  LayoutGrid,
  Filter,
  X,
  ChevronUp,
  ChevronDown,
  Download
} from 'lucide-vue-next'
import html2pdf from 'html2pdf.js'

const props = defineProps({
  bookId: {
    type: [String, Number],
    required: true
  },
  bookTitle: {
    type: String,
    default: 'Study Session'
  }
})

const router = useRouter()

const studyNotesStore = useStudyNotesStore()
const quotesStore = useQuotesStore()
const booksStore = useUserBooksStore()

const notes = computed(() => studyNotesStore.notes || [])
const searchQuery = ref('')
const selectedRef = ref(null)
const activeType = ref('all')
const newNoteContent = ref('')
const newNoteRef = ref('')
const newNoteType = ref('note')
const newNotePageNumber = ref('')
const newNoteChapter = ref('')
const showSearch = ref(false)
const showReferences = ref(false)
const isFooterCollapsed = ref(false)
const showEditModal = ref(false)
const editingNote = ref(null)
const editNoteContent = ref('')
const editNoteRef = ref('')
const editNotePageNumber = ref('')
const editNoteChapter = ref('')
const editNoteType = ref('note')
const showNewNoteHighlightButton = ref(false)
const newNoteHighlightPosition = ref({ x: 0, y: 0 })
const newNoteTextareaRef = ref(null)
const showBookSelector = ref(false)
const bookSearchQuery = ref('')
const userBooks = ref([])

const loadStudyData = async () => {
  await studyNotesStore.fetchNotes({ book: props.bookId })
}

onMounted(async () => {
  await Promise.all([
    loadStudyData(),
    booksStore.fetchBooks()
  ])
  userBooks.value = booksStore.userBooks || []
  window.scrollTo(0, 0)
})

watch(() => props.bookId, async (newId, oldId) => {
  if (newId && newId !== oldId) {
    await loadStudyData()
  }
})

const references = computed(() => {
  const refsMap = new Map() // Use Map to track lowercase -> original case mapping

  notes.value.forEach(note => {
    // If backend sends references_list, use it; otherwise split by comma
    const refList = note.references_list || (note.reference ? note.reference.split(',').map(r => r.trim()) : ['General'])
    refList.forEach(ref => {
      if (ref) {
        const lowerRef = ref.toLowerCase()
        // Keep first occurrence's case
        if (!refsMap.has(lowerRef)) {
          refsMap.set(lowerRef, ref)
        }
      }
    })
  })

  // Return sorted references (case-insensitive sort)
  return Array.from(refsMap.values()).sort((a, b) => a.toLowerCase().localeCompare(b.toLowerCase()))
})

const filteredNotes = computed(() => {
  let filtered = [...notes.value]

  if (selectedRef.value) {
    filtered = filtered.filter(n => {
      // Check if note contains the selected reference (case-insensitive, supports multiple references)
      const refList = n.references_list || (n.reference ? n.reference.split(',').map(r => r.trim()) : [])
      return refList.some(ref => ref.toLowerCase() === selectedRef.value.toLowerCase())
    })
  }

  if (activeType.value !== 'all') {
    filtered = filtered.filter(n => n.note_type === activeType.value)
  }

  if (searchQuery.value) {
    const search = searchQuery.value.toLowerCase()
    filtered = filtered.filter(n =>
      n.content.toLowerCase().includes(search) ||
      n.reference?.toLowerCase().includes(search)
    )
  }

  return filtered
})

const handleSave = async () => {
  if (!newNoteContent.value.trim()) return

  const payload = {
    book: props.bookId,
    content: newNoteContent.value,
    reference: newNoteRef.value || 'General',
    note_type: newNoteType.value,
    page_number: newNotePageNumber.value ? parseInt(newNotePageNumber.value) : null,
    chapter: newNoteChapter.value || null
  }

  const result = await studyNotesStore.createNote(payload)

  if (result.success) {
    newNoteContent.value = ''
    newNoteRef.value = ''
    newNotePageNumber.value = ''
    newNoteChapter.value = ''
  }
}

const handleDelete = async (id) => {
  if (confirm('Delete study note?')) {
    await studyNotesStore.deleteNote(id)
  }
}

const handleEdit = (note) => {
  editingNote.value = note
  editNoteContent.value = note.content
  editNoteRef.value = note.reference || ''
  editNotePageNumber.value = note.page_number || ''
  editNoteChapter.value = note.chapter || ''
  editNoteType.value = note.note_type || 'note'
  showEditModal.value = true
}

const handleSaveEdit = async () => {
  if (!editNoteContent.value.trim() || !editingNote.value) return

  const result = await studyNotesStore.updateNote(editingNote.value.id, {
    content: editNoteContent.value,
    reference: editNoteRef.value,
    page_number: editNotePageNumber.value || null,
    chapter: editNoteChapter.value,
    note_type: editNoteType.value
  })

  if (result.success) {
    showEditModal.value = false
    editingNote.value = null
    editNoteContent.value = ''
    editNoteRef.value = ''
    editNotePageNumber.value = ''
    editNoteChapter.value = ''
  }
}

const handleCancelEdit = () => {
  showEditModal.value = false
  editingNote.value = null
  editNoteContent.value = ''
  editNoteRef.value = ''
  editNotePageNumber.value = ''
  editNoteChapter.value = ''
}

const handlePromote = async (note) => {
  if (confirm('Promote this study note to a main quote?')) {
    const result = await studyNotesStore.promoteToQuote(note.id)
    if (result.success) {
      // Refresh quotes store to show new quote
      await quotesStore.fetchQuotes()
    }
  }
}

const handleHighlight = async (highlightData) => {
  console.log('handleHighlight called with:', highlightData)

  // Store highlight in the note
  const note = notes.value.find(n => n.id === highlightData.noteId)
  console.log('Found note:', note)

  if (note) {
    if (!note.highlights) {
      note.highlights = []
    }

    // Check if this text is already highlighted
    const alreadyHighlighted = note.highlights.some(h => h.text === highlightData.text)
    if (alreadyHighlighted) {
      return // Don't add duplicate highlights
    }

    note.highlights.push({
      text: highlightData.text,
      startOffset: highlightData.startOffset,
      endOffset: highlightData.endOffset
    })

    // Update the note in the backend
    const result = await studyNotesStore.updateNote(highlightData.noteId, {
      highlights: note.highlights
    })

    console.log('Update result:', result)
    if (result.data) {
      console.log('Backend returned data:', result.data)
      console.log('Backend returned data.id:', result.data.id)
    }

    if (!result.success) {
      console.error('Failed to save highlight:', result.error)
      // Remove the highlight from local state if save failed
      note.highlights.pop()
    }
  } else {
    console.error('Note not found! noteId:', highlightData.noteId, 'Available notes:', notes.value.map(n => n.id))
  }
}

const handleRemoveHighlight = async (highlightData) => {
  console.log('handleRemoveHighlight called with:', highlightData)

  const note = notes.value.find(n => n.id === highlightData.noteId)
  console.log('Found note:', note)

  if (note && note.highlights) {
    // Remove the highlight from the array
    note.highlights = note.highlights.filter(h => h.text !== highlightData.text)

    // Update the note in the backend
    const result = await studyNotesStore.updateNote(highlightData.noteId, {
      highlights: note.highlights
    })

    if (!result.success) {
      console.error('Failed to remove highlight:', result.error)
      // Restore the highlight if save failed
      note.highlights.push({
        text: highlightData.text
      })
    }
  } else {
    console.error('Note not found! noteId:', highlightData.noteId, 'Available notes:', notes.value.map(n => n.id))
  }
}

const handleBack = () => {
  router.push(`/books/${props.bookId}`)
}

const handleNewNoteTextSelection = () => {
  setTimeout(() => {
    const selection = window.getSelection()
    const selectedText = selection.toString().trim()

    if (selectedText.length > 0 && newNoteTextareaRef.value?.contains(selection.anchorNode)) {
      const range = selection.getRangeAt(0)
      const rect = range.getBoundingClientRect()

      newNoteHighlightPosition.value = {
        x: rect.left + rect.width / 2,
        y: rect.top - 45
      }
      showNewNoteHighlightButton.value = true
    } else {
      showNewNoteHighlightButton.value = false
    }
  }, 10)
}

const applyNewNoteHighlight = () => {
  const selection = window.getSelection()
  const selectedText = selection.toString().trim()

  if (selectedText.length > 0) {
    // Wrap the selected text in a highlight mark
    const range = selection.getRangeAt(0)
    const mark = document.createElement('mark')
    mark.className = 'bg-yellow-400/30 px-0.5 rounded highlight-text'

    try {
      range.surroundContents(mark)
    } catch (e) {
      // If surroundContents fails (e.g., selection spans multiple elements), use a different approach
      const fragment = range.extractContents()
      mark.appendChild(fragment)
      range.insertNode(mark)
    }
  }

  showNewNoteHighlightButton.value = false
  selection.removeAllRanges()
}

// Filter books based on search
const filteredBooks = computed(() => {
  if (!bookSearchQuery.value) return userBooks.value

  const query = bookSearchQuery.value.toLowerCase()
  return userBooks.value.filter(userBook =>
    userBook.book?.title?.toLowerCase().includes(query) ||
    userBook.book?.authors?.some(author => author.name?.toLowerCase().includes(query))
  )
})

// Export study notes to PDF
const exportToPDF = () => {
  if (notes.value.length === 0) return

  // Stats
  const quoteCount = notes.value.filter(n => n.note_type === 'quote').length
  const insightCount = notes.value.filter(n => n.note_type === 'insight').length
  const questionCount = notes.value.filter(n => n.note_type === 'question').length
  const noteCount = notes.value.filter(n => n.note_type === 'note').length

  const exportDate = new Date().toLocaleDateString('sr-RS', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })

  // Sort notes by reference (case-insensitive)
  const sortedNotes = [...notes.value].sort((a, b) => {
    const refA = (a.reference || 'General').toLowerCase()
    const refB = (b.reference || 'General').toLowerCase()
    return refA.localeCompare(refB)
  })

  // Group notes by reference (case-insensitive grouping)
  const groupedNotes = {}
  const refCaseMap = {} // Track original case for each lowercase reference

  sortedNotes.forEach(note => {
    const ref = note.reference || 'General'
    const refLower = ref.toLowerCase()

    // Use first occurrence's case as the key
    if (!refCaseMap[refLower]) {
      refCaseMap[refLower] = ref
    }

    const displayRef = refCaseMap[refLower]
    if (!groupedNotes[displayRef]) {
      groupedNotes[displayRef] = []
    }
    groupedNotes[displayRef].push(note)
  })

  // Create HTML content
  let htmlContent = `
    <!DOCTYPE html>
    <html lang="sr">
    <head>
      <meta charset="UTF-8">
      <style>
        @page {
          margin: 20mm;
          size: A4;
        }
        body {
          font-family: 'Arial', 'Helvetica', sans-serif;
          font-size: 11pt;
          line-height: 1.6;
          color: #000;
        }
        h1 {
          font-size: 24pt;
          font-weight: bold;
          margin-bottom: 10px;
          color: #000;
        }
        .date {
          font-size: 10pt;
          color: #666;
          margin-bottom: 15px;
        }
        .stats {
          font-size: 10pt;
          margin-bottom: 20px;
          padding: 10px;
          background: #f5f5f5;
          border-radius: 5px;
        }
        .reference-section {
          margin-bottom: 25px;
          page-break-inside: avoid;
        }
        .reference-title {
          font-size: 16pt;
          font-weight: bold;
          color: #4F46E5;
          margin-bottom: 15px;
          border-bottom: 2px solid #4F46E5;
          padding-bottom: 5px;
        }
        .note {
          margin-bottom: 20px;
          page-break-inside: avoid;
        }
        .note-type {
          font-size: 9pt;
          font-weight: bold;
          text-transform: uppercase;
          margin-bottom: 3px;
        }
        .note-type.quote { color: #A855F7; }
        .note-type.insight { color: #FBBF24; }
        .note-type.question { color: #3B82F6; }
        .note-type.note { color: #64748B; }
        .note-meta {
          font-size: 8pt;
          color: #999;
          margin-bottom: 8px;
        }
        .note-content {
          font-size: 10pt;
          line-height: 1.5;
          white-space: pre-wrap;
          word-wrap: break-word;
        }
      </style>
    </head>
    <body>
      <h1>Study Notes: ${props.bookTitle}</h1>
      <div class="date">Exported on ${exportDate}</div>
      <div class="stats">
        Total Notes: ${notes.value.length} (${quoteCount} Quotes, ${insightCount} Insights, ${questionCount} Questions, ${noteCount} Notes)
      </div>
  `

  // Add notes grouped by reference
  Object.entries(groupedNotes).forEach(([reference, refNotes]) => {
    htmlContent += `<div class="reference-section">`
    htmlContent += `<div class="reference-title">${reference}</div>`

    refNotes.forEach(note => {
      const metaInfo = []
      if (note.page_number) metaInfo.push(`Page ${note.page_number}`)
      if (note.chapter) metaInfo.push(`Chapter: ${note.chapter}`)

      htmlContent += `
        <div class="note">
          <div class="note-type ${note.note_type}">${note.note_type.toUpperCase()}</div>
          ${metaInfo.length > 0 ? `<div class="note-meta">${metaInfo.join(' • ')}</div>` : ''}
          <div class="note-content">${note.content}</div>
        </div>
      `
    })

    htmlContent += `</div>`
  })

  htmlContent += `
    </body>
    </html>
  `

  // Create a temporary element
  const element = document.createElement('div')
  element.innerHTML = htmlContent

  // PDF options
  const opt = {
    margin: 10,
    filename: `${props.bookTitle.replace(/[^a-z0-9]/gi, '_').toLowerCase()}_study_notes.pdf`,
    image: { type: 'jpeg', quality: 0.98 },
    html2canvas: { scale: 2, useCORS: true, letterRendering: true },
    jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' }
  }

  // Generate PDF
  html2pdf().set(opt).from(element).save()
}

// Select book and navigate to study mode
const selectBook = (userBook) => {
  showBookSelector.value = false
  bookSearchQuery.value = ''
  router.push(`/books/${userBook.book.id}/study?title=${encodeURIComponent(userBook.book.title)}`)
}
</script>

<style scoped>
.custom-scrollbar::-webkit-scrollbar {
  width: 6px;
}

.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}

.custom-scrollbar::-webkit-scrollbar-thumb {
  background: rgb(51 65 85 / 0.5);
  border-radius: 3px;
}

.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: rgb(51 65 85 / 0.8);
}

.glass {
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
}

.scrollbar-hide {
  -ms-overflow-style: none;
  scrollbar-width: none;
}

.scrollbar-hide::-webkit-scrollbar {
  display: none;
}
</style>
