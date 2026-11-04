import Fastify from "fastify";
import { app } from "./app";
import { TypeBoxTypeProvider } from "@fastify/type-provider-typebox";

const fastify = Fastify({
  logger: {
    transport: {
      target: "pino-pretty",
    },
    level: process.env.LOG_LEVEL || "info",
  },
}).withTypeProvider<TypeBoxTypeProvider>();

const start = async (): Promise<void> => {
  try {
    await app(fastify);
    await fastify.listen({
      port: Number(process.env.PORT) || 3000,
      host: "0.0.0.0",
    });
  } catch (err) {
    fastify.log.error(err);
    process.exit(1);
  }
};

start();
