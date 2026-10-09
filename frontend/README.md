# Frontend — interfaz web

Interfaz web de Docs Assistant con Next.js App Router y TypeScript. La página consulta `/health` desde el servidor y presenta el estado de la API; las rutas proxy same-origin también manejan autenticación y, durante el Hito 5, la carga y gestión inicial de documentos.

## Requisitos

- Node.js 20.9 o superior y npm.
- API FastAPI local en `http://127.0.0.1:8000` para ver el estado disponible.

## Instalación y arranque

Desde `frontend/`:

```powershell
Copy-Item .env.example .env.local
npm.cmd ci
npm.cmd run dev
```

`Copy-Item` se usa solo la primera vez. Abre `http://localhost:3000`. Mantén la API activa en otra terminal. Si usas otra URL, configura `API_BASE_URL` en `.env.local` y reinicia el servidor. Esta variable solo se usa en el servidor Next.js; no la cambies a `NEXT_PUBLIC_API_BASE_URL`.

## Node.js y npm en Windows

npm normalmente se instala junto con Node.js usando el instalador oficial LTS. No necesitas instalar npm como dependencia del proyecto. Next.js requiere Node.js 20.9 o superior.

Después de instalar Node.js, cierra y vuelve a abrir PowerShell o VS Code para recargar `PATH`. Comprueba los comandos:

```powershell
node --version
npm.cmd --version
Get-Command node, npm.cmd
```

En PowerShell, `npm` puede intentar abrir `npm.ps1` y quedar bloqueado por la política de ejecución de scripts. `npm.cmd` usa el lanzador de Windows y evita ese bloqueo sin cambiar la política. Ejecuta los comandos desde `frontend/`, donde está `package.json`.

## Pruebas y calidad

```powershell
npm.cmd test
npm.cmd run lint
npm.cmd run typecheck
npm.cmd run build
```

`npm.cmd test` valida el estado de la API, el proxy same-origin, autenticación y el flujo de documentos. Consulta [docs/testing.md](../docs/testing.md). `package-lock.json` fija las versiones; usa `npm.cmd ci` para una instalación reproducible.
