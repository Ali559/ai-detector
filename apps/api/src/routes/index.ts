import { FastifyInstance } from "fastify";
import { authRoutes } from "./auth.routes";
export const routes = async (fastify: FastifyInstance) => {
  await fastify.register(authRoutes, { prefix: "/auth" });
};
