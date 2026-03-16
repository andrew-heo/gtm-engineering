# GTM StratOps Webapp

React + Tailwind portfolio app for GTM strategy and operations workflows.

## Current scope

- App shell with sidebar navigation
- Fully built `Territory Balancing` page
- Placeholder entries for the next workflows

## Run locally

```bash
npm install
npm run dev
```

## Build

```bash
npm run build
```

## Deploy on Vercel

This app can be hosted on Vercel's free tier.

Use these project settings in Vercel:

- Framework Preset: `Vite`
- Root Directory: `projects/apps/gtm-stratops-webapp`
- Build Command: `npm run build`
- Output Directory: `dist`
- Install Command: `npm install`

If you import the whole `gtm-engineering` repo, set the Root Directory above so Vercel deploys this app instead of the Python portfolio root.

## Content model

Workflow content is defined in `src/data/workflows.js`. Add new workflow objects there to expand the app.
