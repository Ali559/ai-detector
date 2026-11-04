import { FastifyInstance } from "fastify";
import {
  AnalyzeVideoInput,
  AnalyzeVideoSchema,
} from "../schemas/detectionSchema";
import {
  AiServiceError,
  QuotaExceededError,
  callAiService,
  refundCheck,
  reserveCheck,
  saveDetection,
} from "../services/detection.service";

// A full capture is up to 64 JPEG frames as base64: tens of MB.
const MAX_BODY_BYTES = 64 * 1024 * 1024;

export const detectionRoutes = (fastify: FastifyInstance) => {
  fastify.post<{ Body: AnalyzeVideoInput }>(
    "/",
    {
      schema: { body: AnalyzeVideoSchema },
      bodyLimit: MAX_BODY_BYTES,
      preHandler: fastify.requireUser,
    },
    async (request, reply) => {
      const userId = request.user!.id;
      const input = request.body;
      if (!input.frames?.length && !input.bursts?.length) {
        return reply
          .code(400)
          .send({ error: "Send at least one frame or burst" });
      }

      let quota;
      try {
        quota = await reserveCheck(fastify.db, userId);
      } catch (error) {
        if (error instanceof QuotaExceededError) {
          return reply.code(429).send({ error: error.message });
        }
        throw error;
      }

      const started = performance.now();
      let result;
      try {
        result = await callAiService(input);
      } catch (error) {
        await refundCheck(fastify.db, userId);
        if (error instanceof AiServiceError) {
          request.log.warn({ err: error }, "AI service call failed");
          return reply.code(error.status).send({ error: error.message });
        }
        throw error;
      }

      const detectionId = await saveDetection(fastify.db, {
        userId,
        ipAddress: request.ip,
        userAgent: request.headers["user-agent"],
        input,
        result,
        processingTimeMs: Math.round(performance.now() - started),
      });

      return {
        id: detectionId,
        checks: { used: quota.used, limit: quota.limit },
        ...result,
      };
    },
  );
};
