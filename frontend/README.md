# Request Inspector frontend

Vue 3 + Vite + TypeScript single-page app for the inbox UI. Styling uses Tailwind with the Airmail tokens in `src/assets/index.css`, and components come from radix-vue and lucide-vue-next.

## Scripts

- `npm run dev`: start the Vite dev server. `/api` is proxied to `RI_BACKEND_URL` (default `http://localhost:8000`).
- `npm run build`: type-check with `vue-tsc`, then build to `dist/`.
- `npm run preview`: serve the production build locally.
- `npm run lint`: run ESLint with auto-fix.

## Structure

- `src/views/`: route pages. `InboxView` is lazy-loaded at `/i/:id`.
- `src/components/`: app shell (`AppHeader`), shared pieces (`MethodStamp`, `RecentInboxes`), and `ui/` primitives.
- `src/api/`: typed REST client and wire types that mirror the backend schemas.
- `src/lib/`: session tokens (sessionStorage), recent inboxes and formatting helpers.
- `src/composables/`: `useTheme` (light, dark or system, stored in `ri:theme`).
- `src/router/index.ts`: routes, legacy `/inspector/*` redirects, and page titles.
