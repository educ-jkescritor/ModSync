"use client";

import { ChangeEvent, DragEvent, useEffect, useMemo, useRef, useState } from "react";
import {
  AlertCircle,
  BookOpen,
  CheckCircle2,
  ClipboardCheck,
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
import { API_BASE_URL, analyzePdf, submitFeedback } from "@/lib/api";
import { MultiAgentArchitecture } from "@/components/ui/architecture-diagram";
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
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);
  const [error, setError] = useState<string | null>(null);
  const [report, setReport] = useState<ReviewReport | null>(null);
  const [priorityFilter, setPriorityFilter] = useState<FilterValue>("All");
  const [query, setQuery] = useState("");
  const [activeLightboxImage, setActiveLightboxImage] = useState<string | null>(null);

  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") {
        setActiveLightboxImage(null);
      }
    }
    if (activeLightboxImage) {
      window.addEventListener("keydown", handleKeyDown);
    }
    return () => {
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [activeLightboxImage]);

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
    setStage("uploading");
    const extractTimer = window.setTimeout(() => setStage("extracting"), 450);
    const analysisTimer = window.setTimeout(() => setStage("analyzing"), 950);

    try {
      const result = await analyzePdf(file);
      setReport(result);
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

      <section className="mx-auto max-w-7xl px-5 pt-6">
        <MultiAgentArchitecture />
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
              <Button onClick={runAnalysis} disabled={!mounted || !file || stage === "uploading" || stage === "extracting" || stage === "analyzing"}>
                {stage === "uploading" || stage === "extracting" || stage === "analyzing" ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <FileSearch className="h-4 w-4" />
                )}
                Generate review report
              </Button>
              <Button variant="secondary" onClick={loadDemoReport}>
                <FileSearch className="h-4 w-4" />
                Demo report
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
            <SummaryTile label="Technologies" value={report.summary.technology_count} />
            <SummaryTile label="Review candidates" value={report.summary.review_candidate_count} />
            <SummaryTile label="High priority" value={report.summary.high_priority_count} tone="high" />
            <SummaryTile label="Pages analyzed" value={report.pages_analyzed} />
          </div>

          <div className="mb-5 flex flex-col gap-3 rounded-md border border-border bg-white p-4 md:flex-row md:items-center md:justify-between">
            <div className="flex flex-wrap gap-2">
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
                uploadId={report?.id}
                onViewImage={setActiveLightboxImage}
              />
            ))}
          </div>
        </section>
      )}

      {/* Lightbox Modal */}
      {activeLightboxImage && (
        <div 
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4 animate-in fade-in duration-200"
          onClick={() => setActiveLightboxImage(null)}
        >
          <button 
            onClick={() => setActiveLightboxImage(null)}
            className="absolute right-4 top-4 rounded-full bg-white/10 p-2 text-white hover:bg-white/20 transition focus:outline-none"
            aria-label="Close image viewer"
          >
            <X className="h-6 w-6" />
          </button>
          <div 
            className="relative max-h-[90vh] max-w-[90vw] overflow-hidden rounded-lg bg-white shadow-2xl border border-white/10 animate-in zoom-in-95 duration-200"
            onClick={(e) => e.stopPropagation()}
          >
            <img 
              src={activeLightboxImage.startsWith("http") || activeLightboxImage.startsWith("/demo-page") ? activeLightboxImage : `${API_BASE_URL}${activeLightboxImage}`} 
              alt="Visual page reference" 
              className="max-h-[85vh] max-w-full object-contain"
            />
            <div className="bg-slate-900 px-4 py-3 text-center text-white flex items-center justify-between">
              <span className="text-xs font-semibold text-slate-300">
                Visual Reference Screenshot
              </span>
              <span className="text-[11px] text-slate-400">
                Click outside or press Escape to close
              </span>
            </div>
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
  onViewImage
}: {
  recommendation: Recommendation;
  uploadId?: number;
  onViewImage?: (imageUrl: string) => void;
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

  const [selectedDecision, setSelectedDecision] = useState<"Approve" | "Reject" | "Modify" | null>(null);
  const [rationale, setRationale] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  async function handleFeedbackSubmit() {
    if (!selectedDecision) return;
    setSubmitting(true);
    try {
      await submitFeedback({
        upload_id: uploadId,
        technology: recommendation.technology,
        decision: selectedDecision,
        faculty_rationale: rationale,
        original_recommendation: JSON.stringify(recommendation)
      });
      setSubmitted(true);
    } catch (err) {
      alert(err instanceof Error ? err.message : "Failed to save feedback.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Card>
      <CardHeader className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
        <div>
          <CardTitle className="text-lg">{recommendation.technology}</CardTitle>
          <p className="mt-1 text-sm text-muted-foreground">
            Found on {recommendation.pages.length === 1 ? "page" : "pages"} {recommendation.pages.join(", ")} ({recommendation.frequency} total mentions)
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Badge tone={tone}>{recommendation.review_priority} priority</Badge>
          <Badge tone="neutral">{Math.round(recommendation.confidence_score * 100)}% confidence</Badge>
        </div>
      </CardHeader>
      <CardContent>
        <div className="grid gap-5 lg:grid-cols-[minmax(0,1.5fr)_minmax(280px,0.8fr)]">
          <div className="space-y-4">
            <Field label="Priority rationale" value={priorityRationale} />
            <Field label="Why it was suggested" value={recommendation.why_suggested} />
            <Field label="Industry observation" value={recommendation.industry_observation} />
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

            <EvidenceAndContext recommendation={recommendation} onViewImage={onViewImage} />

            {/* Human-in-the-Loop Feedback Form */}
            <div className="rounded-md border border-slate-200 bg-slate-50/60 p-4 shadow-inner mt-6">
              <h3 className="text-sm font-semibold text-slate-800 flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-primary" />
                Faculty Human-in-the-Loop Validation
              </h3>
              {submitted ? (
                <div className="mt-3 flex items-start gap-2 text-sm text-teal-800 bg-teal-50 border border-teal-200 p-3 rounded-md">
                  <CheckCircle2 className="h-5 w-5 text-teal-600 mt-0.5 flex-none" />
                  <div>
                    <strong>Validation Logged ({selectedDecision}):</strong>{" "}
                    <span className="italic">"{rationale || "Acknowledged/Approved"}"</span>
                    <p className="mt-1 text-xs text-muted-foreground">Feedback stored locally in SQLite feedback database for fine-tuning.</p>
                  </div>
                </div>
              ) : (
                <div className="mt-3 space-y-3">
                  <p className="text-xs text-muted-foreground">
                    Align the ModSync model. Your decision will be saved to SQLite and exported into standard JSONL datasets for subsequent fine-tuning.
                  </p>
                  <div className="flex flex-wrap gap-2">
                    <Button
                      size="sm"
                      variant={selectedDecision === "Approve" ? "default" : "secondary"}
                      onClick={() => {
                        setSelectedDecision("Approve");
                        if (!rationale) setRationale("Approved standard review recommendation.");
                      }}
                      className={cn(selectedDecision === "Approve" && "bg-teal-700 hover:bg-teal-800 text-white")}
                    >
                      Approve
                    </Button>
                    <Button
                      size="sm"
                      variant={selectedDecision === "Modify" ? "default" : "secondary"}
                      onClick={() => {
                        setSelectedDecision("Modify");
                        setRationale("");
                      }}
                      className={cn(selectedDecision === "Modify" && "bg-slate-700 hover:bg-slate-800 text-white")}
                    >
                      Modify
                    </Button>
                    <Button
                      size="sm"
                      variant={selectedDecision === "Reject" ? "default" : "secondary"}
                      onClick={() => {
                        setSelectedDecision("Reject");
                        setRationale("");
                      }}
                      className={cn(selectedDecision === "Reject" && "bg-rose-700 hover:bg-rose-800 text-white")}
                    >
                      Reject
                    </Button>
                  </div>

                  {selectedDecision && (
                    <div className="space-y-2 animate-in fade-in duration-200">
                      <label className="block text-xs font-semibold text-slate-700">
                        {selectedDecision === "Approve" ? "Faculty Rationale (optional):" : "Provide details for this reject/modify decision (required for fine-tuning):"}
                      </label>
                      <textarea
                        value={rationale}
                        onChange={(e) => setRationale(e.target.value)}
                        placeholder={selectedDecision === "Approve" ? "e.g., Looks good, will migrate the laboratory codebase." : "e.g., Rejecting because our local corporate partner still requires training on this legacy tech."}
                        className="w-full text-sm border border-slate-200 rounded-md p-2 h-16 focus:outline-none focus:ring-1 focus:ring-primary focus:border-primary bg-white"
                      />
                      <div className="flex gap-2">
                        <Button
                          size="sm"
                          onClick={handleFeedbackSubmit}
                          disabled={submitting || (selectedDecision !== "Approve" && !rationale.trim())}
                        >
                          {submitting ? "Saving..." : "Save Validation Decision"}
                        </Button>
                        <Button
                          size="sm"
                          variant="secondary"
                          onClick={() => {
                            setSelectedDecision(null);
                            setRationale("");
                          }}
                        >
                          Cancel
                        </Button>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>

          <div className="space-y-4">
            <ScoreBreakdown recommendation={recommendation} />
            <ResourceList title="Official documentation" links={recommendation.official_documentation} />
            <ResourceList title="Learning resources" links={recommendation.learning_resources} />
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
      description: "Scores how outdated or deprecated a technology is (0-40 pts). High risk means it is End-of-Life and may break labs."
    },
    {
      label: "Frequency",
      value: recommendation.score_breakdown.frequency,
      description: "Scores how many times it was mentioned (0-30 pts). High frequency implies the module is structurally dependent on it."
    },
    {
      label: "Labs",
      value: recommendation.score_breakdown.appears_in_labs,
      description: "Adds 20 pts if the technology is used in hands-on labs, as deprecated tooling will immediately block students."
    },
    {
      label: "Activities",
      value: recommendation.score_breakdown.appears_in_learning_activities,
      description: "Adds 10 pts if the technology is tied to learning outcomes, requiring rubric updates if changed."
    }
  ];

  return (
    <div>
      <h3 className="text-sm font-semibold">Priority score {recommendation.priority_score}/100</h3>
      <div className="mt-2 space-y-2">
        {rows.map(({ label, value, description }) => (
          <details key={label} className="group rounded-md bg-muted text-sm cursor-pointer [&_summary::-webkit-details-marker]:hidden">
            <summary className="flex items-center justify-between px-3 py-2">
              <span className="text-muted-foreground underline decoration-dashed underline-offset-4">{label}</span>
              <span className="font-semibold">{value}</span>
            </summary>
            <div className="px-3 pb-3 pt-1 text-muted-foreground">
              {description}
            </div>
          </details>
        ))}
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
  onViewImage
}: {
  recommendation: Recommendation;
  onViewImage?: (imageUrl: string) => void;
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
          const imageUrl = matchingReason?.image_url
            ? (matchingReason.image_url.startsWith("http") || matchingReason.image_url.startsWith("/demo-page")
                ? matchingReason.image_url
                : `${API_BASE_URL}${matchingReason.image_url}`)
            : null;
          
          return (
            <div key={ctx.page} className="rounded-md border border-border bg-white overflow-hidden shadow-sm">
              <div className="bg-muted px-3 py-2 border-b border-border flex items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  <Badge tone="neutral">Page {ctx.page}</Badge>
                  <span className="text-xs text-muted-foreground font-mono uppercase tracking-wider">Exact Quote</span>
                </div>
                {imageUrl && (
                  <span className="text-[11px] text-teal-700 font-semibold flex items-center gap-1.5 bg-teal-50 px-2 py-0.5 rounded-full border border-teal-100">
                    <span className="h-1.5 w-1.5 rounded-full bg-teal-500 animate-pulse" />
                    Visual Reference Available
                  </span>
                )}
              </div>
              <div className="p-4">
                <div className={cn("grid gap-4 items-start", imageUrl ? "md:grid-cols-[1fr_200px]" : "grid-cols-1")}>
                  <div className="space-y-3">
                    <blockquote className="border-l-4 border-primary/40 pl-4 italic text-sm text-muted-foreground bg-teal-50/50 py-2 rounded-r-sm">
                      "{ctx.context_text}"
                    </blockquote>
                    {matchingReason?.reason && (
                      <p className="text-sm leading-6 text-foreground">
                        <span className="font-semibold text-primary">AI Context: </span>
                        {matchingReason.reason}
                      </p>
                    )}
                  </div>
                  {imageUrl && (
                    <div 
                      onClick={() => onViewImage?.(matchingReason?.image_url || "")}
                      className="group relative flex aspect-[4/3] w-full md:w-[200px] items-center justify-center overflow-hidden rounded-md border border-slate-200 bg-slate-50 cursor-pointer shadow-sm transition hover:border-primary/50"
                    >
                      <img 
                        src={imageUrl} 
                        alt={`Page ${ctx.page} reference`} 
                        className="h-full w-full object-cover transition duration-300 group-hover:scale-105"
                      />
                      <div className="absolute inset-0 flex flex-col items-center justify-center bg-slate-900/40 opacity-0 transition-opacity duration-300 group-hover:opacity-100">
                        <Search className="h-5 w-5 text-white mb-1" />
                        <span className="text-[10px] font-bold text-white uppercase tracking-wider">View Full Page</span>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}



function ResourceList({ title, links }: { title: string; links: string[] }) {
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
