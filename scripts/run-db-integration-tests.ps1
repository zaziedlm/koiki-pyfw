param(
    [string]$DbContainerName = "",
    [string]$DbServiceName = "db",
    [string]$AdminUser = "koiki_user",
    [string]$AdminDatabase = "postgres",
    [string]$TestDbName = "test_db",
    [string]$TestDbUser = "test_user",
    [string]$TestDbPassword = "test_pass",
    [string]$EnvFile = ".env.ci"
)

$ErrorActionPreference = "Stop"

function Assert-LastExitCode {
    param(
        [string]$StepName
    )

    if ($LASTEXITCODE -ne 0) {
        throw "$StepName failed (exit code: $LASTEXITCODE)"
    }
}

function Resolve-DbContainerName {
    param(
        [string]$RequestedContainerName,
        [string]$ServiceName
    )

    if ($RequestedContainerName) {
        docker inspect $RequestedContainerName | Out-Null 2>$null
        if ($LASTEXITCODE -eq 0) {
            return $RequestedContainerName
        }
        throw "Container '$RequestedContainerName' was not found."
    }

    $composeContainerId = docker compose ps -q $ServiceName 2>$null
    if ($LASTEXITCODE -eq 0 -and $composeContainerId) {
        $resolvedName = docker inspect --format "{{.Name}}" $composeContainerId 2>$null
        if ($LASTEXITCODE -eq 0 -and $resolvedName) {
            return $resolvedName.TrimStart("/")
        }
    }

    $runningNames = docker ps --format "{{.Names}}" 2>$null
    $hint = if ($runningNames) {
        "Running containers: " + (($runningNames | Where-Object { $_ }) -join ", ")
    } else {
        "No running containers were detected."
    }

    throw "Could not resolve the PostgreSQL container for compose service '$ServiceName'. $hint"
}

function Invoke-ContainerPsql {
    param(
        [string]$Sql,
        [string]$Database = $AdminDatabase,
        [string]$User = $AdminUser
    )

    & docker exec $DbContainerName psql -v ON_ERROR_STOP=1 -U $User -d $Database -c $Sql
    Assert-LastExitCode -StepName "psql command"
}

function Invoke-ContainerPsqlScalar {
    param(
        [string]$Sql,
        [string]$Database = $AdminDatabase,
        [string]$User = $AdminUser
    )

    $result = & docker exec $DbContainerName psql -t -A -U $User -d $Database -c $Sql
    Assert-LastExitCode -StepName "psql command"
    return ($result | Out-String).Trim()
}

$DbContainerName = Resolve-DbContainerName -RequestedContainerName $DbContainerName -ServiceName $DbServiceName
Write-Host "[INFO] Target DB container: $DbContainerName"

Write-Host "[INFO] Ensuring role '$TestDbUser' exists..."
$createRoleSql = @"
DO `$`$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = '$TestDbUser') THEN
    CREATE ROLE $TestDbUser LOGIN PASSWORD '$TestDbPassword';
  ELSE
    ALTER ROLE $TestDbUser WITH LOGIN PASSWORD '$TestDbPassword';
  END IF;
END
`$`$;
"@
Invoke-ContainerPsql -Sql $createRoleSql

Write-Host "[INFO] Ensuring database '$TestDbName' exists..."
$databaseExists = Invoke-ContainerPsqlScalar -Sql "SELECT 1 FROM pg_database WHERE datname = '$TestDbName';"
if (-not $databaseExists) {
    Invoke-ContainerPsql -Sql "CREATE DATABASE $TestDbName OWNER $TestDbUser;"
} else {
    Write-Host "[INFO] Database '$TestDbName' already exists. Reusing it."
}

Write-Host "[INFO] Verifying connection as '$TestDbUser' to '$TestDbName'..."
docker exec -i $DbContainerName psql -U $TestDbUser -d $TestDbName -c "SELECT current_database(), current_user;"
Assert-LastExitCode -StepName "verify test database connection"

$env:RUN_DB_INTEGRATION = "1"
$env:DATABASE_URL = "postgresql+asyncpg://$TestDbUser`:$TestDbPassword@localhost:5432/$TestDbName"
$env:ENV_FILE = $EnvFile

Write-Host "[INFO] RUN_DB_INTEGRATION=$env:RUN_DB_INTEGRATION"
Write-Host "[INFO] DATABASE_URL=$env:DATABASE_URL"
Write-Host "[INFO] ENV_FILE=$env:ENV_FILE"
Write-Host "[INFO] Running db_integration tests..."

uv run pytest `
  components/koiki_ref_app/tests/integration/app/api/test_auth_api.py `
  tests/integration/services/ `
  -m db_integration

Assert-LastExitCode -StepName "db_integration pytest"

Write-Host ""
Write-Host "[DONE] db_integration tests completed successfully."
