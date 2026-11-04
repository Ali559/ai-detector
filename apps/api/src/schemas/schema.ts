// schema.ts
import {
  pgTable,
  uuid,
  varchar,
  boolean,
  timestamp,
  integer,
  real,
  jsonb,
  text,
  pgEnum,
  index,
  uniqueIndex,
} from "drizzle-orm/pg-core";
import { relations } from "drizzle-orm";

// Enums
export const userTierEnum = pgEnum("user_tier", [
  "free",
  "premium",
  "enterprise",
]);
export const subscriptionStatusEnum = pgEnum("subscription_status", [
  "active",
  "canceled",
  "past_due",
  "trialing",
]);
export const detectionStatusEnum = pgEnum("detection_status", [
  "processing",
  "completed",
  "failed",
]);
export const confidenceLevelEnum = pgEnum("confidence_level", [
  "low",
  "medium",
  "high",
  "very_high",
]);
export const providerEnum = pgEnum("provider", [
  "email",
  "google",
  "github",
  "microsoft",
]);
export const actionEnum = pgEnum("action", [
  "detection",
  "api_call",
  "export",
  "share",
]);
export const reportTypeEnum = pgEnum("report_type", [
  "false_positive",
  "false_negative",
  "bug",
  "other",
]);
export const reportStatusEnum = pgEnum("report_status", [
  "pending",
  "reviewed",
  "resolved",
  "dismissed",
]);

// Users Table
export const users = pgTable(
  "users",
  {
    id: uuid("id").primaryKey().defaultRandom(),
    email: varchar("email", { length: 255 }).notNull().unique(),
    emailVerified: boolean("email_verified").default(false).notNull(),
    name: varchar("name", { length: 255 }),
    avatarUrl: text("avatar_url"),

    // Subscription
    tier: userTierEnum("tier").default("free").notNull(),
    subscriptionStatus: subscriptionStatusEnum("subscription_status"),
    subscriptionId: varchar("subscription_id", { length: 255 }),
    subscriptionExpiresAt: timestamp("subscription_expires_at"),

    // Usage tracking
    dailyChecksUsed: integer("daily_checks_used").default(0).notNull(),
    dailyChecksLimit: integer("daily_checks_limit").default(20).notNull(),
    monthlyChecksUsed: integer("monthly_checks_used").default(0).notNull(),
    lastResetAt: timestamp("last_reset_at").defaultNow().notNull(),

    // Metadata
    preferences: jsonb("preferences"),
    timezone: varchar("timezone", { length: 50 }),

    createdAt: timestamp("created_at").defaultNow().notNull(),
    updatedAt: timestamp("updated_at").defaultNow().notNull(),
    lastLoginAt: timestamp("last_login_at"),
  },
  (table) => [
    uniqueIndex("users_email_idx").on(table.email),
    index("users_tier_idx").on(table.tier),
  ],
);

// Accounts Table (for SSO)
export const accounts = pgTable(
  "accounts",
  {
    id: uuid("id").primaryKey().defaultRandom(),
    accountId: text("accountId").notNull(),
    providerId: text("providerId").notNull(),
    idToken: text("idToken"),
    password: text("password"),
    userId: uuid("user_id")
      .notNull()
      .references(() => users.id, { onDelete: "cascade" }),
    provider: providerEnum("provider"),
    providerAccountId: varchar("provider_account_id", { length: 255 }),
    accessToken: text("access_token"),
    refreshToken: text("refresh_token"),
    expiresAt: timestamp("expires_at"),

    createdAt: timestamp("created_at").defaultNow().notNull(),
    updatedAt: timestamp("updated_at").defaultNow().notNull(),
  },
  (table) => [
    index("accounts_user_id_idx").on(table.userId),
    uniqueIndex("accounts_provider_account_idx").on(
      table.provider,
      table.providerAccountId,
    ),
  ],
);

