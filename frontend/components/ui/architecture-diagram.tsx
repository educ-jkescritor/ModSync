"use client";

import { useState } from "react";
import { BrainCircuit, Search, BookOpen, TrendingUp, Bot, FileText, ArrowRight, LayoutDashboard, DatabaseZap, X, Network, Link2, CheckCircle2, AlertTriangle, Layers } from "lucide-react";

const MOCK_DATA: Record<string, any> = {
  "input": {
    filename: "week-3-frontend.pdf",
    pages: 12,
    images_detected: 3,
    status: "uploaded"
  },
  "agent-1": {
    name: "Document Analysis Agent",
    status: "processing complete",
    multimodal_insights: [
      "Page 4: Text describes class components.",
      "Page 5: Architecture diagram showing Webpack pipeline.",
      "Page 8: Screenshot of a create-react-app terminal output."
    ],
    semantic_summary: "Module teaches introductory React, focusing on CRA, Webpack, and Class Components."
  },
  "agent-2": {
    name: "Tech Detection Agent",
    status: "entities extracted",
    detected_technologies: [
      { name: "React", version: "<16.8" },
      { name: "create-react-app", version: "n/a" },
      { name: "Webpack", version: "4.x" }
    ]
  },
  "agent-3": {
    name: "Lifecycle Validation Agent",
    status: "database queried",
    lifecycle_checks: [
      { tech: "React <16.8", status: "Legacy (Pre-hooks)" },
      { tech: "create-react-app", status: "Deprecated by React team" },
      { tech: "Webpack 4", status: "EOL (End of Life)" }
    ]
  },
  "agent-4": {
    name: "Industry Trend Agent",
    status: "market data retrieved",
    market_insights: [
      { tech: "create-react-app", modern_alternative: "Vite or Next.js" },
      { tech: "React <16.8", modern_alternative: "Functional Components with Hooks" }
    ]
  },
  "agent-5": {
    name: "Educational Context Agent",
    status: "context analyzed",
    findings: {
      appears_in_lab: true,
      lab_friction_risk: "High",
      reason: "Students will get deprecation warnings installing create-react-app. Class components do not align with modern entry-level job requirements."
    }
  },
  "agent-6": {
    name: "Recommendation Agent",
    status: "report synthesized",
    final_actions: [
      "Replace 'create-react-app' lab with 'npm create vite@latest'.",
      "Update Page 4-8 code examples to use React Hooks instead of Class Components."
    ],
    verified_links: [
      "https://react.dev/learn/your-first-component",
      "https://vitejs.dev/guide/"
    ]
  },
  "output": {
    report_status: "Generated",
    faculty_validation_required: true,
    total_priority_score: 85,
    risk_level: "High"
  }
};

