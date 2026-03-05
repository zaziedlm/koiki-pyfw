param(
    [switch]$SkipVolumeReset,
    [switch]$SkipBuild
)

$ErrorActionPreference = "Stop"

function Get-EnvValue {
    param(
        [string]$Path,
        [string]$Key,
        [string]$DefaultValue
    )

    if (-not (Test-Path $Path)) {
        return $DefaultValue
    }

    $line = Get-Content $Path | Where-Object { $_ -match "^$Key=(.*)$" } | Select-Object -First 1
    if (-not $line) {
        return $DefaultValue
    }

    $matches = [regex]::Match($line, "^$Key=(.*)$")
    if ($matches.Success) {
        return $matches.Groups[1].Value.Trim()
    }
    return $DefaultValue
}

function Set-EnvValue {
    param(
        [string]$Path,
        [string]$Key,
        [string]$Value
    )

    if (-not (Test-Path $Path)) {
        New-Item -Path $Path -ItemType File -Force | Out-Null
    }

    $lines = Get-Content $Path -ErrorAction SilentlyContinue
    if (-not $lines) {
        $lines = @()
    }

    $updated = $false
    for ($i = 0; $i -lt $lines.Count; $i++) {
        if ($lines[$i] -match "^$Key=") {
            $lines[$i] = "$Key=$Value"
            $updated = $true
            break
        }
    }

    if (-not $updated) {
        $lines += "$Key=$Value"
    }

    Set-Content -Path $Path -Value $lines -Encoding UTF8
}

function Ensure-EnvValue {
    param(
        [string]$Path,
        [string]$Key,
        [string]$DefaultValue
    )

    $current = Get-EnvValue -Path $Path -Key $Key -DefaultValue ""
    if (-not $current) {
        Set-EnvValue -Path $Path -Key $Key -Value $DefaultValue
    }
}

function Assert-LastExitCode {
    param(
        [string]$StepName
    )

    if ($LASTEXITCODE -ne 0) {
        throw "$StepName failed (exit code: $LASTEXITCODE)"
    }
}

Write-Host "[INFO] Preparing SAML user-table E2E environment..."

if (-not (Test-Path ".env")) {
    if (Test-Path ".env.example") {
        Copy-Item ".env.example" ".env"
        Write-Host "[INFO] .env created from .env.example (base settings)"
    } else {
        throw ".env and templates are missing."
    }

    if (Test-Path ".env.saml.example") {
        Write-Host "[INFO] Merging SAML-related settings from .env.saml.example"
        Get-Content ".env.saml.example" | ForEach-Object {
            if ($_ -match "^(SAML_[A-Z0-9_]+|SSO_LINK_BACKEND)=(.*)$") {
                $k = $matches[1]
                $v = $matches[2]

                # Skip multiline certificate placeholders in env-file merge
                if ($k -in @("SAML_IDP_X509_CERT", "SAML_SP_X509_CERT", "SAML_SP_PRIVATE_KEY")) {
                    return
                }

                Set-EnvValue -Path ".env" -Key $k -Value $v
            }
        }
    }
}

# Ensure DB settings required for migration exist (when .env was saml-only etc.)
Ensure-EnvValue -Path ".env" -Key "POSTGRES_SERVER" -DefaultValue "db"
Ensure-EnvValue -Path ".env" -Key "POSTGRES_USER" -DefaultValue "koiki_user"
Ensure-EnvValue -Path ".env" -Key "POSTGRES_PASSWORD" -DefaultValue "koiki_password"
Ensure-EnvValue -Path ".env" -Key "POSTGRES_DB" -DefaultValue "koiki_todo_db"
Ensure-EnvValue -Path ".env" -Key "POSTGRES_PORT" -DefaultValue "5432"
Ensure-EnvValue -Path ".env" -Key "DATABASE_URL" -DefaultValue "postgresql+asyncpg://koiki_user:koiki_password@db:5432/koiki_todo_db"

Set-EnvValue -Path ".env" -Key "SSO_LINK_BACKEND" -Value "user_table"
Write-Host "[INFO] Set SSO_LINK_BACKEND=user_table in .env"

$postgresUser = Get-EnvValue -Path ".env" -Key "POSTGRES_USER" -DefaultValue "koiki_user"
$postgresDb = Get-EnvValue -Path ".env" -Key "POSTGRES_DB" -DefaultValue "koiki_todo_db"

if (-not $SkipVolumeReset) {
    Write-Host "[INFO] Stopping containers and removing volumes..."
    docker compose down -v --remove-orphans
    Assert-LastExitCode -StepName "docker compose down"
}

$upArgs = @("compose", "up", "-d")
if (-not $SkipBuild) {
    $upArgs += "--build"
}
$upArgs += @("db", "keycloak", "app", "frontend")

Write-Host "[INFO] Starting stack: docker $($upArgs -join ' ')"
& docker @upArgs
Assert-LastExitCode -StepName "docker compose up"

Write-Host "[INFO] Waiting for PostgreSQL readiness..."
$ready = $false
for ($i = 0; $i -lt 90; $i++) {
    docker compose exec -T db pg_isready -U $postgresUser -d $postgresDb | Out-Null
    if ($LASTEXITCODE -eq 0) {
        $ready = $true
        break
    }
    Start-Sleep -Seconds 2
}
if (-not $ready) {
    throw "PostgreSQL did not become ready in time."
}

Write-Host "[INFO] Running Alembic migrations inside app container..."
docker compose exec -T app alembic upgrade head
Assert-LastExitCode -StepName "alembic upgrade head"

Write-Host "[INFO] Verifying migration state (alembic_version)..."
docker compose exec -T db psql -v ON_ERROR_STOP=1 -U $postgresUser -d $postgresDb -c "SELECT version_num FROM alembic_version;"
Assert-LastExitCode -StepName "verify alembic_version"

Write-Host "[INFO] Creating temporary \"user\" table for user_table backend..."
Get-Content "scripts/sql/create_user_table_for_sso.sql" -Raw `
    | docker compose exec -T db psql -v ON_ERROR_STOP=1 -U $postgresUser -d $postgresDb
Assert-LastExitCode -StepName "create temporary user table"

Write-Host "[INFO] Verifying \"user\" table columns..."
docker compose exec -T db psql -U $postgresUser -d $postgresDb -c "SELECT column_name, data_type FROM information_schema.columns WHERE table_name='user' ORDER BY ordinal_position;"
Assert-LastExitCode -StepName "verify user table columns"

Write-Host ""
Write-Host "[DONE] E2E setup completed."
Write-Host "  - Frontend: http://localhost:3000"
Write-Host "  - Backend : http://localhost:8000"
Write-Host "  - Keycloak: http://localhost:8090 (admin/admin)"
Write-Host ""
Write-Host "SAML test users (realm-saml.json):"
Write-Host "  - saml-user / Passw0rd!"
Write-Host "  - saml-admin / AdminPass123!"
Write-Host "  - saml-test / TestPass123!"