// Sessions Table
export const sessions = pgTable(
  "sessions",
  {
    id: uuid("id").primaryKey().defaultRandom(),
    userId: uuid("user_id")
      .notNull()
      .references(() => users.id, { onDelete: "cascade" }),
    token: varchar("token", { length: 255 }).notNull().unique(),
    expiresAt: timestamp("expires_at").notNull(),
    ipAddress: varchar("ip_address", { length: 45 }),
    userAgent: text("user_agent"),

    createdAt: timestamp("created_at").defaultNow().notNull(),
    updatedAt: timestamp("updated_at").defaultNow().notNull(),
  },
  (table) => [
    uniqueIndex("sessions_token_idx").on(table.token),
    index("sessions_user_id_idx").on(table.userId),
    index("sessions_expires_at_idx").on(table.expiresAt),
  ],
);

// Detection Results Table
export const detectionResults = pgTable(
  "detection_results",
  {
    id: uuid("id").primaryKey().defaultRandom(),
    userId: uuid("user_id")
      .notNull()
      .references(() => users.id, { onDelete: "cascade" }),

    // Video/Source info
    videoUrl: text("video_url"),
    videoTitle: text("video_title"),
    videoPlatform: varchar("video_platform", { length: 50 }),
    pageUrl: text("page_url"),

    // Detection data
    overallConfidence: real("overall_confidence").notNull(),
    authenticityScore: real("authenticity_score").notNull(),
    status: detectionStatusEnum("status").default("processing").notNull(),

    // Results breakdown
    framesAnalyzed: integer("frames_analyzed").notNull(),
    detectionMethodsUsed: jsonb("detection_methods_used").notNull(),
    detailedResults: jsonb("detailed_results").notNull(),

    // Flags & warnings
    isLikelyAi: boolean("is_likely_ai").notNull(),
    confidenceLevel: confidenceLevelEnum("confidence_level").notNull(),
    warningFlags: jsonb("warning_flags"),

    // Processing metadata
    processingTimeMs: integer("processing_time_ms").notNull(),
    apiCosts: real("api_costs"),

    // User actions
    userFeedback: varchar("user_feedback", { length: 50 }),
    userNotes: text("user_notes"),
    isBookmarked: boolean("is_bookmarked").default(false).notNull(),
    isArchived: boolean("is_archived").default(false).notNull(),

    createdAt: timestamp("created_at").defaultNow().notNull(),
    updatedAt: timestamp("updated_at").defaultNow().notNull(),
  },
  (table) => [
    index("detection_results_user_created_idx").on(
      table.userId,
      table.createdAt,
    ),
    index("detection_results_status_idx").on(table.status),
    index("detection_results_bookmarked_idx").on(
      table.userId,
      table.isBookmarked,
    ),
  ],
);

// Frame Analysis Table
export const frameAnalyses = pgTable(
  "frame_analyses",
  {
    id: uuid("id").primaryKey().defaultRandom(),
    detectionResultId: uuid("detection_result_id")
      .notNull()
      .references(() => detectionResults.id, { onDelete: "cascade" }),

    frameNumber: integer("frame_number").notNull(),
    frameHash: varchar("frame_hash", { length: 64 }).notNull(),
    frameTimestampMs: integer("frame_timestamp_ms").notNull(),

    // Detection results
    authenticityScore: real("authenticity_score").notNull(),
    aiProbability: real("ai_probability").notNull(),

    // Per-provider results
    providerResults: jsonb("provider_results").notNull(),

    // Visual analysis
    detectedArtifacts: jsonb("detected_artifacts"),
    reverseImageMatches: jsonb("reverse_image_matches"),

    // Metadata
    analysisMethod: jsonb("analysis_method").notNull(),
    processingTimeMs: integer("processing_time_ms").notNull(),

    createdAt: timestamp("created_at").defaultNow().notNull(),
  },
  (table) => [
    index("frame_analyses_detection_result_idx").on(table.detectionResultId),
    index("frame_analyses_frame_hash_idx").on(table.frameHash),
  ],
);

