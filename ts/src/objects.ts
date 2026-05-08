/**
 * Content-addressed objects for prompt-git.
 */

export interface Blob {
  hash: string;
  content: string;
  format: "plaintext" | "jinja2" | "json_messages" | "yaml_turns";
  model_hint: string | null;
}

export interface Tree {
  hash: string;
  entries: Record<string, string>; // path → blob_hash
}

export interface Commit {
  hash: string;
  parent: string | null;
  tree: string;
  message: string;
  author: string;
  committed_at: string;
  eval_scores: Record<string, number>;
  metadata: Record<string, unknown>;
}

export interface Tag {
  hash: string;
  name: string;
  target: string;
  message: string | null;
  created_at: string;
}

export interface SemanticDiff {
  from_hash: string;
  to_hash: string;
  summary: string;
  additions: string[];
  removals: string[];
  tone_shift: string | null;
  structural_changes: string[];
  model_used: string;
  generated_at: string;
}

export interface EvalScore {
  commit_hash: string;
  metric: string;
  value: number;
  recorded_at: string;
  notes: string | null;
}