export function MultiAgentArchitecture() {
  const [activeNode, setActiveNode] = useState<string | null>(null);

  const toggleNode = (id: string) => {
    setActiveNode(activeNode === id ? null : id);
  };

  return (
    <div className="bg-white border border-border rounded-xl p-6 shadow-sm mb-6 mt-6">
      <h2 className="text-xl font-bold mb-2 flex items-center gap-2">
        <BrainCircuit className="w-6 h-6 text-primary" />
        ModSync Interactive Mindmap
      </h2>
      <p className="text-sm text-muted-foreground mb-8">
        Click on any node below to simulate peeking into the agent's real-time data context, similar to Obsidian's graph view.
      </p>

      <div className="flex flex-col xl:flex-row gap-6 items-center justify-between overflow-x-auto pb-4 px-2">
        {/* Input */}
        <div 
          onClick={() => toggleNode("input")}
          className={`flex flex-col items-center min-w-[140px] cursor-pointer transition-all duration-200 hover:scale-105 ${activeNode === "input" ? "ring-2 ring-slate-400 rounded-xl bg-slate-50 p-2 shadow-md" : "p-2"}`}
        >
          <div className="w-16 h-16 rounded-full bg-slate-50 flex items-center justify-center border-2 border-slate-200 shadow-sm">
            <FileText className="w-8 h-8 text-slate-500" />
          </div>
          <span className="mt-3 font-semibold text-sm text-center">Course Module</span>
          <span className="text-[11px] font-medium px-2 py-0.5 bg-slate-100 rounded-full text-slate-500 mt-1">Raw PDF & Images</span>
        </div>

        <ArrowRight className="text-slate-300 hidden xl:block flex-shrink-0" />

        {/* Central Orchestrator / Document Agent */}
        <div 
          onClick={() => toggleNode("agent-1")}
          className={`flex flex-col items-center min-w-[160px] cursor-pointer transition-all duration-200 hover:scale-105 ${activeNode === "agent-1" ? "ring-2 ring-indigo-400 rounded-xl bg-indigo-50/50 p-2 shadow-md" : "p-2"}`}
        >
          <div className="w-20 h-20 rounded-full bg-indigo-50 flex items-center justify-center border-2 border-indigo-400 shadow-sm relative">
            <Search className="w-10 h-10 text-indigo-600" />
            <div className="absolute -top-2 -right-2 bg-indigo-100 text-indigo-800 text-[10px] font-bold px-2 py-0.5 rounded-full border border-indigo-200">Agent 1</div>
          </div>
          <span className="mt-3 font-bold text-sm text-center">Document Analysis</span>
          <span className="text-xs text-muted-foreground text-center leading-tight mt-1">Retrieves multimodal data<br/>Outputs page summaries</span>
        </div>

        <ArrowRight className="text-slate-300 hidden xl:block flex-shrink-0" />

        {/* Specialized Agents */}
        <div className="flex flex-col gap-3 min-w-[280px]">
          <AgentCard 
            id="agent-2"
            icon={Bot} 
            num="2"
            title="Tech Detection Agent" 
            desc="Identifies tools & frameworks" 
            retrieves="Retrieves: Semantic Page Contexts" 
            isActive={activeNode === "agent-2"}
            onClick={() => toggleNode("agent-2")}
          />
          <AgentCard 
            id="agent-3"
            icon={DatabaseZap} 
            num="3"
            title="Lifecycle Validation Agent" 
            desc="Queries external EOL databases" 
            retrieves="Retrieves: Detected Tech List" 
            isActive={activeNode === "agent-3"}
            onClick={() => toggleNode("agent-3")}
          />
          <AgentCard 
            id="agent-4"
            icon={TrendingUp} 
            num="4"
            title="Industry Trend Agent" 
            desc="Scans job markets & tech radars" 
            retrieves="Retrieves: Detected Tech List" 
            isActive={activeNode === "agent-4"}
            onClick={() => toggleNode("agent-4")}
          />
          <AgentCard 
            id="agent-5"
            icon={BookOpen} 
            num="5"
            title="Educational Context Agent" 
            desc="Analyzes teaching methods (e.g. Labs)" 
            retrieves="Retrieves: Semantic Page Contexts" 
            isActive={activeNode === "agent-5"}
            onClick={() => toggleNode("agent-5")}
          />
        </div>

        <ArrowRight className="text-slate-300 hidden xl:block flex-shrink-0" />

        {/* Output Synthesizer */}
        <div 
          onClick={() => toggleNode("agent-6")}
          className={`flex flex-col items-center min-w-[180px] cursor-pointer transition-all duration-200 hover:scale-105 ${activeNode === "agent-6" ? "ring-2 ring-teal-400 rounded-xl bg-teal-50/50 p-2 shadow-md" : "p-2"}`}
        >
          <div className="w-20 h-20 rounded-full bg-teal-50 flex items-center justify-center border-2 border-teal-400 shadow-sm relative">
            <BrainCircuit className="w-10 h-10 text-teal-600" />
            <div className="absolute -top-2 -right-2 bg-teal-100 text-teal-800 text-[10px] font-bold px-2 py-0.5 rounded-full border border-teal-200">Agent 6</div>
          </div>
          <span className="mt-3 font-bold text-sm text-center">Recommendation Agent</span>
          <span className="text-xs text-muted-foreground text-center leading-tight mt-1">Retrieves all agent outputs<br/>Searches official doc links</span>
        </div>

        <ArrowRight className="text-slate-300 hidden xl:block flex-shrink-0" />

        {/* Output */}
        <div 
          onClick={() => toggleNode("output")}
          className={`flex flex-col items-center min-w-[140px] cursor-pointer transition-all duration-200 hover:scale-105 ${activeNode === "output" ? "ring-2 ring-green-400 rounded-xl bg-green-50/50 p-2 shadow-md" : "p-2"}`}
        >
          <div className="w-16 h-16 rounded-full bg-green-50 flex items-center justify-center border-2 border-green-300 shadow-sm">
            <LayoutDashboard className="w-8 h-8 text-green-600" />
          </div>
          <span className="mt-3 font-semibold text-sm text-center">ModSync UI</span>
          <span className="text-[11px] font-medium px-2 py-0.5 bg-green-100 border border-green-200 rounded-full text-green-700 mt-1">Final Verified Report</span>
        </div>
      </div>

      {/* Visual Data Panel */}
      {activeNode && MOCK_DATA[activeNode] && (
        <div className="mt-8 p-6 bg-slate-50/80 backdrop-blur-sm rounded-xl border border-slate-200 shadow-inner relative animate-in fade-in slide-in-from-top-4 duration-300">
          <button 
            onClick={() => setActiveNode(null)}
            className="absolute top-4 right-4 text-slate-400 hover:text-slate-700 transition-colors bg-white p-1 rounded-full shadow-sm border border-slate-200"
          >
            <X className="w-5 h-5" />
          </button>
          
          <div className="flex items-center gap-2 mb-6">
            <Network className="w-5 h-5 text-indigo-600" />
            <h3 className="text-slate-800 font-bold text-lg">
              {activeNode.includes('agent') ? MOCK_DATA[activeNode].name : (activeNode === 'input' ? 'Ingestion Payload' : 'Final Output Payload')}
            </h3>
            <span className="px-2.5 py-0.5 bg-indigo-100 text-indigo-700 text-[11px] font-bold uppercase tracking-wide rounded-full ml-2">
              {MOCK_DATA[activeNode].status || "Live"}
            </span>
          </div>

          {/* Render Data as Visual Nodes */}
          <VisualDataRenderer data={MOCK_DATA[activeNode]} />
          
        </div>
      )}
    </div>
  );
}

