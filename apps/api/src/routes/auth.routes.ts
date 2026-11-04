import { FastifyInstance } from "fastify";
import {
  CreateUserSchema,
  LoginUserInput,
  LoginUserSchema,
} from "../schemas/userSchema";
import { Signin, Signup } from "../services/auth.service";
import { CreateUserDto } from "../types/user.types";

export const authRoutes = (fastify: FastifyInstance) => {
  fastify.post<{ Body: LoginUserInput }>(
    "/signin/email",
    { schema: LoginUserSchema },
    async (request, reply) => {
      try {
        const { user, token } = await Signin(fastify.auth, request.body);
        reply.header("Authorization", token);
        return { user, token };
      } catch (error) {
        fastify.log.error(error);
        return error;
      }
    },
  );
  fastify.post<{ Body: CreateUserDto }>(
    "/signup/email",
    {
      schema: {
        body: CreateUserSchema,
        response: {},
      },
    },
    async (request) => {
      try {
        const { user } = await Signup(fastify.auth, request.body);
        return user;
      } catch (error) {
        fastify.log.error(error);
        return error;
      }
    },
  );
};
