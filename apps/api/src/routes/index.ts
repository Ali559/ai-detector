import { FastifyInstance } from "fastify";
import { authRoutes } from "./auth.routes";
import { detectionRoutes } from "./detections.routes";
export const routes = async (fastify: FastifyInstance) => {
  await fastify.register(authRoutes, { prefix: "/auth" });
  await fastify.register(detectionRoutes, { prefix: "/detections" });
};
