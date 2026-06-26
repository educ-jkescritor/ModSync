export type ReviewPriority = "High" | "Medium" | "Low";

export type ExplainabilityItem = {
  factor: string;
  points: number;
  max_points: number;
  evidence: string;
  implication: string;
  review_question: string;
};

export type PageReviewReason = {
  page: number;
  context_text: string;
  reason: string;
  review_focus: string;
  implications: string[];
  image_url?: string;
};

export type Recommendation = {
  technology: string;
  review_priority: ReviewPriority;
  priority_score: number;
  confidence_score: number;
  industry_observation: string;
  why_suggested: string;
  priority_rationale?: string;
  suggested_faculty_action: string;
  specific_recommendations?: string[];
  page_review_reasons?: PageReviewReason[];
  explainability?: ExplainabilityItem[];
  official_documentation: string[];
  learning_resources: string[];
  faculty_validation_required: boolean;
  sample_contexts: {
    page: number;
    context: string[];
    context_text: string;
    appears_in_lab?: boolean;
    appears_in_learning_activity?: boolean;
  }[];
  score_breakdown: {
    technology_lifecycle_risk: number;
    frequency: number;
    appears_in_labs: number;
    appears_in_learning_activities: number;
  };
  pages: number[];
  frequency: number;
  ai_mode: string;
  migration_guide?: string;
  migration_legacy_code?: string;
  migration_modern_code?: string;
  migration_rationale_why_deprecated?: string;
  migration_rationale_modern_benefits?: string;
};

export type ReviewReport = {
  id?: number;
  filename?: string;
  file_size?: number;
  pages_analyzed: number;
  recommendations: Recommendation[];
  summary: {
    technology_count: number;
    review_candidate_count: number;
    high_priority_count: number;
    medium_priority_count: number;
    low_priority_count: number;
  };
};
