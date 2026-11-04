import { FastifyInstance, FastifyPluginAsync } from "fastify";
import fp from "fastify-plugin";
import pg from "pg";
import { drizzle } from "drizzle-orm/node-postgres";
const { Pool } = pg;

const databasePlugin: FastifyPluginAsync = async (fastify: FastifyInstance) => {
  const pool = new Pool({
    connectionString: process.env.DATABASE_URL,
    max: 20,
    idleTimeoutMillis: 30000,
    connectionTimeoutMillis: 2000,
  });

  // Test connection
  try {
    await pool.query("SELECT NOW()");
    fastify.log.info("Database connected successfully");
  } catch (err) {
    fastify.log.error(err, "Database connection failed:");
    throw err;
  }
  const db = drizzle(pool);
  fastify.decorate("db", db);

  fastify.addHook("onClose", async () => {
    await pool.end();
  });
};

export default fp(databasePlugin, {
  name: "database-plugin",
});
