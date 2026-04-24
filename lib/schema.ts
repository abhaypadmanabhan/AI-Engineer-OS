import { z } from "zod";

export const interviewQSchema = z.object({
  q: z.string(),
  answer: z.string(),
  difficulty: z.enum(["junior", "mid", "senior"]).default("mid"),
});

export const gateSchema = z.object({
  metric: z.string(),
  threshold: z.number(),
  eval_script: z.string().optional(),
  dataset: z.string().optional(),
});

export const frontmatterSchema = z.object({
  title: z.string(),
  layer: z.number().int().min(0).max(7),
  order: z.number().int().min(1),
  minutes: z.number().int().positive(),
  cost_usd: z.number().nonnegative().default(0),
  p95_latency_ms: z.number().int().nullable().optional(),
  stack: z.array(z.string()).default([]),
  gate: gateSchema.optional(),
  interview_qs: z.array(interviewQSchema).default([]),
});

export type Frontmatter = z.infer<typeof frontmatterSchema>;
export type Gate = z.infer<typeof gateSchema>;
export type InterviewQ = z.infer<typeof interviewQSchema>;
