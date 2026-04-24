export const PRICING = {
  "claude-sonnet-4-6": { input_per_mtok: 3, output_per_mtok: 15 },
  "claude-haiku-4-5":  { input_per_mtok: 1, output_per_mtok: 5  },
  "gpt-5":             { input_per_mtok: 10, output_per_mtok: 40 },
} as const;

export type ModelId = keyof typeof PRICING;

export function computeCost(
  model: ModelId,
  inputTok: number,
  outputTok: number,
): number {
  const p = PRICING[model];
  return (inputTok / 1_000_000) * p.input_per_mtok + (outputTok / 1_000_000) * p.output_per_mtok;
}
