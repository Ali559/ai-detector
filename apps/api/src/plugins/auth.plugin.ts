import { FastifyInstance, FastifyPluginAsync, FastifyRequest } from "fastify";
import fp from "fastify-plugin";
import { betterAuth } from "better-auth";
import { drizzleAdapter } from "better-auth/adapters/drizzle";
import { bearer } from "better-auth/plugins";
import { fromNodeHeaders } from "better-auth/node";
import { accounts, sessions, users, verifications } from "../schemas/schema";

const authPlugin: FastifyPluginAsync = async (fastify: FastifyInstance) => {
  const auth = betterAuth({
    database: drizzleAdapter(fastify.db, {
      provider: "pg",
      schema: {
        user: users,
        session: sessions,
        account: accounts,
        verification: verifications,
      },
    }),
    user: { fields: { image: "avatarUrl" } },
    // Verification emails need a mail provider; until one is wired up, sign-up
    // doesn't send them.
    emailAndPassword: { enabled: true },
    // The extension sends `Authorization: Bearer <session token>`.
    plugins: [bearer()],
    advanced: {
      database: {
        generateId: () => crypto.randomUUID(),
      },
    },
  });

  await fastify.decorate("auth", auth);

  // preHandler for routes that need a signed-in user
  fastify.decorate("requireUser", async (request: FastifyRequest, reply) => {
    const session = await auth.api.getSession({
      headers: fromNodeHeaders(request.headers),
    });
    if (!session) {
      return reply.code(401).send({ error: "Not signed in" });
    }
    request.user = {
      id: session.user.id,
      email: session.user.email,
      name: session.user.name,
    };
  });
};

export default fp(authPlugin, {
  name: "auth-plugin",
  dependencies: ["database-plugin"],
});
