# Video Frame Capture API Server

## ⚠️ Warning: This project is under construction and most of the features are not yet implemented.

A high-performance Node.js API server for detecting AI-generated content in video frames. Built with Fastify, PostgreSQL, and TypeScript to provide real-time authenticity detection with multi-provider AI analysis.

## 🎯 Overview

The Video Frame Capture API receives video frames from client applications and analyzes them using multiple AI detection services to determine if the content is authentic or AI-generated. The system provides confidence scores, detailed breakdowns, and comprehensive user management with tiered subscriptions.

---

## ✨ Features

### Core Functionality

- **Multi-Provider AI Detection**: Integrates with Hive, Optic, and custom ML models
- **Frame Analysis**: Processes up to 10 frames per request with parallel API calls
- **Intelligent Caching**: Stores results using perceptual hashing to reduce costs
- **Rate Limiting**: Per-user quotas based on subscription tier
- **Usage Analytics**: Detailed tracking of API costs and detection patterns

### Authentication & Authorization

- **Email & OAuth**: Sign up with email or Google/GitHub/Microsoft
- **BetterAuth Integration**: Modern, secure authentication
- **Session Management**: JWT-based sessions with automatic refresh
- **API Keys**: Programmatic access for premium users
- **Role-based Access**: Free, Premium, and Enterprise tiers

### Subscription Management

- **Stripe Integration**: Secure payment processing
- **Flexible Billing**: Monthly and yearly subscriptions
- **Webhook Handling**: Real-time updates from Stripe
- **Invoice Management**: Automated billing and receipt generation
- **Payment Methods**: Store and manage multiple payment methods

### Premium Features

- **API Key Management**: Create, rotate, and revoke API keys
- **Custom Webhooks**: Event notifications for detection completion
- **Dashboard Analytics**: Comprehensive usage statistics and trends
- **Priority Processing**: Faster queue for premium users
- **Unlimited History**: Keep all detection results indefinitely

---

## 🛠️ Tech Stack

- **Runtime**: Node.js 20+
- **Framework**: Fastify (high-performance HTTP framework)
- **Language**: TypeScript (strict mode)
- **Database**: PostgreSQL (hosted on Neon)
- **ORM**: Drizzle ORM (type-safe SQL toolkit)
- **Authentication**: BetterAuth
- **Cache**: Redis (for rate limiting & sessions)
- **Queue**: BullMQ (background job processing)
- **Payments**: Stripe
- **Validation**: Zod
- **Testing**: Vitest

---

## 📊 Database Schema

### User Management

- **users** - User accounts, subscription info, usage quotas
- **accounts** - OAuth provider connections
- **sessions** - Active user sessions with expiration
- **api_keys** - API keys for programmatic access

### Detection System

- **detection_results** - Video analysis results with metadata
- **frame_analyses** - Individual frame detection data
- **detection_cache** - Cached results (30-day TTL)

### Payment System

- **subscriptions** - Active and past subscriptions
- **invoices** - Billing history and invoice metadata
- **payments** - Individual payment transactions
- **payment_methods** - Saved payment methods
- **pricing_plans** - Product catalog with features

### Analytics & Monitoring

- **usage_logs** - API calls, costs, and resource usage
- **webhooks** - User-configured webhook endpoints
- **reports** - User feedback and false positive reports

---

## 🚀 Getting Started

### Prerequisites

- Node.js 20+ and npm/pnpm
- Neon PostgreSQL account (free tier available)
- Stripe account (test mode for development)
- Redis instance (optional for development)

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/video-frame-capture-api.git
cd video-frame-capture-api

# Install dependencies
npm install

# Setup environment variables
cp .env.example .env
# Edit .env with your credentials (see below)

# Setup database
npm run db:push

# Seed initial data (optional)
npm run db:seed

# Start development server
npm run dev
```

### Environment Variables

Create a `.env` file in the root directory:

```env
# Server
NODE_ENV=development
PORT=3000
API_URL=http://localhost:3000

# Database
DATABASE_URL=postgresql://user:password@ep-xxx.neon.tech/dbname

# Authentication
BETTER_AUTH_SECRET=your-random-secret-key-min-32-chars
BETTER_AUTH_URL=http://localhost:3000
BETTER_AUTH_TRUSTED_ORIGINS=chrome-extension://your-extension-id

# OAuth Providers (optional)
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
GITHUB_CLIENT_ID=your-github-client-id
GITHUB_CLIENT_SECRET=your-github-client-secret

# Stripe
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Redis (optional for development)
REDIS_URL=redis://localhost:6379

# AI Detection APIs
HIVE_API_KEY=your-hive-api-key
OPTIC_API_KEY=your-optic-api-key

# Email (optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASS=your-app-password

