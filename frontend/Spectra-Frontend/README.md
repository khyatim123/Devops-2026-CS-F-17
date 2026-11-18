# SPECTRA Frontend

A standalone React + Vite dashboard. This is a **new frontend project**; it does not replace, edit, or contain your drowsiness backend or either existing application.

## 1. Extract the ZIP

Extract `Spectra-Frontend` into your projects folder. Keep it alongside your existing folders, for example:

```text
Devops-2026-CS-F-17-backup/
└── frontend/
    ├── Spectra-Frontend/       # NEW dashboard
    ├── drowsy-frontend/        # EXISTING driver safety frontend
    └── mail_detection-frontend/ # EXISTING email frontend
```

Do not copy this folder over `backend`, `drowsy-frontend`, or `mail_detection-frontend`.

## 2. Install and start SPECTRA

Open PowerShell in the new `Spectra-Frontend` folder:

```powershell
npm install
Copy-Item .env.example .env
npm run dev
```

Open the Vite URL printed in the terminal (normally `http://localhost:5173`).

## 3. Configure your existing frontends

Open `.env`. Set `VITE_DRIVER_APP_URL` and `VITE_EMAIL_APP_URL` to the actual Vite URLs printed by the terminals for your two existing frontends.

Example only:

```env
VITE_DRIVER_APP_URL=http://localhost:5174
VITE_EMAIL_APP_URL=http://localhost:5175
VITE_DRIVER_API_URL=http://127.0.0.1:8001
VITE_EMAIL_API_URL=http://127.0.0.1:8002
```

The frontend URLs (5174/5175 in this example) are browser pages. The backend URLs (8001/8002 in this example) are API services. They are different things.

After editing `.env`, stop and restart SPECTRA (`Ctrl+C`, then `npm run dev`).

## 4. Start your existing projects separately

Start each existing frontend and backend using its own instructions/terminal. SPECTRA opens the two existing frontend pages in separate browser tabs from the sidebar and module cards.

## Important

- This dashboard does not replace `backend/app.py` or any drowsiness detection code.
- It does not move or merge the MailShield project.
- Analytics and health-check panels are placeholders until the real backend endpoints are connected.
- If a module opens the wrong page, correct its frontend URL in `.env`.
