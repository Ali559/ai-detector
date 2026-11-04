import { betterAuth } from "better-auth";
import { NodePgDatabase } from "drizzle-orm/node-postgres";

declare module "fastify" {
  interface FastifyInstance {
    db: NodePgDatabase;
    auth: ReturnType<typeof betterAuth>;
    requireUser: (
      request: FastifyRequest,
      reply: FastifyReply,
    ) => Promise<unknown>;
  }

  interface FastifyRequest {
    user?: {
      id: string;
      email: string;
      name: string;
    };
  }
}