// Usage Logs Table
export const usageLogs = pgTable(
  "usage_logs",
  {
    id: uuid("id").primaryKey().defaultRandom(),
    userId: uuid("user_id")
      .notNull()
      .references(() => users.id, { onDelete: "cascade" }),

    action: actionEnum("action").notNull(),
    resourceType: varchar("resource_type", { length: 50 }),
    resourceId: uuid("resource_id"),

    // Request metadata
    ipAddress: varchar("ip_address", { length: 45 }).notNull(),
    userAgent: text("user_agent"),
    endpoint: varchar("endpoint", { length: 255 }),

    // Costs & limits
    creditsUsed: integer("credits_used").default(1).notNull(),
    apiCost: real("api_cost"),

    createdAt: timestamp("created_at").defaultNow().notNull(),
  },
  (table) => [
    index("usage_logs_user_created_idx").on(table.userId, table.createdAt),
    index("usage_logs_action_idx").on(table.action),
  ],
);

// API Keys Table
export const apiKeys = pgTable(
  "api_keys",
  {
    id: uuid("id").primaryKey().defaultRandom(),
    userId: uuid("user_id")
      .notNull()
      .references(() => users.id, { onDelete: "cascade" }),

    keyHash: varchar("key_hash", { length: 255 }).notNull().unique(),
    keyPrefix: varchar("key_prefix", { length: 20 }).notNull(),
    name: varchar("name", { length: 100 }).notNull(),

    // Permissions
    scopes: jsonb("scopes").notNull(),
    rateLimit: integer("rate_limit").notNull(),

    // Usage tracking
    lastUsedAt: timestamp("last_used_at"),
    requestsCount: integer("requests_count").default(0).notNull(),

    // Status
    isActive: boolean("is_active").default(true).notNull(),
    expiresAt: timestamp("expires_at"),

    createdAt: timestamp("created_at").defaultNow().notNull(),
    updatedAt: timestamp("updated_at").defaultNow().notNull(),
  },
  (table) => [
    uniqueIndex("api_keys_key_hash_idx").on(table.keyHash),
    index("api_keys_user_id_idx").on(table.userId),
  ],
);

// Detection Cache Table
export const detectionCache = pgTable(
  "detection_cache",
  {
    id: uuid("id").primaryKey().defaultRandom(),

    frameHash: varchar("frame_hash", { length: 64 }).notNull().unique(),
    videoHash: varchar("video_hash", { length: 64 }),

    // Cached results
    authenticityScore: real("authenticity_score").notNull(),
    aiProbability: real("ai_probability").notNull(),
    detectionMethods: jsonb("detection_methods").notNull(),
    detailedResults: jsonb("detailed_results").notNull(),

    // Metadata
    timesAccessed: integer("times_accessed").default(1).notNull(),
    lastAccessedAt: timestamp("last_accessed_at").defaultNow().notNull(),

    // Expiration
    expiresAt: timestamp("expires_at").notNull(),
    createdAt: timestamp("created_at").defaultNow().notNull(),
  },
  (table) => [
    uniqueIndex("detection_cache_frame_hash_idx").on(table.frameHash),
    index("detection_cache_video_hash_idx").on(table.videoHash),
    index("detection_cache_expires_at_idx").on(table.expiresAt),
  ],
);

// Webhooks Table
export const webhooks = pgTable(
  "webhooks",
  {
    id: uuid("id").primaryKey().defaultRandom(),
    userId: uuid("user_id")
      .notNull()
      .references(() => users.id, { onDelete: "cascade" }),

    url: text("url").notNull(),
    events: jsonb("events").notNull(),
    secret: varchar("secret", { length: 255 }).notNull(),

    isActive: boolean("is_active").default(true).notNull(),
    lastTriggeredAt: timestamp("last_triggered_at"),
    failureCount: integer("failure_count").default(0).notNull(),

    createdAt: timestamp("created_at").defaultNow().notNull(),
    updatedAt: timestamp("updated_at").defaultNow().notNull(),
  },
  (table) => [index("webhooks_user_id_idx").on(table.userId)],
);

// Reports Table
export const reports = pgTable(
  "reports",
  {
    id: uuid("id").primaryKey().defaultRandom(),
    userId: uuid("user_id")
      .notNull()
      .references(() => users.id, { onDelete: "cascade" }),
    detectionResultId: uuid("detection_result_id").references(
      () => detectionResults.id,
      { onDelete: "set null" },
    ),

    reportType: reportTypeEnum("report_type").notNull(),
    description: text("description").notNull(),

    status: reportStatusEnum("status").default("pending").notNull(),
    adminNotes: text("admin_notes"),

    createdAt: timestamp("created_at").defaultNow().notNull(),
    updatedAt: timestamp("updated_at").defaultNow().notNull(),
  },
  (table) => [
    index("reports_user_id_idx").on(table.userId),
    index("reports_status_idx").on(table.status),
  ],
);

