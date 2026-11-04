import { FastifyInstance, FastifyPluginAsync } from "fastify";
import fp from "fastify-plugin";
import { betterAuth } from "better-auth";
import { drizzleAdapter } from "better-auth/adapters/drizzle";
import { accounts, sessions, users } from "../schemas/schema";
const authPlugin: FastifyPluginAsync = async (fastify: FastifyInstance) => {
  const auth = betterAuth({
    database: drizzleAdapter(fastify.db, {
      provider: "pg",
      schema: {
        user: users,
        session: sessions,
        account: accounts,
      },
    }),
    emailAndPassword: { enabled: true },
    emailVerification: {
      sendOnSignUp: true,
      autoSignInAfterVerification: true,
    },
    advanced: {
      database: {
        generateId: () => crypto.randomUUID(),
      },
    },
  });

  await fastify.decorate("auth", auth);
};

export default fp(authPlugin, { name: "auth-plugin" });
