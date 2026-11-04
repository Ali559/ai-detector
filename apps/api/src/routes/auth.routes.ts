import { FastifyInstance, FastifyReply } from "fastify";
import { APIError } from "better-auth/api";
import { fromNodeHeaders } from "better-auth/node";
import {
  CreateUserSchema,
  LoginUserInput,
  LoginUserSchema,
} from "../schemas/userSchema";
import { Signin, Signup } from "../services/auth.service";
import { CreateUserDto } from "../types/user.types";

// better-auth throws APIError with the right HTTP status (e.g. 401 for a
// wrong password, 422 for an existing email); pass that through.
const sendAuthError = (
  fastify: FastifyInstance,
  reply: FastifyReply,
  error: unknown,
) => {
  if (error instanceof APIError) {
    return reply
      .code(error.statusCode)
      .send({ error: error.body?.message ?? error.message });
  }
  fastify.log.error(error);
  return reply.code(500).send({ error: "Authentication failed" });
};

export const authRoutes = (fastify: FastifyInstance) => {
  fastify.post<{ Body: LoginUserInput }>(
    "/signin/email",
    { schema: { body: LoginUserSchema } },
    async (request, reply) => {
      try {
        const { user, token } = await Signin(fastify.auth, request.body);
        reply.header("Authorization", token);
        return { user, token };
      } catch (error) {
        return sendAuthError(fastify, reply, error);
      }
    },
  );

  fastify.post<{ Body: CreateUserDto }>(
    "/signup/email",
    { schema: { body: CreateUserSchema } },
    async (request, reply) => {
      try {
        const { user, token } = await Signup(fastify.auth, request.body);
        return { user, token };
      } catch (error) {
        return sendAuthError(fastify, reply, error);
      }
    },
  );

  fastify.get("/me", { preHandler: fastify.requireUser }, (request, reply) =>
    reply.send({ user: request.user }),
  );

  fastify.post("/signout", async (request, reply) => {
    try {
      await fastify.auth.api.signOut({
        headers: fromNodeHeaders(request.headers),
      });
      return { ok: true };
    } catch (error) {
      return sendAuthError(fastify, reply, error);
    }
  });
};