// Payment-related enums
export const paymentProviderEnum = pgEnum("payment_provider", [
  "stripe",
  "paypal",
  "paddle",
]);
export const subscriptionIntervalEnum = pgEnum("subscription_interval", [
  "month",
  "year",
]);
export const invoiceStatusEnum = pgEnum("invoice_status", [
  "draft",
  "open",
  "paid",
  "void",
  "uncollectible",
]);
export const paymentStatusEnum = pgEnum("payment_status", [
  "succeeded",
  "pending",
  "failed",
  "refunded",
  "canceled",
]);

// Subscriptions Table
export const subscriptions = pgTable(
  "subscriptions",
  {
    id: uuid("id").primaryKey().defaultRandom(),
    userId: uuid("user_id")
      .notNull()
      .references(() => users.id, { onDelete: "cascade" }),

    // Payment provider details
    provider: paymentProviderEnum("provider").notNull(),
    providerSubscriptionId: varchar("provider_subscription_id", { length: 255 })
      .notNull()
      .unique(),
    providerCustomerId: varchar("provider_customer_id", {
      length: 255,
    }).notNull(),
    providerPriceId: varchar("provider_price_id", { length: 255 }),

    // Subscription details
    tier: userTierEnum("tier").notNull(),
    status: subscriptionStatusEnum("status").notNull(),
    interval: subscriptionIntervalEnum("interval").notNull(),

    // Pricing
    amount: integer("amount").notNull(), // in cents
    currency: varchar("currency", { length: 3 }).default("usd").notNull(),

    // Dates
    currentPeriodStart: timestamp("current_period_start").notNull(),
    currentPeriodEnd: timestamp("current_period_end").notNull(),
    cancelAt: timestamp("cancel_at"),
    canceledAt: timestamp("canceled_at"),
    endedAt: timestamp("ended_at"),
    trialStart: timestamp("trial_start"),
    trialEnd: timestamp("trial_end"),

    // Metadata
    metadata: jsonb("metadata"),

    createdAt: timestamp("created_at").defaultNow().notNull(),
    updatedAt: timestamp("updated_at").defaultNow().notNull(),
  },
  (table) => [
    index("subscriptions_user_id_idx").on(table.userId),
    uniqueIndex("subscriptions_provider_sub_id_idx").on(
      table.providerSubscriptionId,
    ),
    index("subscriptions_status_idx").on(table.status),
    index("subscriptions_current_period_end_idx").on(table.currentPeriodEnd),
  ],
);

// Invoices Table
export const invoices = pgTable(
  "invoices",
  {
    id: uuid("id").primaryKey().defaultRandom(),
    userId: uuid("user_id")
      .notNull()
      .references(() => users.id, { onDelete: "cascade" }),
    subscriptionId: uuid("subscription_id").references(() => subscriptions.id, {
      onDelete: "set null",
    }),

    // Payment provider details
    provider: paymentProviderEnum("provider").notNull(),
    providerInvoiceId: varchar("provider_invoice_id", { length: 255 })
      .notNull()
      .unique(),

    // Invoice details
    status: invoiceStatusEnum("status").notNull(),
    amount: integer("amount").notNull(), // in cents
    amountPaid: integer("amount_paid").default(0).notNull(),
    currency: varchar("currency", { length: 3 }).default("usd").notNull(),

    // Invoice info
    invoiceNumber: varchar("invoice_number", { length: 100 }),
    invoicePdf: text("invoice_pdf"), // URL to PDF
    hostedInvoiceUrl: text("hosted_invoice_url"), // Provider's hosted page

    // Dates
    periodStart: timestamp("period_start"),
    periodEnd: timestamp("period_end"),
    dueDate: timestamp("due_date"),
    paidAt: timestamp("paid_at"),

    // Metadata
    metadata: jsonb("metadata"),

    createdAt: timestamp("created_at").defaultNow().notNull(),
    updatedAt: timestamp("updated_at").defaultNow().notNull(),
  },
  (table) => [
    index("invoices_user_id_idx").on(table.userId),
    index("invoices_subscription_id_idx").on(table.subscriptionId),
    uniqueIndex("invoices_provider_invoice_id_idx").on(table.providerInvoiceId),
    index("invoices_status_idx").on(table.status),
    index("invoices_created_at_idx").on(table.createdAt),
  ],
);

