import { betterAuth } from "better-auth";
import { NodePgDatabase } from "drizzle-orm/node-postgres";

declare module "fastify" {
  interface FastifyInstance {
    db: NodePgDatabase;
    auth: ReturnType<typeof betterAuth>;
  }

  interface FastifyRequest {
    user?: {
      id: string;
      email: string;
      role: string;
    };
  }
}
