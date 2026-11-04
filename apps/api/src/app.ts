import { FastifyInstance } from "fastify";
import cors from "@fastify/cors";
import authPlugin from "./plugins/auth.plugin";
import databasePlugin from "./plugins/database.plugin";
import { routes } from "./routes/index";
import { config } from "dotenv";
config();
export async function app(fastify: FastifyInstance): Promise<FastifyInstance> {
  // Register CORS
  await fastify.register(cors, {
    origin: process.env.CORS_ORIGIN || "*",
  });

  // Register plugins
  await fastify.register(databasePlugin);
  await fastify.register(authPlugin);

  // Register routes
  await fastify.register(routes, { prefix: "/api" });

  return fastify;
}