function AgentCard({ id, icon: Icon, num, title, desc, retrieves, isActive, onClick }: any) {
  return (
    <div 
      onClick={onClick}
      className={`flex items-center gap-3 bg-slate-50 border p-3 rounded-xl shadow-sm hover:shadow-md cursor-pointer transition-all duration-200 hover:-translate-y-0.5 relative overflow-hidden ${isActive ? 'border-indigo-400 ring-2 ring-indigo-400 bg-indigo-50/30' : 'border-slate-200'}`}
    >
      <div className={`absolute top-0 left-0 w-1 h-full ${isActive ? 'bg-indigo-600' : 'bg-indigo-400'}`}></div>
      <div className="bg-white p-2.5 rounded-lg shadow-sm border border-slate-100 relative">
        <Icon className="w-5 h-5 text-indigo-600" />
        <div className="absolute -top-2 -right-2 bg-indigo-100 text-indigo-700 text-[9px] font-bold w-4 h-4 flex items-center justify-center rounded-full border border-indigo-200">{num}</div>
      </div>
      <div className="flex flex-col">
        <span className="text-sm font-bold text-slate-800">{title}</span>
        <span className="text-[11px] text-slate-500 leading-tight mb-1">{desc}</span>
        <span className="text-[10px] text-indigo-600 font-semibold bg-indigo-50 border border-indigo-100 w-fit px-1.5 py-0.5 rounded">{retrieves}</span>
      </div>
    </div>
  );
}

