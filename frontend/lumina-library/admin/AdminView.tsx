
import React, { useState, useMemo } from 'react';
import { 
  Database, ShieldAlert, Link2, GitMerge, Plus, 
  BarChart3, Settings, Search, Check, X, AlertTriangle,
  ChevronRight, ArrowRight, Filter, Download, Save,
  RefreshCw, Globe, BookCopy, Users, Layers
} from 'lucide-react';
import { getAdminStats, getPendingConflicts, getAuthorMergeCandidates, DataConflict, AuthorMergeCandidate } from '../services/adminService';

export const AdminView: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'overview' | 'conflicts' | 'authors' | 'curation'>('overview');
  const [searchQuery, setSearchQuery] = useState('');
  
  const stats = useMemo(() => getAdminStats(), []);
  const conflicts = useMemo(() => getPendingConflicts(), []);
  const authorCandidates = useMemo(() => getAuthorMergeCandidates(), []);

  return (
    <div className="h-full flex flex-col bg-[#02040a] animate-in fade-in duration-700 overflow-hidden">
      
      {/* 1. TOP ARCHITECT BAR */}
      <header className="h-24 border-b border-white/5 bg-slate-950/40 backdrop-blur-3xl flex items-center justify-between px-10 shrink-0">
        <div className="flex items-center gap-6">
          <div className="w-12 h-12 rounded-2xl bg-indigo-500 flex items-center justify-center shadow-2xl shadow-indigo-500/20 ring-1 ring-white/20">
            <Database size={24} className="text-white" />
          </div>
          <div>
            <h1 className="text-2xl font-black text-white tracking-tighter uppercase">Architect <span className="text-indigo-500">Command</span></h1>
            <div className="flex items-center gap-3">
              <span className="text-[10px] font-black text-slate-500 uppercase tracking-widest">System Core v8.4.1</span>
              <div className="flex items-center gap-1">
                <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                <span className="text-[9px] font-black text-emerald-500/80 uppercase">Node Active</span>
              </div>
            </div>
          </div>
        </div>

        <nav className="flex items-center gap-2 p-1.5 bg-white/5 rounded-2xl border border-white/5">
          <AdminTab active={activeTab === 'overview'} onClick={() => setActiveTab('overview')} label="Insight" icon={<BarChart3 size={14}/>} />
          <AdminTab active={activeTab === 'conflicts'} onClick={() => setActiveTab('conflicts')} label="Conflicts" icon={<ShieldAlert size={14}/>} badge={conflicts.length.toString()} />
          <AdminTab active={activeTab === 'authors'} onClick={() => setActiveTab('authors')} label="Author Sync" icon={<Users size={14}/>} />
          <AdminTab active={activeTab === 'curation'} onClick={() => setActiveTab('curation')} label="Archive" icon={<Layers size={14}/>} />
        </nav>

        <div className="flex items-center gap-4">
          <button className="p-3 rounded-2xl bg-white/5 text-slate-500 hover:text-white transition-all"><Settings size={18}/></button>
          <button className="px-6 py-3 rounded-2xl bg-indigo-500 text-white font-black text-[10px] uppercase tracking-widest shadow-xl shadow-indigo-500/20 hover:bg-indigo-400 transition-all">Export Schema</button>
        </div>
      </header>

      {/* 2. MAIN CONTENT AREA */}
      <main className="flex-1 overflow-y-auto custom-scrollbar p-10">
        <div className="max-w-[1600px] mx-auto space-y-12">
          
          {activeTab === 'overview' && (
            <div className="space-y-10 animate-in slide-in-from-bottom-4 duration-500">
              <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                <StatCard label="Canonical Library" value={stats.totalCanonicalWorks.toLocaleString()} trend="+142 this week" icon={<Globe size={20}/>} />
                <StatCard label="Data Discrepancies" value={stats.pendingConflicts.toString()} trend="Requires Action" icon={<ShieldAlert size={20}/>} alert />
                <StatCard label="Relational Mapping" value="94.2%" trend="Author Consistency" icon={<Link2 size={20}/>} />
                <StatCard label="User Library Nodes" value="48.2k" trend="+1.2% activity" icon={<Users size={20}/>} />
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                <div className="lg:col-span-2 glass rounded-[2.5rem] p-10 border-white/5 space-y-8">
                  <div className="flex items-center justify-between">
                    <h3 className="text-xl font-black text-white tracking-tight uppercase">Recent Data Ingestions</h3>
                    <button className="text-indigo-400 text-[10px] font-black uppercase tracking-widest hover:underline">View Pipeline</button>
                  </div>
                  <div className="space-y-4">
                    {[1, 2, 3, 4].map(i => (
                      <div key={i} className="flex items-center justify-between p-5 rounded-2xl bg-white/[0.02] border border-white/5 hover:bg-white/[0.04] transition-all group">
                         <div className="flex items-center gap-5">
                            <div className="w-10 h-10 rounded-xl bg-slate-900 border border-white/5 flex items-center justify-center">
                               <RefreshCw size={18} className="text-indigo-500" />
                            </div>
                            <div>
                               <p className="text-sm font-bold text-white">Google API Sync #{4820 + i}</p>
                               <p className="text-[10px] text-slate-500 font-bold uppercase">14 Volumes processed • 0.2ms latency</p>
                            </div>
                         </div>
                         <div className="flex items-center gap-6">
                            <span className="text-[10px] font-black text-emerald-500 uppercase">Success</span>
                            <ChevronRight size={16} className="text-slate-700 group-hover:text-indigo-400 transition-all" />
                         </div>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="glass rounded-[2.5rem] p-10 border-white/5 space-y-8 flex flex-col justify-between">
                  <div>
                    <h3 className="text-xl font-black text-white tracking-tight uppercase mb-2">Schema Integrity</h3>
                    <p className="text-slate-500 text-sm font-medium">Automatic validation against OpenLibrary and Google datasets.</p>
                  </div>
                  
                  <div className="flex-1 flex flex-col justify-center items-center py-10">
                     <div className="relative">
                        <div className="w-32 h-32 rounded-full border-[10px] border-indigo-500/10 border-t-indigo-500 animate-spin" style={{ animationDuration: '3s' }} />
                        <div className="absolute inset-0 flex flex-col items-center justify-center">
                           <span className="text-2xl font-black text-white">{stats.databaseHealth}%</span>
                           <span className="text-[8px] font-black text-slate-500 uppercase">Status</span>
                        </div>
                     </div>
                  </div>

                  <button className="w-full py-4 rounded-2xl bg-white/5 border border-white/10 text-white font-black text-[10px] uppercase tracking-widest hover:bg-white/10 transition-all">
                    Run Validation Protocol
                  </button>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'conflicts' && (
            <div className="space-y-10 animate-in slide-in-from-bottom-4 duration-500">
               <header className="flex items-center justify-between">
                 <div>
                    <h2 className="text-4xl font-black text-white tracking-tighter uppercase mb-2">Data <span className="text-rose-500">Conflicts</span></h2>
                    <p className="text-slate-500 font-medium">Manual intervention required for {conflicts.length} ambiguous entries.</p>
                 </div>
                 <div className="flex gap-4">
                    <button className="px-6 py-3 rounded-2xl bg-white/5 border border-white/5 text-slate-400 font-bold text-xs">Ignore Minor</button>
                    <button className="px-6 py-3 rounded-2xl bg-indigo-500 text-white font-black text-xs uppercase tracking-widest">Resolve All Auto</button>
                 </div>
               </header>

               <div className="grid grid-cols-1 gap-6">
                 {conflicts.map(conflict => (
                   <div key={conflict.id} className="glass rounded-[2rem] border-white/5 overflow-hidden flex flex-col lg:flex-row shadow-2xl">
                      <div className="lg:w-72 bg-slate-950 p-8 flex flex-col items-center border-r border-white/5">
                         <img src={conflict.bookCover} className="w-24 h-36 rounded-xl shadow-2xl mb-6 ring-1 ring-white/10" />
                         <h4 className="text-sm font-black text-white text-center mb-1">{conflict.bookTitle}</h4>
                         <span className="text-[9px] font-black text-indigo-400 uppercase tracking-widest">Ambiguity in {conflict.field}</span>
                      </div>
                      
                      <div className="flex-1 grid grid-cols-1 md:grid-cols-2 p-1 shadow-inner bg-black/40">
                         <ConflictSource 
                           source={conflict.sourceA} 
                           field={conflict.field} 
                           active={true}
                         />
                         <ConflictSource 
                           source={conflict.sourceB} 
                           field={conflict.field} 
                         />
                      </div>

                      <div className="lg:w-64 p-8 flex flex-col justify-center gap-3">
                         <button className="w-full py-4 rounded-2xl bg-emerald-500 text-white font-black text-[10px] uppercase tracking-widest shadow-xl shadow-emerald-500/20 hover:scale-105 transition-all">Confirm A</button>
                         <button className="w-full py-4 rounded-2xl bg-white/5 border border-white/10 text-white font-black text-[10px] uppercase tracking-widest hover:bg-white/10">Use B</button>
                         <button className="w-full py-3 rounded-2xl text-slate-600 font-black text-[9px] uppercase tracking-widest hover:text-rose-500 transition-colors">Discard Both</button>
                      </div>
                   </div>
                 ))}
               </div>
            </div>
          )}

          {activeTab === 'authors' && (
            <div className="space-y-10 animate-in slide-in-from-bottom-4 duration-500">
               <header>
                  <h2 className="text-4xl font-black text-white tracking-tighter uppercase mb-2">Author <span className="text-indigo-500">Synchronizer</span></h2>
                  <p className="text-slate-500 font-medium">Merge variations and link creators to their canonical masterpieces.</p>
               </header>

               <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                  {authorCandidates.map(auth => (
                    <div key={auth.id} className="glass rounded-[2.5rem] border-white/5 p-10 space-y-8 group hover:border-indigo-500/20 transition-all">
                       <div className="flex items-center justify-between">
                          <div className="flex items-center gap-6">
                             <div className="w-14 h-14 rounded-2xl bg-gradient-to-tr from-indigo-500 to-purple-600 p-0.5">
                                <div className="w-full h-full rounded-2xl bg-slate-900 flex items-center justify-center font-black text-xl text-white">
                                  {auth.primaryName.charAt(0)}
                                </div>
                             </div>
                             <div>
                                <h3 className="text-xl font-black text-white">{auth.primaryName}</h3>
                                <p className="text-[10px] font-black text-indigo-400 uppercase tracking-widest">{auth.bookCount} Associated Works</p>
                             </div>
                          </div>
                          <div className="text-right">
                             <p className="text-[9px] font-black text-slate-600 uppercase tracking-widest">Last Activity</p>
                             <p className="text-xs font-bold text-slate-400">{auth.lastIngested}</p>
                          </div>
                       </div>

                       <div className="p-6 rounded-2xl bg-black/40 border border-white/5 space-y-4">
                          <p className="text-[10px] font-black text-slate-500 uppercase tracking-widest mb-2">Duplicate Variations Detected:</p>
                          {auth.variants.map((v, i) => (
                            <div key={i} className="flex items-center justify-between p-3 rounded-xl bg-white/[0.02] border border-white/5">
                               <div className="flex items-center gap-3">
                                  <AlertTriangle size={12} className="text-amber-500" />
                                  <span className="text-sm font-medium text-slate-300">{v}</span>
                               </div>
                               <button className="text-[9px] font-black text-indigo-500 uppercase hover:underline">Link</button>
                            </div>
                          ))}
                       </div>

                       <div className="flex gap-4">
                          <button className="flex-1 py-4 rounded-2xl bg-indigo-500 text-white font-black text-[10px] uppercase tracking-widest shadow-xl shadow-indigo-500/20 flex items-center justify-center gap-2">
                             <GitMerge size={16}/> Perform Merge
                          </button>
                          <button className="px-6 py-4 rounded-2xl bg-white/5 border border-white/10 text-white font-black text-[10px] uppercase tracking-widest hover:bg-white/10 transition-all">
                             View Bibliography
                          </button>
                       </div>
                    </div>
                  ))}
               </div>
            </div>
          )}

          {activeTab === 'curation' && (
            <div className="space-y-10 animate-in slide-in-from-bottom-4 duration-500">
               <div className="flex flex-col md:flex-row md:items-end justify-between gap-8">
                  <div>
                    <h2 className="text-4xl font-black text-white tracking-tighter uppercase mb-2">Digital <span className="text-indigo-500">Curation</span></h2>
                    <p className="text-slate-500 font-medium">Manually append volumes or correct metadata for restricted titles.</p>
                  </div>
                  <button className="group flex items-center gap-3 px-8 py-5 rounded-2xl bg-indigo-500 text-white font-bold shadow-xl shadow-indigo-500/20 hover:bg-indigo-400 active:scale-95 transition-all">
                    <Plus size={24} className="group-hover:rotate-90 transition-transform duration-300" />
                    Manually Ingest Volume
                  </button>
               </div>

               <div className="glass rounded-[2.5rem] border-white/5 overflow-hidden">
                  <div className="p-8 border-b border-white/5 flex items-center justify-between bg-white/[0.02]">
                    <div className="flex items-center gap-4">
                       <Search className="text-slate-600" size={18} />
                       <input 
                         type="text" 
                         placeholder="Search global repository..."
                         className="bg-transparent border-none text-white outline-none text-sm w-96"
                       />
                    </div>
                    <div className="flex items-center gap-2">
                       <CuratorFilter active label="All Ingestions" />
                       <CuratorFilter label="Pending Approval" />
                       <CuratorFilter label="Restricted" />
                    </div>
                  </div>
                  <div className="divide-y divide-white/5">
                     {[1,2,3,4,5,6].map(i => (
                       <div key={i} className="p-6 flex items-center justify-between hover:bg-white/[0.01] transition-all">
                          <div className="flex items-center gap-6 flex-1">
                             <div className="w-10 h-14 rounded bg-slate-900 border border-white/10 shrink-0" />
                             <div>
                                <h4 className="text-sm font-bold text-white">Advanced Engineering Philosophy Vol {i}</h4>
                                <p className="text-xs text-slate-500">Lumina Editorial Team • Hardcover</p>
                             </div>
                          </div>
                          <div className="flex items-center gap-12">
                             <div className="text-right">
                                <p className="text-[10px] font-black text-slate-600 uppercase tracking-widest">Metadata</p>
                                <p className="text-xs font-bold text-emerald-500">Verified</p>
                             </div>
                             <div className="text-right">
                                <p className="text-[10px] font-black text-slate-600 uppercase tracking-widest">Linked</p>
                                <p className="text-xs font-bold text-white">4 Editions</p>
                             </div>
                             <button className="p-3 rounded-xl hover:bg-white/5 text-slate-500 transition-all"><Settings size={16}/></button>
                          </div>
                       </div>
                     ))}
                  </div>
               </div>
            </div>
          )}

        </div>
      </main>
    </div>
  );
};

const AdminTab = ({ active, onClick, label, icon, badge }: { active: boolean, onClick: () => void, label: string, icon: any, badge?: string }) => (
  <button 
    onClick={onClick}
    className={`px-5 py-2.5 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all flex items-center gap-2 ${
      active ? 'bg-indigo-500 text-white shadow-lg' : 'text-slate-500 hover:text-slate-300'
    }`}
  >
    {icon}
    {label}
    {badge && (
      <span className={`px-1.5 py-0.5 rounded-md text-[8px] ${active ? 'bg-white text-indigo-500' : 'bg-rose-500 text-white shadow-[0_0_10px_#f43f5e]'}`}>
        {badge}
      </span>
    )}
  </button>
);

const StatCard = ({ label, value, trend, icon, alert = false }: { label: string, value: string, trend: string, icon: any, alert?: boolean }) => (
  <div className={`p-8 rounded-[2.5rem] glass border-white/5 bg-white/[0.03] transition-all hover:bg-white/[0.05] group ${alert ? 'hover:border-rose-500/20' : 'hover:border-indigo-500/20'}`}>
    <div className="flex items-center justify-between mb-6">
      <div className={`p-3 rounded-2xl bg-white/5 border border-white/10 group-hover:scale-110 transition-all ${alert ? 'text-rose-500' : 'text-indigo-400'}`}>
        {icon}
      </div>
      <span className={`text-[8px] font-black px-2 py-0.5 rounded uppercase tracking-widest ${alert ? 'bg-rose-500/10 text-rose-500' : 'bg-emerald-500/10 text-emerald-500'}`}>
        {trend}
      </span>
    </div>
    <p className="text-[10px] font-black text-slate-600 uppercase tracking-widest mb-1">{label}</p>
    <p className="text-3xl font-black text-white tracking-tighter">{value}</p>
  </div>
);

const ConflictSource = ({ source, field, active = false }: { source: any, field: string, active?: boolean }) => (
  <div className={`p-10 transition-all border-2 rounded-[2rem] ${active ? 'bg-indigo-500/5 border-indigo-500/20' : 'bg-transparent border-transparent'}`}>
     <div className="flex items-center justify-between mb-8">
        <div>
           <p className="text-[9px] font-black text-slate-600 uppercase tracking-widest mb-1">Provider Source</p>
           <p className="text-sm font-bold text-white uppercase tracking-tighter">{source.provider}</p>
        </div>
        {active && <div className="px-3 py-1 rounded-full bg-indigo-500 text-white text-[8px] font-black uppercase tracking-widest">Recommended</div>}
     </div>
     
     <div className="space-y-2">
        <p className="text-[10px] font-black text-slate-500 uppercase tracking-widest">{field}</p>
        <p className={`text-2xl font-black tracking-tight ${active ? 'text-indigo-400' : 'text-slate-300'}`}>{source.value}</p>
     </div>
  </div>
);

const CuratorFilter = ({ label, active = false }: { label: string, active?: boolean }) => (
  <button className={`px-4 py-1.5 rounded-lg text-[9px] font-black uppercase tracking-widest transition-all ${
    active ? 'bg-white/10 text-white' : 'text-slate-600 hover:text-slate-400'
  }`}>
    {label}
  </button>
);
