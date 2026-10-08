# Frontend

React + TypeScript + Vite client for uploading meeting audio, polling the backend pipeline, reviewing results, and downloading exports.

```powershell
npm install
Copy-Item .env.example .env
npm run dev
```

Set `VITE_API_BASE_URL` to the FastAPI server URL when it is not `http://localhost:8000`. Run `npm run build` for a production build.
