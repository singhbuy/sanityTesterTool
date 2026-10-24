# PC Execution Engine runner (design.md v6 §2.2): Playwright is the
# mandatory, no-alternative driver for the PC/desktop target. No device
# farm applies here — this is the whole PC-side infra, a container image
# CI invokes per run.
#
# Does NOT cover mobile (Appium WebView-context vs Drizz, still a 2-way
# open choice per requirements.md v1.4 — see infra/README.md) and does NOT
# stand up the CI pipeline itself (trigger is an existing CI webhook,
# design.md §4 Non-Functional).

FROM mcr.microsoft.com/playwright:v1.48.0-jammy

WORKDIR /runner

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

ENTRYPOINT ["node", "run-case.js"]
