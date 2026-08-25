FROM node:22-alpine AS base
RUN corepack enable && corepack prepare pnpm@10.34.2 --activate

# Step 1: Rebuild the source code only when needed
FROM base AS builder
WORKDIR /app
COPY pnpm-lock.yaml* pnpm-workspace.yaml package.json turbo.json tsconfig.base.json ./
COPY apps/web ./apps/web
COPY packages ./packages

RUN pnpm install --frozen-lockfile=false
RUN pnpm --filter @benchpress/telemetry build
RUN pnpm --filter @benchpress/sdk build
RUN pnpm --filter web build

# Step 2: Production image, copy all the files and run next
FROM base AS runner
WORKDIR /app

ENV NODE_ENV=production
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

COPY --from=builder /app/apps/web/public ./apps/web/public
COPY --from=builder --chown=nextjs:nodejs /app/apps/web/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/apps/web/.next/static ./apps/web/.next/static

USER nextjs
EXPOSE 3000

CMD ["node", "apps/web/server.js"]
