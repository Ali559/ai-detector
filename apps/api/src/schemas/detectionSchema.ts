// Mirrors apps/ai_service/app/schemas.py. The API passes the request through
// to the AI service unchanged, so field names stay snake_case.
import { Type, Static } from "@sinclair/typebox";

const Frame = Type.Object({
  data: Type.String({ minLength: 1 }),
  timestamp: Type.Optional(Type.Union([Type.Number(), Type.Null()])),
});

export const AnalyzeVideoSchema = Type.Object({
  video: Type.Optional(
    Type.Object({
      page_url: Type.Optional(Type.Union([Type.String(), Type.Null()])),
      width: Type.Optional(Type.Union([Type.Integer(), Type.Null()])),
      height: Type.Optional(Type.Union([Type.Integer(), Type.Null()])),
      duration: Type.Optional(Type.Union([Type.Number(), Type.Null()])),
      capture_method: Type.Optional(
        Type.Union([Type.Literal("canvas"), Type.Literal("tab_capture")]),
      ),
    }),
  ),
  frames: Type.Optional(Type.Array(Frame, { maxItems: 64 })),
  bursts: Type.Optional(
    Type.Array(
      Type.Object({
        fps: Type.Number({ exclusiveMinimum: 0 }),
        frames: Type.Array(Frame, { minItems: 2, maxItems: 32 }),
      }),
      { maxItems: 4 },
    ),
  ),
});

export type AnalyzeVideoInput = Static<typeof AnalyzeVideoSchema>;

export interface HeadResult {
  name: string;
  model: string;
  available: boolean;
  score: number | null;
  peak: number | null;
  frames_scored: number;
  calibrated: boolean;
  reason: string | null;
  per_frame: { index: number; timestamp: number | null; score: number }[];
  details: Record<string, unknown>;
}

export interface AnalyzeVideoResult {
  verdict: "likely_ai" | "inconclusive" | "no_evidence";
  probability: number | null;
  calibrated: boolean;
  reasons: string[];
  heads: HeadResult[];
  quality: {
    total_frames: number;
    usable_frames: number;
    usable_bursts: number;
    poor: boolean;
    flags: string[];
  };
  frame_hashes: string[];
  processing_time_ms: number;
}