# Rate Limiting
RATE_LIMIT_MAX=100
RATE_LIMIT_WINDOW_MS=900000
```

---

## 📡 API Endpoints

### Authentication

```http
POST   /api/auth/signup
POST   /api/auth/signin
POST   /api/auth/signout
GET    /api/auth/session
POST   /api/auth/oauth/google
POST   /api/auth/oauth/github
POST   /api/auth/refresh
```

**Example: Sign Up**

```bash
curl -X POST http://localhost:3000/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepassword123",
    "name": "John Doe"
  }'
```

### Detection

```http
POST   /api/detect                    # Analyze video frames
GET    /api/detect/:id                # Get detection result
GET    /api/detect/history            # Get user's detection history
POST   /api/detect/:id/bookmark       # Toggle bookmark
PATCH  /api/detect/:id                # Update notes/feedback
DELETE /api/detect/:id                # Delete detection result
```

**Example: Analyze Frames**

```bash
curl -X POST http://localhost:3000/api/detect \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "frames": [
      {
        "data": "base64_encoded_image_data",
        "timestamp": 1000
      },
      {
        "data": "base64_encoded_image_data",
        "timestamp": 5000
      }
    ],
    "videoUrl": "https://youtube.com/watch?v=...",
    "videoTitle": "Sample Video"
  }'
```

**Response:**

```json
{
  "id": "uuid",
  "overallConfidence": 87.5,
  "authenticityScore": 89.2,
  "isLikelyAi": false,
  "confidenceLevel": "high",
  "framesAnalyzed": 10,
  "processingTimeMs": 2341,
  "detailedResults": {
    "hive": { "score": 88.3, "confidence": "high" },
    "optic": { "score": 90.1, "confidence": "very_high" }
  },
  "warningFlags": [],
  "frameAnalyses": [
    {
      "frameNumber": 1,
      "authenticityScore": 89.5,
      "aiProbability": 10.5,
      "detectedArtifacts": []
    }
  ]
}
```

### User & Profile

```http
GET    /api/user/profile              # Get user profile
PATCH  /api/user/profile              # Update profile
GET    /api/user/usage                # Get usage statistics
GET    /api/user/stats                # Get dashboard stats
DELETE /api/user/account              # Delete account
```

### Subscriptions

```http
GET    /api/subscriptions             # Get current subscription
POST   /api/subscriptions/create      # Create subscription
POST   /api/subscriptions/cancel      # Cancel subscription
POST   /api/subscriptions/resume      # Resume canceled subscription
GET    /api/subscriptions/plans       # Get available plans
```

**Example: Create Subscription**

```bash
curl -X POST http://localhost:3000/api/subscriptions/create \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "priceId": "price_1234567890",
    "paymentMethodId": "pm_1234567890"
  }'
```

### Payments & Billing

```http
GET    /api/invoices                  # Get invoice history
GET    /api/invoices/:id              # Get invoice details
GET    /api/payments                  # Get payment history
POST   /api/payment-methods           # Add payment method
GET    /api/payment-methods           # List payment methods
PATCH  /api/payment-methods/:id       # Set default payment method
DELETE /api/payment-methods/:id       # Remove payment method
```

### API Keys (Premium)

```http
POST   /api/api-keys                  # Create API key
GET    /api/api-keys                  # List API keys
PATCH  /api/api-keys/:id              # Update API key
DELETE /api/api-keys/:id              # Revoke API key
```

**Example: Create API Key**

```bash
curl -X POST http://localhost:3000/api/api-keys \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Production API Key",
    "scopes": ["detect:read", "detect:write"],
    "rateLimit": 1000
  }'