// Payments Table (individual payment transactions)
export const payments = pgTable(
  "payments",
  {
    id: uuid("id").primaryKey().defaultRandom(),
    userId: uuid("user_id")
      .notNull()
      .references(() => users.id, { onDelete: "cascade" }),
    invoiceId: uuid("invoice_id").references(() => invoices.id, {
      onDelete: "set null",
    }),

    // Payment provider details
    provider: paymentProviderEnum("provider").notNull(),
    providerPaymentId: varchar("provider_payment_id", { length: 255 })
      .notNull()
      .unique(),
    providerPaymentIntentId: varchar("provider_payment_intent_id", {
      length: 255,
    }),

    // Payment details
    status: paymentStatusEnum("status").notNull(),
    amount: integer("amount").notNull(), // in cents
    amountRefunded: integer("amount_refunded").default(0).notNull(),
    currency: varchar("currency", { length: 3 }).default("usd").notNull(),

    // Payment method
    paymentMethod: varchar("payment_method", { length: 50 }), // card, paypal, etc.
    last4: varchar("last_4", { length: 4 }), // Last 4 digits of card
    brand: varchar("brand", { length: 50 }), // visa, mastercard, etc.

    // Transaction details
    description: text("description"),
    receiptUrl: text("receipt_url"),

    // Refund info
    refundReason: text("refund_reason"),
    refundedAt: timestamp("refunded_at"),

    // Metadata
    metadata: jsonb("metadata"),

    createdAt: timestamp("created_at").defaultNow().notNull(),
    updatedAt: timestamp("updated_at").defaultNow().notNull(),
  },
  (table) => [
    index("payments_user_id_idx").on(table.userId),
    index("payments_invoice_id_idx").on(table.invoiceId),
    uniqueIndex("payments_provider_payment_id_idx").on(table.providerPaymentId),
    index("payments_status_idx").on(table.status),
    index("payments_created_at_idx").on(table.createdAt),
  ],
);

// Pricing Plans Table (for your product catalog)
export const pricingPlans = pgTable(
  "pricing_plans",
  {
    id: uuid("id").primaryKey().defaultRandom(),

    // Plan details
    name: varchar("name", { length: 100 }).notNull(),
    tier: userTierEnum("tier").notNull().unique(),
    description: text("description"),

    // Pricing
    monthlyPrice: integer("monthly_price").notNull(), // in cents
    yearlyPrice: integer("yearly_price").notNull(), // in cents
    currency: varchar("currency", { length: 3 }).default("usd").notNull(),

    // Features/Limits
    dailyChecksLimit: integer("daily_checks_limit").notNull(),
    monthlyChecksLimit: integer("monthly_checks_limit").notNull(),
    features: jsonb("features").notNull(), // Array of feature flags

    // Provider IDs
    stripePriceIdMonthly: varchar("stripe_price_id_monthly", { length: 255 }),
    stripePriceIdYearly: varchar("stripe_price_id_yearly", { length: 255 }),

    // Status
    isActive: boolean("is_active").default(true).notNull(),
    displayOrder: integer("display_order").default(0).notNull(),

    createdAt: timestamp("created_at").defaultNow().notNull(),
    updatedAt: timestamp("updated_at").defaultNow().notNull(),
  },
  (table) => [
    uniqueIndex("pricing_plans_tier_idx").on(table.tier),
    index("pricing_plans_is_active_idx").on(table.isActive),
  ],
);

