Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Push-Location $PSScriptRoot
try {
    $composeFile = "docker-compose.deploy.yml"
    $envFile = Join-Path $PSScriptRoot ".env"
    $createEnvironment = -not (Test-Path $envFile)

    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
        throw "No se encontro Docker. Instala Docker Desktop y vuelve a ejecutar este archivo."
    }

    & docker info --format "{{.ServerVersion}}" *> $null
    if ($LASTEXITCODE -ne 0) {
        throw "Docker no esta iniciado. Abre Docker Desktop y vuelve a ejecutar este archivo."
    }

    if ($createEnvironment) {
        $templatePath = Join-Path $PSScriptRoot ".env.example"
        if (-not (Test-Path $templatePath)) {
            throw "No se encontro .env.example; no se puede preparar la configuracion local."
        }

        $environment = Get-Content -Raw $templatePath
    }
    else {
        $environment = Get-Content -Raw $envFile
    }

    $passwordMatch = [regex]::Match($environment, "(?m)^POSTGRES_PASSWORD=(.*)$")
    if (-not $passwordMatch.Success) {
        throw ".env no contiene POSTGRES_PASSWORD; revisa la configuracion antes de continuar."
    }

    $replacePassword = [string]::IsNullOrWhiteSpace($passwordMatch.Groups[1].Value) -or
        $passwordMatch.Groups[1].Value.Trim() -eq "change_me_locally"
    if ($replacePassword) {
        $random = [System.Security.Cryptography.RandomNumberGenerator]::Create()
        $bytes = New-Object byte[] 24
        try {
            $random.GetBytes($bytes)
        }
        finally {
            $random.Dispose()
        }
        $localPassword = [System.BitConverter]::ToString($bytes).Replace("-", "").ToLowerInvariant()
        $environment = [regex]::Replace(
            $environment,
            "(?m)^POSTGRES_PASSWORD=.*$",
            "POSTGRES_PASSWORD=$localPassword",
            1
        )
    }

    if ($createEnvironment -or $replacePassword) {
        $encoding = New-Object System.Text.UTF8Encoding($false)
        [System.IO.File]::WriteAllText($envFile, $environment, $encoding)
        Write-Host "Se asigno una contrasena aleatoria local en .env. El archivo no debe subirse a Git."
    }

    if (-not (Test-Path $composeFile)) {
        throw "No se encontro $composeFile en la carpeta del proyecto."
    }

    $composeArgs = @("--project-name", "docs-assistant-local", "--env-file", ".env", "-f", $composeFile)
    & docker compose @composeArgs config --quiet
    if ($LASTEXITCODE -ne 0) {
        throw "La configuracion de Docker Compose no es valida. Revisa .env."
    }

    Write-Host "Aplicando migraciones de la base de datos..."
    & docker compose @composeArgs run --build --rm api alembic upgrade head
    if ($LASTEXITCODE -ne 0) {
        throw "Fallo la migracion. Revisa el mensaje anterior; no se han borrado los datos."
    }

    Write-Host "Construyendo e iniciando la aplicacion..."
    & docker compose @composeArgs up --build --detach
    if ($LASTEXITCODE -ne 0) {
        throw "No se pudo iniciar el stack. Revisa el mensaje anterior."
    }

    $ready = $false
    for ($attempt = 0; $attempt -lt 30; $attempt++) {
        try {
            $response = Invoke-WebRequest `
                -Uri "http://127.0.0.1:3000" `
                -TimeoutSec 5 `
                -UseBasicParsing
            if ($response.StatusCode -eq 200) {
                $ready = $true
                break
            }
        }
        catch {
            Start-Sleep -Seconds 2
        }
    }

    if (-not $ready) {
        & docker compose @composeArgs ps
        throw "La aplicacion no respondio en http://localhost:3000. Consulta los logs con: docker compose --project-name docs-assistant-local --env-file .env -f docker-compose.deploy.yml logs"
    }

    Write-Host ""
    Write-Host "La aplicacion esta lista: http://localhost:3000"
    Write-Host "Para detenerla sin borrar los datos: docker compose --project-name docs-assistant-local --env-file .env -f docker-compose.deploy.yml down"
    Write-Host "RAG necesita una OPENAI_API_KEY propia en .env; sin ella no se llama a OpenAI."
}
catch {
    Write-Error $_
    exit 1
}
finally {
    Pop-Location
}
