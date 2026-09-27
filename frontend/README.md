# Frontend — Hito 2

Interfaz inicial de Docs Assistant con Next.js App Router y TypeScript. La página consulta `/health` desde el servidor y presenta un estado sencillo; no envía detalles de red al navegador. El desarrollo del Hito 2 está implementado. Las comprobaciones locales pasan; la ejecución de GitHub Actions queda pendiente de confirmación.

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

Abre `http://localhost:3000`. Mantén la API activa en otra terminal. Si usas otra URL, configura `API_BASE_URL` en `.env.local` y reinicia el servidor. Esta variable se usa solo en el servidor Next.js; no la cambies a `NEXT_PUBLIC_API_BASE_URL`.

## Node.js y npm en Windows

npm es el gestor de paquetes de Node.js y normalmente se instala junto con Node.js usando el instalador oficial LTS. No necesitas instalar npm como dependencia del proyecto. Next.js requiere Node.js 20.9 o superior; las versiones posteriores que cumplan ese mínimo son válidas.

Después de instalar Node.js, cierra y vuelve a abrir PowerShell o VS Code para que la terminal recargue `PATH`. Comprueba que ambos comandos están disponibles:

```powershell
node --version
npm.cmd --version
Get-Command node, npm.cmd
```

Ejecuta `npm.cmd ci` **desde `frontend/`**, donde está `package.json`. En PowerShell, `npm` puede intentar abrir `npm.ps1` y quedar bloqueado por la política de ejecución de scripts; `npm.cmd` llama al lanzador de Windows y evita ese bloqueo sin cambiar la política. Si `npm.cmd` tampoco se reconoce, repara o reinstala Node.js desde el instalador oficial y comprueba que la carpeta de Node se añadió a `PATH`.
## Pruebas y calidad

```powershell
npm.cmd test
npm.cmd run lint
npm.cmd run typecheck
npm.cmd run build
```

`npm.cmd test` valida los casos disponibles/no disponibles, el rechazo de esquemas que no sean HTTP(S), el manejo de errores de red y el anuncio accesible del estado. Consulta [docs/testing.md](../docs/testing.md) para el registro y el propósito de cada grupo de pruebas.

El `package-lock.json` fija las versiones resueltas. Consérvalo en Git y usa `npm.cmd ci` para instalaciones reproducibles.