// Payment Methods Table (saved payment methods)
export const paymentMethods = pgTable(
  "payment_methods",
  {
    id: uuid("id").primaryKey().defaultRandom(),
    userId: uuid("user_id")
      .notNull()
      .references(() => users.id, { onDelete: "cascade" }),

    // Provider details
    provider: paymentProviderEnum("provider").notNull(),
    providerPaymentMethodId: varchar("provider_payment_method_id", {
      length: 255,
    })
      .notNull()
      .unique(),

    // Payment method details
    type: varchar("type", { length: 50 }).notNull(), // card, paypal, bank_account
    last4: varchar("last_4", { length: 4 }),
    brand: varchar("brand", { length: 50 }), // visa, mastercard, etc.
    expiryMonth: integer("expiry_month"),
    expiryYear: integer("expiry_year"),

    // Status
    isDefault: boolean("is_default").default(false).notNull(),
    isExpired: boolean("is_expired").default(false).notNull(),

    createdAt: timestamp("created_at").defaultNow().notNull(),
    updatedAt: timestamp("updated_at").defaultNow().notNull(),
  },
  (table) => [
    index("payment_methods_user_id_idx").on(table.userId),
    uniqueIndex("payment_methods_provider_payment_method_id_idx").on(
      table.providerPaymentMethodId,
    ),
  ],
);

// Relations
export const usersRelations = relations(users, ({ many }) => ({
  accounts: many(accounts),
  sessions: many(sessions),
  detectionResults: many(detectionResults),
  usageLogs: many(usageLogs),
  apiKeys: many(apiKeys),
  webhooks: many(webhooks),
  reports: many(reports),
}));

export const accountsRelations = relations(accounts, ({ one }) => ({
  user: one(users, {
    fields: [accounts.userId],
    references: [users.id],
  }),
}));

export const sessionsRelations = relations(sessions, ({ one }) => ({
  user: one(users, {
    fields: [sessions.userId],
    references: [users.id],
  }),
}));

export const detectionResultsRelations = relations(
  detectionResults,
  ({ one, many }) => ({
    user: one(users, {
      fields: [detectionResults.userId],
      references: [users.id],
    }),
    frameAnalyses: many(frameAnalyses),
    reports: many(reports),
  }),
);

export const frameAnalysesRelations = relations(frameAnalyses, ({ one }) => ({
  detectionResult: one(detectionResults, {
    fields: [frameAnalyses.detectionResultId],
    references: [detectionResults.id],
  }),
}));

export const usageLogsRelations = relations(usageLogs, ({ one }) => ({
  user: one(users, {
    fields: [usageLogs.userId],
    references: [users.id],
  }),
}));

export const apiKeysRelations = relations(apiKeys, ({ one }) => ({
  user: one(users, {
    fields: [apiKeys.userId],
    references: [users.id],
  }),
}));

export const webhooksRelations = relations(webhooks, ({ one }) => ({
  user: one(users, {
    fields: [webhooks.userId],
    references: [users.id],
  }),
}));

export const reportsRelations = relations(reports, ({ one }) => ({
  user: one(users, {
    fields: [reports.userId],
    references: [users.id],
  }),
  detectionResult: one(detectionResults, {
    fields: [reports.detectionResultId],
    references: [detectionResults.id],
  }),
}));

// Type exports for use in your application
export type User = typeof users.$inferSelect;
export type NewUser = typeof users.$inferInsert;

export type Account = typeof accounts.$inferSelect;
export type NewAccount = typeof accounts.$inferInsert;

export type Session = typeof sessions.$inferSelect;
export type NewSession = typeof sessions.$inferInsert;

export type DetectionResult = typeof detectionResults.$inferSelect;
export type NewDetectionResult = typeof detectionResults.$inferInsert;

export type FrameAnalysis = typeof frameAnalyses.$inferSelect;
export type NewFrameAnalysis = typeof frameAnalyses.$inferInsert;

export type UsageLog = typeof usageLogs.$inferSelect;
export type NewUsageLog = typeof usageLogs.$inferInsert;

export type ApiKey = typeof apiKeys.$inferSelect;
export type NewApiKey = typeof apiKeys.$inferInsert;

export type DetectionCache = typeof detectionCache.$inferSelect;
export type NewDetectionCache = typeof detectionCache.$inferInsert;

export type Webhook = typeof webhooks.$inferSelect;
export type NewWebhook = typeof webhooks.$inferInsert;

export type Report = typeof reports.$inferSelect;
export type NewReport = typeof reports.$inferInsert;
