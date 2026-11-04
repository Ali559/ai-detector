// eslint.config.js
import eslint from "@eslint/js";
import tseslint from "typescript-eslint";
import globals from "globals";

// 🚨 CRITICAL: Imports for Prettier integration
import prettierConfig from "eslint-config-prettier";
import prettierPlugin from "eslint-plugin-prettier";

export default [
  // 1. Files to Ignore
  {
    ignores: ["dist/", "node_modules/", "coverage/", "test/fixtures/"],
  },

  // 2. Base Configuration for All Files
  {
    files: ["**/*.{js,mjs,cjs,ts}"],
    languageOptions: {
      // Setup Node.js globals (e.g., process, module, __dirname)
      globals: {
        ...globals.node,
        // If you are using ES Modules (type: "module" in package.json)
        ...globals.nodeBuiltin,
      },
      sourceType: "module", // Use 'script' for CommonJS
    },
    rules: {
      // General Node/Fastify Code Quality Rules
      "no-console": ["warn", { allow: ["warn", "error"] }],
      "no-unused-vars": [
        "warn",
        { argsIgnorePattern: "^_", varsIgnorePattern: "^_" },
      ],

      // Best practice for server code to avoid unexpected behavior
      "require-await": "error",
    },
  },

  // 3. Recommended ESLint & TypeScript Rules
  // These apply a solid base for code quality
  eslint.configs.recommended,
  ...tseslint.configs.recommended,

  // 4. TypeScript-Specific Overrides
  {
    files: ["**/*.ts"],
    languageOptions: {
      parser: tseslint.parser,
      // You may need to configure parserOptions for type-aware rules
      // parserOptions: {
      //   project: ['./tsconfig.json'],
      //   tsconfigRootDir: import.meta.dirname,
      // },
    },
    rules: {
      "@typescript-eslint/no-unused-vars": [
        "warn",
        {
          argsIgnorePattern: "^(request|reply|next)$",
          varsIgnorePattern: "^_",
        },
      ],

      // Fastify's type inference is very good, so this is often unnecessary
      "@typescript-eslint/explicit-module-boundary-types": "off",
    },
  },

  // 5. Prettier Integration (MUST be the LAST config)
  // This turns off all style rules that conflict with Prettier
  prettierConfig,
  // This runs Prettier and reports differences as ESLint errors
  {
    plugins: {
      prettier: prettierPlugin,
    },
    rules: {
      "prettier/prettier": ["error", { endOfLine: "lf" }], // Use 'lf' for Linux/Mac/Git compatibility
    },
  },
];