```

### Webhooks (Premium)

```http
POST   /api/webhooks                  # Create webhook
GET    /api/webhooks                  # List webhooks
PATCH  /api/webhooks/:id              # Update webhook
DELETE /api/webhooks/:id              # Delete webhook
POST   /api/webhooks/:id/test         # Test webhook
```

### Admin (Internal)

```http
GET    /api/admin/users               # List all users
GET    /api/admin/stats               # System statistics
POST   /api/admin/users/:id/ban       # Ban user
POST   /api/admin/cache/clear         # Clear detection cache
```

---

## 💰 Pricing Tiers

### Free Tier

- 20 detections per day (600/month)
- Single AI detection provider
- 30-day result retention
- Basic support

**Daily Limit**: 20 | **Monthly Limit**: 600

### Premium Tier - $9.99/month

- 500 detections per month (17/day avg)
- Multi-provider AI consensus
- Unlimited result retention
- Priority processing queue
- Dashboard analytics
- API key access
- Email support

**Daily Limit**: Flexible | **Monthly Limit**: 500

### Enterprise Tier - Custom Pricing

- Unlimited detections
- Custom ML model integration
- Dedicated infrastructure
- Webhook support
- SLA guarantees
- Dedicated account manager
- Phone support

**Daily Limit**: Unlimited | **Monthly Limit**: Unlimited

---

## 🏗️ Project Structure

```
server/
├── src/
│   ├── routes/
│   │   ├── auth.ts              # Authentication endpoints
│   │   ├── detect.ts            # Detection endpoints
│   │   ├── user.ts              # User management
│   │   ├── subscriptions.ts     # Subscription management
│   │   ├── payments.ts          # Payment endpoints
│   │   ├── webhooks.ts          # Webhook management
│   │   └── admin.ts             # Admin endpoints
│   ├── services/
│   │   ├── detection.ts         # Core detection logic
│   │   ├── ai-providers/
│   │   │   ├── hive.ts          # Hive AI integration
│   │   │   ├── optic.ts         # Optic integration
│   │   │   └── custom.ts        # Custom ML models
│   │   ├── cache.ts             # Caching service
│   │   ├── queue.ts             # Job queue management
│   │   └── stripe.ts            # Stripe integration
│   ├── middleware/
│   │   ├── auth.ts              # Authentication middleware
│   │   ├── rateLimit.ts         # Rate limiting
│   │   ├── validate.ts          # Request validation
│   │   └── errorHandler.ts     # Error handling
│   ├── db/
│   │   ├── schema.ts            # Drizzle schema
│   │   ├── queries.ts           # Database queries
│   │   ├── index.ts             # DB connection
│   │   └── seed.ts              # Seed data
│   ├── utils/
│   │   ├── hash.ts              # Perceptual hashing
│   │   ├── validation.ts        # Zod schemas
│   │   └── logger.ts            # Winston logger
│   ├── types/
│   │   └── index.ts             # TypeScript types
│   └── index.ts                 # App entry point
├── drizzle/
│   ├── migrations/              # Database migrations
│   └── meta/                    # Migration metadata
├── tests/
│   ├── auth.test.ts
│   ├── detection.test.ts
│   └── subscriptions.test.ts
├── .env.example
├── drizzle.config.ts
├── tsconfig.json
├── package.json
└── README.md
```

---

## 🗄️ Database Commands

```bash
# Generate new migration from schema changes
npm run db:generate

# Apply pending migrations
npm run db:migrate

# Push schema directly (dev only, skips migrations)
npm run db:push

# Open Drizzle Studio (visual database editor)
npm run db:studio

# Seed database with initial data
npm run db:seed

# Reset database (WARNING: deletes all data)
npm run db:reset
```

---

## 🔐 Security Features

- **Password Hashing**: bcrypt with 12 salt rounds
- **JWT Tokens**: Signed with HS256, short expiration
- **API Key Encryption**: Hashed before storage, never exposed
- **Rate Limiting**: Per-user and per-IP limits
- **Input Validation**: Zod schemas on all endpoints
- **SQL Injection Protection**: Parameterized queries via Drizzle
- **CORS**: Configured for trusted origins only
- **Webhook Signatures**: HMAC verification
- **Request Sanitization**: XSS protection
- **Helmet.js**: Security headers

---

## 🧪 Testing

```bash
# Run all tests
npm test

# Run tests in watch mode
npm run test:watch

# Run tests with coverage
npm run test:coverage

# Run specific test file
npm test -- auth.test.ts
```

---

## 📈 Monitoring & Analytics

### Logging

- **Winston**: Structured logging with multiple transports
- **Log Levels**: error, warn, info, debug
- **Request Logging**: Automatic HTTP request/response logging

### Metrics

- Detection success/failure rates
- API response times
- Provider performance comparison
- Cost per detection by provider
- User growth and churn
- Revenue metrics

### Alerting

- Failed payment notifications
- High error rates
- Unusual API usage patterns
- Provider downtime

---

## 🚢 Deployment

### Railway

```bash
# Install Railway CLI
npm i -g @railway/cli

# Login
railway login

# Deploy
railway up
```

### Render

1. Connect GitHub repository
2. Select "Web Service"
3. Set build command: `npm install && npm run build`
4. Set start command: `npm start`
5. Add environment variables
6. Deploy

### Docker

```dockerfile
FROM node:20-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build
EXPOSE 3000
CMD ["npm", "start"]
```

```bash
# Build image
docker build -t video-frame-api .

# Run container
docker run -p 3000:3000 --env-file .env video-frame-api
```

---

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes with tests
4. Run tests and linting (`npm test && npm run lint`)
5. Commit with conventional commits (`feat:`, `fix:`, etc.)
6. Push to your fork (`git push origin feature/amazing-feature`)
7. Open a Pull Request

### Development Guidelines

- Write tests for new features
- Follow existing code style
- Update documentation
- Add JSDoc comments for public APIs
- Keep PRs focused and small

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details

---

## 🔗 Resources

- **API Documentation**: [Swagger/OpenAPI docs at `/docs`]
- **Database Studio**: Run `npm run db:studio`
- **Support**: support@videoframecapture.com
- **Issues**: [GitHub Issues](https://github.com/yourusername/video-frame-capture-api/issues)

---

## 🙏 Acknowledgments

- **Fastify** - Lightning-fast web framework
- **Drizzle ORM** - Type-safe database toolkit
- **Neon** - Serverless PostgreSQL
- **Stripe** - Payment infrastructure
- **BetterAuth** - Modern authentication

---

\*\*Built with ❤️ for content authenticity