function VisualDataRenderer({ data }: { data: any }) {
  // Filter out top-level name/status as they are in the header
  const renderData = { ...data };
  delete renderData.name;
  delete renderData.status;

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {Object.entries(renderData).map(([key, value]) => {
        const label = key.replace(/_/g, " ").toUpperCase();
        
        // Handle Arrays
        if (Array.isArray(value)) {
          return (
            <div key={key} className="bg-white rounded-xl p-4 border border-slate-200 shadow-sm col-span-1 md:col-span-2">
              <span className="text-slate-500 text-xs font-bold tracking-wider flex items-center gap-1.5 mb-3">
                <Layers className="w-3.5 h-3.5" />
                {label}
              </span>
              <div className="flex flex-wrap gap-3">
                {value.map((item, i) => (
                   typeof item === 'object' ? (
                     // Mini object cards inside array
                     <div key={i} className="bg-slate-50 border border-slate-200 rounded-lg p-3 text-sm flex flex-col gap-2 w-full md:w-[calc(50%-0.5rem)] lg:w-[calc(33.33%-0.5rem)]">
                        {Object.entries(item).map(([k, v]) => (
                           <div key={k} className="flex flex-col">
                             <span className="text-slate-400 text-[10px] uppercase font-bold">{k.replace(/_/g, " ")}:</span>
                             <span className="text-slate-800 font-medium">{String(v)}</span>
                           </div>
                        ))}
                     </div>
                   ) : (
                     // Simple pills for strings
                     <div key={i} className="flex items-start gap-2 bg-indigo-50 border border-indigo-100 px-3 py-2 rounded-lg text-sm text-indigo-900 shadow-sm w-full md:w-auto">
                       {String(item).startsWith('http') ? (
                         <>
                           <Link2 className="w-4 h-4 text-indigo-400 mt-0.5" />
                           <a href={String(item)} className="hover:underline break-all">{String(item)}</a>
                         </>
                       ) : (
                         <>
                           <CheckCircle2 className="w-4 h-4 text-indigo-400 mt-0.5 flex-shrink-0" />
                           <span>{String(item)}</span>
                         </>
                       )}
                     </div>
                   )
                ))}
              </div>
            </div>
          )
        }

        // Handle Objects
        if (typeof value === 'object' && value !== null) {
          return (
            <div key={key} className="bg-white rounded-xl p-4 border border-slate-200 shadow-sm">
              <span className="text-slate-500 text-xs font-bold tracking-wider flex items-center gap-1.5 mb-3">
                <DatabaseZap className="w-3.5 h-3.5" />
                {label}
              </span>
              <div className="flex flex-col gap-3 bg-slate-50 rounded-lg p-3 border border-slate-100">
                 {Object.entries(value).map(([k, v]) => (
                   <div key={k} className="flex flex-col pb-2 border-b border-slate-200 last:border-0 last:pb-0">
                     <span className="text-slate-400 text-[10px] uppercase font-bold">{k.replace(/_/g, " ")}</span>
                     <span className="text-slate-800 text-sm font-medium">
                       {typeof v === 'boolean' ? (v ? 'Yes' : 'No') : String(v)}
                     </span>
                   </div>
                 ))}
              </div>
            </div>
          )
        }

        // Handle Primitives (Strings/Numbers)
        return (
          <div key={key} className="bg-white rounded-xl p-4 border border-slate-200 shadow-sm flex flex-col justify-center">
            <span className="text-slate-500 text-xs font-bold tracking-wider mb-1">{label}</span>
            <span className="text-slate-800 text-lg font-bold">{String(value)}</span>
          </div>
        );
      })}
    </div>
  )
}
