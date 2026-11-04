// drizzle.config.ts
import type { Config } from "drizzle-kit";
import * as dotenv from "dotenv";

dotenv.config();

export default {
  schema: "./src/schemas/schema.ts",
  out: "./src/db/migrations",
  dialect: "postgresql",
  dbCredentials: {
    url: process.env.DATABASE_URL!,
    password: "1212",
    user: "ali",
    database: "video_frame_capture",
  },
  verbose: true,
  strict: true,
} satisfies Config;
