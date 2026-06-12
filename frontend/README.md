# Frontend

React + TypeScript + Vite + Tailwind. Thin client over the FastAPI backend.

```bash
npm install
npm run dev          # http://localhost:5173
npm run build
npm run lint         # tsc --noEmit
```

`VITE_API_BASE_URL` defaults to `http://localhost:8000/api/v1`.

## Routes

- `/login` — public sign-in page
- `/patients` — clinician patient search
- `/patients/:id` — full clinician workflow (risk gauge, SHAP drivers, checklist, PDF export, AI chat panel)
- `/dashboard/clinician` — clinician overview (stubbed widgets)
- `/dashboard/case-manager` — case manager overview (stubbed widgets)
- `/dashboard/admin` — administrator overview (stubbed widgets)

Route guards live in `src/auth/RequireAuth.tsx`; role-aware navigation in
`src/components/AppShell.tsx`.
