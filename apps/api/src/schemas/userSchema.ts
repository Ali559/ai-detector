// schemas/userSchemas.ts
import { Type, Static } from "@sinclair/typebox";

// Define schemas with full autocomplete + inferred types
export const CreateUserSchema = Type.Object({
  email: Type.String({ format: "email" }),
  password: Type.String({ minLength: 8, maxLength: 48 }),
  name: Type.String({ minLength: 3 }),
});

export const UpdateUserSchema = Type.Partial(CreateUserSchema); // ✅ optional fields
export const LoginUserSchema = Type.Pick(CreateUserSchema, [
  "email",
  "password",
]);

// Inferred TS types ✨
export type CreateUserInput = Static<typeof CreateUserSchema>;
export type UpdateUserInput = Static<typeof UpdateUserSchema>;
export type LoginUserInput = Static<typeof LoginUserSchema>;
