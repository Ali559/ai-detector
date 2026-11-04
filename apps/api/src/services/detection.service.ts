import { and, eq, lt, or, sql } from "drizzle-orm";
import { NodePgDatabase } from "drizzle-orm/node-postgres";
import {
  detectionResults,
  frameAnalyses,
  usageLogs,
  users,
} from "../schemas/schema";
import {
  AnalyzeVideoInput,
  AnalyzeVideoResult,
  HeadResult,
} from "../schemas/detectionSchema";

const AI_SERVICE_URL = process.env.AI_SERVICE_URL || "http://localhost:8000";
const AI_SERVICE_TIMEOUT_MS =
  Number(process.env.AI_SERVICE_TIMEOUT_MS) || 120_000;
// Shared secret, matching the AI service's SERVICE_TOKEN when it's exposed publicly.
const AI_SERVICE_TOKEN = process.env.AI_SERVICE_TOKEN;

export class QuotaExceededError extends Error {}
export class AiServiceError extends Error {
  constructor(
    message: string,
    public readonly status: number,
  ) {
    super(message);
  }
}

/**
 * Atomically use one of today's checks. The daily counter resets the first
 * time it's touched on a new UTC day. Throws QuotaExceededError at the limit.
 */
export async function reserveCheck(db: NodePgDatabase, userId: string) {
  const startOfDay = sql`date_trunc('day', now() at time zone 'utc')`;
  const startOfMonth = sql`date_trunc('month', now() at time zone 'utc')`;
  const updated = await db
    .update(users)
    .set({
      dailyChecksUsed: sql`case when ${users.lastResetAt} < ${startOfDay} then 1 else ${users.dailyChecksUsed} + 1 end`,
      monthlyChecksUsed: sql`case when ${users.lastResetAt} < ${startOfMonth} then 1 else ${users.monthlyChecksUsed} + 1 end`,
      lastResetAt: sql`now() at time zone 'utc'`,
    })
    .where(
      and(
        eq(users.id, userId),
        or(
          lt(users.lastResetAt, startOfDay),
          lt(users.dailyChecksUsed, users.dailyChecksLimit),
        ),
      ),
    )
    .returning({
      used: users.dailyChecksUsed,
      limit: users.dailyChecksLimit,
    });
  if (updated.length === 0)
    throw new QuotaExceededError("Daily check limit reached");
  return updated[0];
}

/** Give a reserved check back, e.g. when the AI service failed. */
export async function refundCheck(db: NodePgDatabase, userId: string) {
  await db
    .update(users)
    .set({
      dailyChecksUsed: sql`greatest(${users.dailyChecksUsed} - 1, 0)`,
      monthlyChecksUsed: sql`greatest(${users.monthlyChecksUsed} - 1, 0)`,
    })
    .where(eq(users.id, userId));
}

export async function callAiService(
  input: AnalyzeVideoInput,
): Promise<AnalyzeVideoResult> {
  let response: Response;
  try {
    response = await fetch(`${AI_SERVICE_URL}/analyze/video`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(AI_SERVICE_TOKEN && {
          Authorization: `Bearer ${AI_SERVICE_TOKEN}`,
        }),
      },
      body: JSON.stringify(input),
      signal: AbortSignal.timeout(AI_SERVICE_TIMEOUT_MS),
    });
  } catch (error) {
    throw new AiServiceError(
      `AI service unreachable: ${(error as Error).message}`,
      503,
    );
  }
  if (!response.ok) {
    const body = (await response.json().catch(() => ({}))) as {
      detail?: unknown;
    };
    const detail =
      typeof body.detail === "string"
        ? body.detail
        : JSON.stringify(body.detail);
    // 422 means the frames themselves were bad; anything else is our problem.
    throw new AiServiceError(
      `AI service error: ${detail ?? response.statusText}`,
      response.status === 422 ? 422 : 502,
    );
  }
  return (await response.json()) as AnalyzeVideoResult;
}

function confidenceLevel(probability: number | null) {
  if (probability === null) return "low" as const;
  const distance = Math.abs(probability - 0.5) * 2;
  if (distance < 0.4) return "low" as const;
  if (distance < 0.7) return "medium" as const;
  if (distance < 0.9) return "high" as const;
  return "very_high" as const;
}

function platformOf(pageUrl: string | null | undefined) {
  if (!pageUrl) return null;
  try {
    return new URL(pageUrl).hostname.replace(/^www\./, "").slice(0, 50);
  } catch {
    return null;
  }
}

// Per-frame scores go to frame_analyses, not the summary.
const headSummary = (head: HeadResult) => ({ ...head, per_frame: undefined });

/**
 * Persist a finished analysis. Frames themselves are never stored, only their
 * hashes and scores.
 */
export function saveDetection(
  db: NodePgDatabase,
  params: {
    userId: string;
    ipAddress: string;
    userAgent?: string;
    input: AnalyzeVideoInput;
    result: AnalyzeVideoResult;
    processingTimeMs: number;
  },
) {
  const { userId, input, result, processingTimeMs } = params;
  const probability = result.probability;

  return db.transaction(async (tx) => {
    const [detection] = await tx
      .insert(detectionResults)
      .values({
        userId,
        pageUrl: input.video?.page_url ?? null,
        videoPlatform: platformOf(input.video?.page_url),
        overallConfidence: probability ?? 0.5,
        authenticityScore: probability === null ? 0.5 : 1 - probability,
        status: "completed",
        framesAnalyzed: result.quality.usable_frames,
        detectionMethodsUsed: result.heads.map((h) => ({
          name: h.name,
          model: h.model,
          available: h.available,
          calibrated: h.calibrated,
        })),
        detailedResults: {
          verdict: result.verdict,
          probability,
          calibrated: result.calibrated,
          reasons: result.reasons,
          quality: result.quality,
          heads: result.heads.map(headSummary),
        },
        isLikelyAi: result.verdict === "likely_ai",
        confidenceLevel: confidenceLevel(probability),
        warningFlags: result.quality.flags,
        processingTimeMs,
      })
      .returning({ id: detectionResults.id });

    // One row per sparse frame, with each head's score for that frame.
    const frames = input.frames ?? [];
    if (frames.length > 0) {
      const perFrameMs = Math.round(result.processing_time_ms / frames.length);
      await tx.insert(frameAnalyses).values(
        frames.map((frame, index) => {
          const providerResults: Record<string, number> = {};
          for (const head of result.heads) {
            const score = head.per_frame.find((f) => f.index === index)?.score;
            if (score !== undefined) providerResults[head.name] = score;
          }
          const scores = Object.values(providerResults);
          const aiProbability = scores.length
            ? scores.reduce((a, b) => a + b, 0) / scores.length
            : (probability ?? 0.5);
          return {
            detectionResultId: detection.id,
            frameNumber: index + 1,
            frameHash: result.frame_hashes[index],
            frameTimestampMs: Math.round((frame.timestamp ?? 0) * 1000),
            authenticityScore: 1 - aiProbability,
            aiProbability,
            providerResults,
            analysisMethod: { heads: Object.keys(providerResults) },
            processingTimeMs: perFrameMs,
          };
        }),
      );
    }

    await tx.insert(usageLogs).values({
      userId,
      action: "detection",
      resourceType: "detection_result",
      resourceId: detection.id,
      ipAddress: params.ipAddress.slice(0, 45),
      userAgent: params.userAgent,
      endpoint: "/api/detections",
    });

    return detection.id;
  });
}
