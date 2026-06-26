"use client";

import { ChangeEvent, DragEvent, useMemo, useRef, useState } from "react";
import {
  AlertCircle,
  BookOpen,
  CheckCircle2,
  ChevronDown,
  ClipboardCheck,
  Download,
  FileSearch,
  FileText,
  Filter,
  Lightbulb,
  ListChecks,
  Loader2,
  Search,
  ShieldCheck,
  Upload,
  X
} from "lucide-react";
import { analyzePdf } from "@/lib/api";

import type { Recommendation, ReviewPriority, ReviewReport } from "@/lib/types";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Progress } from "@/components/ui/progress";
import { cn } from "@/lib/utils";

type Stage = "idle" | "uploading" | "extracting" | "analyzing" | "complete" | "error";
type FilterValue = "All" | ReviewPriority;

const stages: { id: Stage; label: string; progress: number }[] = [
  { id: "uploading", label: "PDF received", progress: 25 },
  { id: "extracting", label: "Text extracted", progress: 55 },
  { id: "analyzing", label: "Review candidates prepared", progress: 82 },
  { id: "complete", label: "Report ready", progress: 100 }
];

export default function Home() {
  const inputRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const [stage, setStage] = useState<Stage>("idle");
  const [error, setError] = useState<string | null>(null);
  const [report, setReport] = useState<ReviewReport | null>(null);
  const [debugPages, setDebugPages] = useState<any[] | null>(null);
  const [priorityFilter, setPriorityFilter] = useState<FilterValue>("All");
  const [query, setQuery] = useState("");
  const [expandedImage, setExpandedImage] = useState<string | null>(null);

  const progress = stages.find((item) => item.id === stage)?.progress ?? 0;

  const filteredRecommendations = useMemo(() => {
    const recommendations = report?.recommendations ?? [];
    return recommendations.filter((item) => {
      const priorityMatches = priorityFilter === "All" || item.review_priority === priorityFilter;
      const queryMatches = item.technology.toLowerCase().includes(query.trim().toLowerCase());
      return priorityMatches && queryMatches;
    });
  }, [priorityFilter, query, report]);

  function selectFile(candidate: File | null) {
    if (!candidate) return;
    if (!candidate.name.toLowerCase().endsWith(".pdf") && candidate.type !== "application/pdf") {
      setError("Only PDF files are accepted.");
      return;
    }
    setFile(candidate);
    setError(null);
  }

  function onFileChange(event: ChangeEvent<HTMLInputElement>) {
    selectFile(event.target.files?.[0] ?? null);
  }

  function onDrop(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
    setDragActive(false);
    selectFile(event.dataTransfer.files?.[0] ?? null);
  }

  async function runAnalysis() {
    if (!file) {
      setError("Select a PDF module first.");
      return;
    }

    setError(null);
    setReport(null);
    setDebugPages(null);
    setStage("uploading");
    const extractTimer = window.setTimeout(() => setStage("extracting"), 450);
    const analysisTimer = window.setTimeout(() => setStage("analyzing"), 950);

    try {
      const result = await analyzePdf(file) as any;
      if (result.debug_pages) {
        setDebugPages(result.debug_pages);
      } else {
        setReport(result);
      }
      setStage("complete");
    } catch (analysisError) {
      setStage("error");
      setError(
        analysisError instanceof Error
          ? analysisError.message
          : "The review report could not be generated."
      );
    } finally {
      window.clearTimeout(extractTimer);
      window.clearTimeout(analysisTimer);
    }
  }

  async function loadDemoReport() {
    setError(null);
    setStage("analyzing");
    try {
      const response = await fetch("/sample-review-output.json");
      if (!response.ok) throw new Error("Demo report is not available.");
      const result = (await response.json()) as ReviewReport;
      setReport(result);
      setStage("complete");
      setFile(null);
    } catch (demoError) {
      setStage("error");
      setError(demoError instanceof Error ? demoError.message : "Demo report failed to load.");
    }
  }

  async function handleExportFinetuning() {
    try {
      const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
      const link = document.createElement("a");
      link.href = `${API_BASE_URL}/api/export-finetuning`;
      link.setAttribute("download", "modsync_finetuning_dataset.jsonl");
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    } catch (e) {
      console.error(e);
      alert("Failed to export dataset.");
    }
  }

  return (
    <main className="min-h-screen">
      <section className="border-b border-border bg-white">
        <div className="mx-auto flex max-w-7xl flex-col gap-4 px-5 py-5 md:flex-row md:items-center md:justify-between">
          <div>
            <h1 className="text-2xl font-semibold text-foreground md:text-3xl">
              ModSync
            </h1>
            <p className="mt-1 max-w-3xl text-sm text-muted-foreground">
              Review recommendations for technologies, references, and instructional contexts in PDF modules.
            </p>
          </div>
          <Badge tone="neutral" className="w-fit gap-2">
            <ShieldCheck className="h-4 w-4" />
            Faculty validation required
          </Badge>
        </div>
      </section>

      <section className="mx-auto grid max-w-7xl gap-5 px-5 py-6 lg:grid-cols-[minmax(0,1fr)_380px]">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Upload className="h-5 w-5 text-primary" />
              Upload PDF module
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div
              role="button"
              tabIndex={0}
              onClick={() => inputRef.current?.click()}
              onKeyDown={(event) => {
                if (event.key === "Enter" || event.key === " ") inputRef.current?.click();
              }}
              onDragOver={(event) => {
                event.preventDefault();
                setDragActive(true);
              }}
              onDragLeave={() => setDragActive(false)}
              onDrop={onDrop}
              className={cn(
                "flex min-h-56 cursor-pointer flex-col items-center justify-center rounded-md border border-dashed border-border bg-muted/45 p-6 text-center transition",
                dragActive && "border-primary bg-teal-50"
              )}
            >
              <FileText className="mb-4 h-12 w-12 text-primary" />
              <p className="text-base font-semibold">
                {file ? file.name : "Drop a PDF module here"}
              </p>
              <p className="mt-2 text-sm text-muted-foreground">PDF only</p>
              <input
                ref={inputRef}
                type="file"
                accept="application/pdf,.pdf"
                className="hidden"
                onChange={onFileChange}
              />
            </div>

            <div className="mt-5 flex flex-col gap-3 sm:flex-row">
              <Button onClick={runAnalysis} disabled={!file || stage === "uploading" || stage === "extracting" || stage === "analyzing"}>
                {stage === "uploading" || stage === "extracting" || stage === "analyzing" ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <FileSearch className="h-4 w-4" />
                )}
                Generate review report
              </Button>
              
              {file && (
                <Button variant="ghost" onClick={() => setFile(null)} aria-label="Clear selected file">
                  <X className="h-4 w-4" />
                  Clear
                </Button>
              )}
            </div>

            {error && (
              <div className="mt-4 flex items-start gap-2 rounded-md border border-rose-200 bg-rose-50 p-3 text-sm text-danger">
                <AlertCircle className="mt-0.5 h-4 w-4 flex-none" />
                <span>{error}</span>
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileSearch className="h-5 w-5 text-primary" />
              Processing
            </CardTitle>
          </CardHeader>
          <CardContent>
            <Progress value={progress} />
            <div className="mt-5 space-y-4">
              {stages.map((item) => {
                const activeIndex = stages.findIndex((step) => step.id === stage);
                const itemIndex = stages.findIndex((step) => step.id === item.id);
                const complete = stage === "complete" || (activeIndex >= itemIndex && stage !== "error");
                const current = stage === item.id && stage !== "complete";

                return (
                  <div key={item.id} className="flex items-center gap-3">
                    <span
                      className={cn(
                        "flex h-8 w-8 items-center justify-center rounded-md border",
                        complete
                          ? "border-primary bg-teal-50 text-primary"
                          : "border-border bg-white text-muted-foreground"
                      )}
                    >
                      {current ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : complete ? (
                        <CheckCircle2 className="h-4 w-4" />
                      ) : (
                        <span className="h-2 w-2 rounded-md bg-current" />
                      )}
                    </span>
                    <span className="text-sm font-medium">{item.label}</span>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>
      </section>

      {report && (
        <section className="mx-auto max-w-7xl px-5 pb-8">
          <div className="mb-5 grid gap-3 md:grid-cols-4">
            <SummaryTile label="Pages analyzed" value={report.pages_analyzed} />
            <SummaryTile label="Relevant pages" value={report.summary.relevant_pages_count} />
            <SummaryTile label="Technologies" value={report.summary.technology_count} />
            <SummaryTile label="High priority" value={report.summary.high_priority_count} tone="high" />
          </div>

          <div className="my-6">
            <h2 className="text-xl font-semibold text-foreground">ModSync Course Alignment Findings</h2>
            <p className="text-xs text-muted-foreground mt-1">Review automated modernization suggestions, examine exact syllabus quotes, and log faculty feedback.</p>
          </div>

          <div className="mb-5 flex flex-col gap-3 rounded-md border border-border bg-white p-4 md:flex-row md:items-center md:justify-between">
            <div className="flex flex-wrap items-center gap-2">
              {(["All", "High", "Medium", "Low"] as FilterValue[]).map((item) => (
                <Button
                  key={item}
                  size="sm"
                  variant={priorityFilter === item ? "default" : "secondary"}
                  onClick={() => setPriorityFilter(item)}
                >
                  <Filter className="h-4 w-4" />
                  {item}
                </Button>
              ))}
              {/* <div className="h-6 w-px bg-border mx-1 hidden sm:block" />
              <Button
                size="sm"
                variant="outline"
                onClick={handleExportFinetuning}
                className="gap-2 border-primary/20 text-primary hover:bg-teal-50 hover:text-primary-dark"
              >
                <Download className="h-4 w-4" />
                Export Fine-Tuning Dataset
              </Button> */}
            </div>
            <div className="relative w-full md:w-80">
              <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Search technology"
                className="pl-9"
              />
            </div>
          </div>

          <div className="grid gap-4">
            {filteredRecommendations.map((recommendation) => (
              <RecommendationCard
                key={`${recommendation.technology}-${recommendation.review_priority}`}
                recommendation={recommendation}
                uploadId={report.id}
                onImageClick={setExpandedImage}
              />
            ))}
          </div>
        </section>
      )}

      {debugPages && (
        <section className="mx-auto max-w-7xl px-5 pb-8">
          <div className="rounded-md border border-amber-200 bg-amber-50 p-4 mb-4">
            <h2 className="text-lg font-bold text-amber-800">Debug: Extracted Pages</h2>
            <p className="text-sm text-amber-700">Displaying raw text and images from PyMuPDF. Analysis is temporarily bypassed.</p>
          </div>
          <div className="grid gap-4">
            {debugPages.map((pageData: any, idx: number) => (
              <div key={idx} className="rounded-md border border-border bg-white p-4">
                <h3 className="font-semibold border-b pb-2 mb-3">Page {pageData.page}</h3>
                
                <div className="grid md:grid-cols-2 gap-4">
                  <div>
                    <h4 className="text-sm font-semibold text-muted-foreground mb-2">Extracted Text</h4>
                    <div className="bg-muted p-3 rounded text-sm whitespace-pre-wrap max-h-60 overflow-y-auto">
                      {pageData.text || <span className="text-muted-foreground italic">No text found</span>}
                    </div>
                  </div>
                  
                  <div>
                    <h4 className="text-sm font-semibold text-muted-foreground mb-2">
                      Extracted Images ({pageData.images?.length || 0})
                    </h4>
                    {pageData.images?.length > 0 ? (
                      <div className="flex flex-col gap-3">
                        {pageData.images.map((imgBase64: string, imgIdx: number) => (
                          <div key={imgIdx} className="border border-border p-2 rounded bg-slate-50 flex flex-col items-center">
                            <span className="text-xs text-muted-foreground mb-1">Image {imgIdx + 1}</span>
                            <img 
                              src={`data:image/png;base64,${imgBase64}`} 
                              alt={`Page ${pageData.page} Image ${imgIdx + 1}`} 
                              className="max-w-full max-h-48 object-contain"
                            />
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="bg-muted p-3 rounded text-sm text-muted-foreground italic">
                        No images found on this page
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Expanded Screenshot Modal Overlay */}
      {expandedImage && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/85 backdrop-blur-sm p-4 animate-in fade-in duration-200 cursor-zoom-out"
          onClick={() => setExpandedImage(null)}
        >
          <div 
            className="relative max-w-5xl max-h-[92vh] overflow-hidden rounded-lg bg-white p-2 shadow-2xl animate-in zoom-in-95 duration-200 cursor-default" 
            onClick={(e) => e.stopPropagation()}
          >
            <button
              onClick={() => setExpandedImage(null)}
              className="absolute right-4 top-4 rounded-full bg-slate-900/60 p-2 text-white hover:bg-slate-900 transition-colors focus:outline-none z-10 shadow"
              aria-label="Close image modal"
            >
              <X className="h-5 w-5" />
            </button>
            <img
              src={expandedImage}
              alt="Expanded Visual Reference"
              className="max-w-full max-h-[86vh] object-contain rounded-md"
            />
          </div>
        </div>
      )}
    </main>
  );
}

function SummaryTile({
  label,
  value,
  tone
}: {
  label: string;
  value: number;
  tone?: "high";
}) {
  return (
    <div className="rounded-md border border-border bg-white p-4">
      <p className="text-sm text-muted-foreground">{label}</p>
      <p className={cn("mt-2 text-3xl font-semibold", tone === "high" && "text-danger")}>
        {value}
      </p>
    </div>
  );
}

function RecommendationCard({
  recommendation,
  uploadId,
  onImageClick
}: {
  recommendation: Recommendation;
  uploadId?: number;
  onImageClick?: (url: string) => void;
}) {
  const tone =
    recommendation.review_priority === "High"
      ? "high"
      : recommendation.review_priority === "Medium"
        ? "medium"
        : "low";
  const sampleContexts = recommendation.sample_contexts ?? [];
  const priorityRationale =
    recommendation.priority_rationale ??
    `${recommendation.review_priority} priority is based on a ${recommendation.priority_score}/100 score from lifecycle, frequency, lab, and activity indicators.`;

  const [status, setStatus] = useState<"idle" | "submitting" | "success" | "error">("idle");
  const [decision, setDecision] = useState<string | null>(null);
  const [showInput, setShowInput] = useState<boolean>(false);
  const [rationale, setRationale] = useState<string>("");
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  async function submitDecision(chosenDecision: string, finalRationale?: string) {
    setStatus("submitting");
    setErrorMsg(null);
    try {
      const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
      const res = await fetch(`${API_BASE_URL}/api/feedback`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          upload_id: uploadId ?? null,
          technology: recommendation.technology,
          decision: chosenDecision,
          faculty_rationale: finalRationale || null,
          original_recommendation: recommendation,
        }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail ?? "Failed to save feedback.");
      }
      setDecision(chosenDecision);
      setStatus("success");
      setShowInput(false);
    } catch (err: any) {
      setStatus("error");
      setErrorMsg(err.message ?? "An error occurred.");
    }
  }

  return (
    <Card>
      <CardHeader className="flex flex-col gap-2">
        <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
          <CardTitle className="text-lg">{recommendation.technology}</CardTitle>
          <div className="flex flex-wrap shrink-0 gap-2">
            <Badge tone={tone}>{recommendation.review_priority} priority</Badge>
            <Badge tone="neutral">{Math.round(recommendation.confidence_score * 100)}% confidence</Badge>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="grid gap-5 lg:grid-cols-[minmax(0,1.5fr)_minmax(280px,0.8fr)]">
          <div className="space-y-4">
            <div>
              <h3 className="text-sm font-semibold text-foreground">Analysis Summary</h3>
              <div className="mt-2 rounded-md border border-border bg-slate-50/30 p-4 text-sm text-muted-foreground leading-relaxed shadow-sm">
                <p>{recommendation.why_suggested || priorityRationale}</p>
              </div>
            </div>
           
            <EvidenceAndContext recommendation={recommendation} onImageClick={onImageClick} />
            
            {/* Migration Assistant Panel */}
            {recommendation.migration_guide && (
              <div className="rounded-md border border-border bg-white p-4 shadow-sm">
                <h3 className="flex items-center gap-2 text-sm font-semibold text-primary">
                  <Lightbulb className="h-4 w-4" />
                  Migration Assistant (AI-Generated Guide)
                </h3>
                <div className="mt-2 text-xs text-muted-foreground leading-relaxed whitespace-pre-line bg-teal-50/20 p-3 rounded border border-teal-100">
                  {recommendation.migration_guide}
                </div>

                {/* Educational Rationale & Standard references */}
                {(recommendation.migration_rationale_why_deprecated || recommendation.migration_rationale_modern_benefits) && (
                  <div className="mt-3 grid gap-3 md:grid-cols-2 text-xs">
                    {recommendation.migration_rationale_why_deprecated && (
                      <div className="rounded-md border border-rose-100 bg-rose-50/30 p-3">
                        <span className="font-semibold text-rose-800 flex items-center gap-1.5 mb-1">
                          <span className="h-1.5 w-1.5 rounded-full bg-rose-500 animate-pulse" />
                          Why it is Outdated & Discouraged
                        </span>
                        <p className="text-muted-foreground leading-relaxed">
                          {recommendation.migration_rationale_why_deprecated}
                        </p>
                      </div>
                    )}
                    {recommendation.migration_rationale_modern_benefits && (
                      <div className="rounded-md border border-teal-100 bg-teal-50/30 p-3">
                        <span className="font-semibold text-teal-800 flex items-center gap-1.5 mb-1">
                          <span className="h-1.5 w-1.5 rounded-full bg-teal-500 animate-pulse" />
                          Why the Modern Approach is Superior
                        </span>
                        <p className="text-muted-foreground leading-relaxed">
                          {recommendation.migration_rationale_modern_benefits}
                        </p>
                      </div>
                    )}
                  </div>
                )}
                
                {/* Legacy vs Modern side-by-side code blocks */}
                <div className="mt-4 grid gap-3 md:grid-cols-2">
                  {recommendation.migration_legacy_code && (
                    <div className="rounded-md border border-rose-200 bg-rose-50/20 p-3">
                      <span className="text-[10px] font-bold text-rose-700 uppercase tracking-wider block mb-1">Legacy / Deprecated Context</span>
                      <pre className="text-xs font-mono bg-slate-900 text-slate-100 p-2.5 rounded overflow-x-auto whitespace-pre-wrap max-h-48">
                        {recommendation.migration_legacy_code}
                      </pre>
                    </div>
                  )}
                  {recommendation.migration_modern_code && (
                    <div className="rounded-md border border-teal-200 bg-teal-50/20 p-3">
                      <span className="text-[10px] font-bold text-teal-700 uppercase tracking-wider block mb-1">Modern / Recommended Replacement</span>
                      <pre className="text-xs font-mono bg-slate-900 text-slate-100 p-2.5 rounded overflow-x-auto whitespace-pre-wrap max-h-48">
                        {recommendation.migration_modern_code}
                      </pre>
                    </div>
                  )}
                </div>
              </div>
            )}




<div className="rounded-md border border-border bg-white p-4 shadow-sm">
              <h3 className="flex items-center gap-2 text-sm font-semibold text-primary">
                <ListChecks className="h-4 w-4" />
                Suggested faculty action
              </h3>
              {recommendation.suggested_faculty_action && (
                <p className="mt-2 text-sm leading-6 text-muted-foreground">
                  {recommendation.suggested_faculty_action}
                </p>
              )}
              <RecommendationList recommendations={recommendation.specific_recommendations} />
            </div>

            {/* Faculty Human-in-the-Loop Validation */}
            <div className="mt-6 border-t border-border pt-4">
              {status === "success" ? (
                <div className="rounded-md border border-teal-200 bg-teal-50/50 p-4 text-sm text-teal-800 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 animate-in fade-in duration-200">
                  <div className="flex items-start gap-2.5">
                    <CheckCircle2 className="h-5 w-5 text-teal-600 mt-0.5 flex-shrink-0" />
                    <div>
                      <span className="font-semibold block">Faculty feedback recorded!</span>
                      <p className="text-xs text-teal-700 mt-1">
                        Status: <strong className="uppercase">{decision}</strong>
                        {rationale && (
                          <>
                            <span className="mx-1.5">•</span>
                            <span className="italic">"{rationale}"</span>
                          </>
                        )}
                      </p>
                    </div>
                  </div>
                  <Button
                    size="sm"
                    variant="ghost"
                    className="text-teal-700 hover:bg-teal-100 hover:text-teal-900 self-end sm:self-center font-medium"
                    onClick={() => setStatus("idle")}
                  >
                    Modify Alignment
                  </Button>
                </div>
              ) : (
                <div className="rounded-md border border-border bg-slate-50/50 p-4 shadow-sm">
                  <div className="flex items-center gap-2">
                    <ShieldCheck className="h-5 w-5 text-primary" />
                    <h3 className="text-sm font-semibold text-foreground">
                      Faculty Human-in-the-Loop Validation
                    </h3>
                  </div>
                  <p className="mt-1 text-xs text-muted-foreground leading-relaxed">
                    Align the ModSync model. Your decision will be saved to SQLite and exported into standard JSONL datasets for subsequent fine-tuning.
                  </p>

                  {errorMsg && (
                    <div className="mt-2.5 rounded border border-rose-200 bg-rose-50 p-2.5 text-xs text-danger font-medium">
                      {errorMsg}
                    </div>
                  )}

                  {showInput ? (
                    <div className="mt-3.5 space-y-3">
                      <label className="block text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                        {decision === "Modify" ? "Specify modifications & rationale" : "Specify rejection rationale (optional)"}
                      </label>
                      <textarea
                        value={rationale}
                        onChange={(e) => setRationale(e.target.value)}
                        placeholder={decision === "Modify" ? "e.g., Use standard C++11 smart pointers instead of manual delete actions..." : "e.g., Faculty prefers teaching this legacy pattern for pedagogical reasons..."}
                        className="w-full min-h-20 text-xs p-2.5 rounded-md border border-border bg-white focus:outline-none focus:ring-1 focus:ring-primary focus:border-primary font-sans leading-relaxed text-foreground"
                      />
                      <div className="flex gap-2 justify-end">
                        <Button
                          size="sm"
                          variant="secondary"
                          disabled={status === "submitting"}
                          onClick={() => {
                            setShowInput(false);
                            setDecision(null);
                          }}
                        >
                          Cancel
                        </Button>
                        <Button
                          size="sm"
                          disabled={status === "submitting" || (decision === "Modify" && !rationale.trim())}
                          onClick={() => submitDecision(decision!, rationale)}
                        >
                          {status === "submitting" ? (
                            <Loader2 className="h-3 w-3 animate-spin mr-1.5" />
                          ) : null}
                          Submit Decision
                        </Button>
                      </div>
                    </div>
                  ) : (
                    <div className="mt-4 flex flex-wrap gap-2.5">
                      <Button
                        size="sm"
                        variant="outline"
                        className="border-emerald-200 text-emerald-700 hover:bg-emerald-50 hover:text-emerald-800"
                        disabled={status === "submitting"}
                        onClick={() => {
                          submitDecision("Approve", "");
                        }}
                      >
                        Approve
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        className="border-amber-200 text-amber-700 hover:bg-amber-50 hover:text-amber-800"
                        disabled={status === "submitting"}
                        onClick={() => {
                          setDecision("Modify");
                          setShowInput(true);
                        }}
                      >
                        Modify
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        className="border-rose-200 text-rose-700 hover:bg-rose-50 hover:text-rose-800"
                        disabled={status === "submitting"}
                        onClick={() => {
                          setDecision("Reject");
                          setShowInput(true);
                        }}
                      >
                        Reject
                      </Button>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>

          <div className="space-y-4">
            <ScoreBreakdown recommendation={recommendation} />
            <ResourceList title={`Current references for ${recommendation.technology}`} links={recommendation.current_technology_references} />
            <ResourceList title="New suggested references" links={recommendation.new_technology_references} />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function Field({ label, value }: { label: string; value?: string }) {
  if (!value) return null;

  return (
    <div>
      <h3 className="text-sm font-semibold">{label}</h3>
      <p className="mt-1 text-sm leading-6 text-muted-foreground">{value}</p>
    </div>
  );
}

function ScoreBreakdown({ recommendation }: { recommendation: Recommendation }) {
  const rows = [
    {
      label: "Lifecycle",
      value: recommendation.score_breakdown.technology_lifecycle_risk,
      max: 40,
      description: "Scores how outdated or deprecated a technology is (0-40 pts). High risk means it is End-of-Life and may break labs."
    },
    {
      label: "Frequency",
      value: recommendation.score_breakdown.frequency,
      max: 30,
      description: "Scores how many times it was mentioned (0-30 pts). High frequency implies the module is structurally dependent on it."
    },
    {
      label: "Labs",
      value: recommendation.score_breakdown.appears_in_labs,
      max: 20,
      description: "Adds 20 pts if the technology is used in hands-on labs, as deprecated tooling will immediately block students."
    },
    {
      label: "Activities",
      value: recommendation.score_breakdown.appears_in_learning_activities,
      max: 10,
      description: "Adds 10 pts if the technology is tied to learning outcomes, requiring rubric updates if changed."
    }
  ];

  return (
    <div>
      <h3 className="text-sm font-semibold">Priority score {recommendation.priority_score}/100</h3>
      <div className="mt-3 space-y-3">
        {rows.map(({ label, value, max, description }) => {
          const percentage = Math.min(100, Math.max(0, (value / max) * 100));
          return (
            <details key={label} className="group rounded-md border border-border bg-card text-sm cursor-pointer shadow-sm hover:border-primary/20 transition-colors">
              <summary className="p-3 list-none [&::-webkit-details-marker]:hidden [&::marker]:content-['']">
                <div className="flex items-center justify-between font-medium">
                  <span className="text-foreground">{label}</span>
                  <div className="flex items-center gap-1.5 text-muted-foreground">
                    <span className="text-xs">{value} / {max}</span>
                    <ChevronDown className="h-4 w-4 transition-transform duration-200 group-open:rotate-180" />
                  </div>
                </div>
                <div className="mt-2.5 flex items-center gap-3">
                  <div className="h-2 flex-1 rounded-full bg-slate-100 overflow-hidden">
                    <div 
                      className="h-full rounded-full bg-primary transition-all duration-350"
                      style={{ width: `${percentage}%` }}
                    />
                  </div>
                  <span className="text-xs font-semibold w-7 text-right text-primary">{Math.round(percentage)}%</span>
                </div>
              </summary>
              <div className="px-3 pb-3 pt-1 text-xs text-muted-foreground border-t border-border bg-slate-50/50 leading-relaxed">
                {description}
              </div>
            </details>
          );
        })}
      </div>
    </div>
  );
}

function RecommendationList({ recommendations }: { recommendations?: string[] }) {
  const items = recommendations ?? [];
  if (items.length === 0) return null;

  return (
    <ul className="mt-3 space-y-2 border-t border-border pt-3">
      {items.map((item) => (
        <li key={item} className="flex gap-2 text-sm leading-6 text-muted-foreground">
          <ClipboardCheck className="mt-1 h-4 w-4 flex-none text-primary" />
          <span>{item}</span>
        </li>
      ))}
    </ul>
  );
}

function EvidenceAndContext({
  recommendation,
  onImageClick
}: {
  recommendation: Recommendation;
  onImageClick?: (url: string) => void;
}) {
  const contexts = recommendation.sample_contexts ?? [];
  const reasons = recommendation.page_review_reasons ?? [];
  
  if (contexts.length === 0 && reasons.length === 0) return null;

  return (
    <div>
      <h3 className="flex items-center gap-2 text-sm font-semibold">
        <BookOpen className="h-4 w-4 text-primary" />
        Extracted Context & AI Analysis
      </h3>
      <div className="mt-3 space-y-4">
        {contexts.map((ctx) => {
          const matchingReason = reasons.find(r => r.page === ctx.page);
          
          return (
            <div key={ctx.page} className="rounded-md border border-border bg-white overflow-hidden shadow-sm">
              <div className="bg-muted px-3 py-2 border-b border-border flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Badge tone="neutral">Page {ctx.page}</Badge>
                  <span className="text-xs text-muted-foreground font-mono uppercase tracking-wider">Exact Quote</span>
                </div>
                {ctx.image_url && (
                  <span className="inline-flex items-center gap-1.5 text-[10px] font-semibold text-teal-600 bg-teal-50 px-2.5 py-0.5 rounded-full border border-teal-100 uppercase tracking-wide">
                    <span className="h-1.5 w-1.5 rounded-full bg-teal-500 animate-pulse" />
                    Visual Reference Available
                  </span>
                )}
              </div>
              <div className="p-4 flex flex-col md:flex-row gap-4 items-start">
                <div className="flex-1 space-y-3 w-full">
                  <blockquote className="border-l-4 border-primary/40 pl-4 italic text-sm text-muted-foreground bg-teal-50/50 py-2 rounded-r-sm break-words">
                    "{ctx.context_text}"
                  </blockquote>
                  {matchingReason?.reason && (
                    <p className="text-sm leading-6 text-foreground">
                      <span className="font-semibold text-primary">AI Context: </span>
                      {matchingReason.reason}
                    </p>
                  )}
                </div>
                {ctx.image_url && (
                  <div 
                    onClick={() => ctx.image_url && onImageClick?.(ctx.image_url)}
                    className="w-full md:w-48 shrink-0 flex flex-col items-center justify-center border border-border rounded-md bg-slate-50 p-2 shadow-sm hover:border-primary/45 cursor-pointer hover:scale-[1.02] transition-all group"
                  >
                    <img
                      src={ctx.image_url}
                      alt={`Page ${ctx.page} Visual Reference`}
                      className="max-w-full max-h-32 object-contain rounded border border-border bg-white shadow-sm group-hover:shadow-md transition-shadow"
                    />
                    <span className="text-[10px] text-muted-foreground mt-2 font-medium flex items-center gap-1 group-hover:text-primary transition-colors">
                      Zoom Screenshot
                    </span>
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}



function ResourceList({ title, links }: { title: string; links?: string[] }) {
  if (!links || links.length === 0) return null;
  return (
    <div>
      <h3 className="text-sm font-semibold">{title}</h3>
      <div className="mt-2 space-y-2">
        {links.map((link) => (
          <a
            key={link}
            href={link}
            target="_blank"
            rel="noreferrer"
            className="block break-words rounded-md border border-border bg-white px-3 py-2 text-sm text-primary hover:bg-teal-50"
          >
            {link}
          </a>
        ))}
      </div>
    </div>
  );
}
