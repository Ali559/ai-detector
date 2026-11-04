import { LoginUserInput } from "../schemas/userSchema";
import { CreateUserDto } from "../types/user.types";
import { betterAuth, User } from "better-auth";

export const Signup = (
  auth: ReturnType<typeof betterAuth>,
  user: CreateUserDto,
): Promise<{ user: User }> => {
  return auth.api.signUpEmail({
    body: {
      email: user.email,
      name: user.name,
      password: user.password,
    },
  });
};

export const Signin = (
  auth: ReturnType<typeof betterAuth>,
  user: LoginUserInput,
): Promise<{ user: User; token: string }> => {
  return auth.api.signInEmail({
    body: {
      email: user.email,
      password: user.password,
    },
  });
};
