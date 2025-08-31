// Types for the Canvas AI Agent

export interface Course {
  [courseName: string]: number;
}

export interface Module {
  id: number;
  name: string;
}

export interface ModuleItem {
  id: number;
  title: string;
  type: string;
  html_url?: string;
  content_id?: number;
}

export interface Resource {
  title: string;
  type: string;
  url: string;
  course: string;
  module: string;
  relevance_score: number;
}

export interface CourseAnalysis {
  course_name: string;
  confidence: number;
  reasoning: string;
}

export interface ModuleAnalysis {
  module_names: string[];
  relevance_explanations: string[];
}

export interface ResourceAnalysis {
  resource_indices: number[];
  relevance_scores: number[];
  reasoning: string;
}

export interface Env {
  CANVAS_API_KEY: string;
  GOOGLE_API_KEY: string;
}
