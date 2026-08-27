/**
 * @benchpress/distillation
 * Core distillation and Vertex AI Gemini fine-tuning schemas.
 */

export interface SftFunctionCall {
  name: string;
  args: Record<string, unknown>;
}

export interface SftMessage {
  role: "system" | "user" | "model" | "tool";
  content?: string;
  tool_calls?: SftFunctionCall[];
}

export interface VertexSftDatasetRecord {
  messages: SftMessage[];
}

export interface DpoPreferencePairRecord {
  prompt: string;
  chosen: SftMessage[];
  rejected: SftMessage[];
  task_id: string;
  cost_differential_usd: number;
}

export class DistillationPipelineHelper {
  public static calculateDistillationEfficiency(
    baselineModelCpr: number,
    distilledModelCpr: number
  ): number {
    if (baselineModelCpr <= 0) return 0;
    return Math.round(((baselineModelCpr - distilledModelCpr) / baselineModelCpr) * 1000) / 10;
  }
}
