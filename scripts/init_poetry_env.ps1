#!/usr/bin/env pwsh
# init_poetry_env.ps1 - Poetryによる開発環境初期化スクリプト

# 必要なPythonバージョンを確認
$pythonVersion = "3.11.7"
$pythonExists = $null -ne (Get-Command python -ErrorAction SilentlyContinue)
if (-not $pythonExists) {
    Write-Error "Python is not installed or not in PATH. Please install Python $pythonVersion." -ForegroundColor Red
    exit 1
}

$currentVersion = & python -c "import sys; print('.'.join(map(str, sys.version_info[:3])))"
Write-Host "Current Python version: $currentVersion"
if ($currentVersion -ne $pythonVersion) {
    Write-Host "Warning: Python version $pythonVersion is recommended. Consider using pyenv." -ForegroundColor Yellow
}

# 基本パッケージがインストールされていることを確認
Write-Host "Ensuring bootstrap packages are installed..." -ForegroundColor Cyan
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$bootstrapRequirements = Join-Path $scriptDir "bootstrap_requirements.txt"

if (Test-Path $bootstrapRequirements) {
    Write-Host "Installing basic bootstrap packages..." -ForegroundColor Cyan
    
    # ブートストラップパッケージのインストール
    # Poetry取得前の初期段階では、pip を使う必要があります
    try {
        # UTF-8エンコーディングでrequirementsファイルを読み込む
        $requirementLines = Get-Content -Path $bootstrapRequirements -Encoding UTF8 | 
            Where-Object { -not [string]::IsNullOrWhiteSpace($_) -and -not $_.StartsWith("#") }
        
        foreach ($requirement in $requirementLines) {
            Write-Host "Installing $requirement..." -ForegroundColor Cyan
            & python -m pip install -q $requirement
            
            if ($LASTEXITCODE -ne 0) {
                Write-Host "Failed to install $requirement." -ForegroundColor Red
                exit 1
            }
        }
        Write-Host "Bootstrap packages installed successfully." -ForegroundColor Green
    }
    catch {
        Write-Host "Error installing bootstrap packages: $_" -ForegroundColor Red
        exit 1
    }
}

# プロジェクトルートディレクトリのパスを取得
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$rootDir = Split-Path -Parent $scriptDir

# プロジェクトルートディレクトリに移動
Push-Location $rootDir

try {
    # poetryのインストール確認と必要に応じてインストール
    $poetryInstalled = $null -ne (Get-Command poetry -ErrorAction SilentlyContinue)
    if (-not $poetryInstalled) {
        Write-Host "Installing poetry package manager..." -ForegroundColor Cyan
        (Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -
        # PATHを更新
        $env:PATH = "$HOME\.poetry\bin;$env:PATH"
    }
    
    # 既存のpoetry環境があれば破棄するオプション（より確実なクリーンインストール用）
    if (Test-Path -Path ".\.venv" -PathType Container) {
        Write-Host "Existing virtual environment found. Recreating for clean installation..." -ForegroundColor Yellow
        Remove-Item -Path ".\.venv" -Recurse -Force -ErrorAction SilentlyContinue
    }      # structlogパッケージのインストール確認（Poetryを使用）
    $structlogInstalled = $null -ne (& poetry show structlog 2>$null)
    if (-not $structlogInstalled) {
        Write-Host "Installing structlog package..." -ForegroundColor Cyan
        poetry add "structlog@>=23.2.0,<24.0.0"
    } else {
        Write-Host "structlog package already installed." -ForegroundColor Green
    }
      
    # pydantic-settingsパッケージのインストール確認（Poetryを使用）
    $pydanticSettingsInstalled = $null -ne (& poetry show pydantic-settings 2>$null)
    if (-not $pydanticSettingsInstalled) {
        Write-Host "Installing pydantic-settings package..." -ForegroundColor Cyan
        poetry add "pydantic-settings@^2.9.1"
    } else {
        Write-Host "pydantic-settings package already installed." -ForegroundColor Green
    }
    
    # 既存のpyproject.tomlからプロジェクト設定を読み込む
    poetry install      # テスト関連のパッケージがインストールされているか確認（Poetryを使用）
    $pytestInstalled = $null -ne (& poetry show --group dev pytest 2>$null)
    if (-not $pytestInstalled) {
        Write-Host "Installing test packages..." -ForegroundColor Cyan
        poetry add --group dev pytest pytest-asyncio pytest-cov pytest-mock
    } else {
        Write-Host "Test packages already installed." -ForegroundColor Green
    }
      # libkoikiをeditable modeでインストール
    Write-Host "Installing libkoiki in development mode..." -ForegroundColor Cyan
    poetry config virtualenvs.create true
    poetry config virtualenvs.in-project true
      if (Test-Path -Path "./libkoiki" -PathType Container) {
        # libkoiki内もPoetry初期化
        Push-Location ./libkoiki
        
        # libkoiki内のpyproject.tomlがあるか確認
        if (Test-Path -Path "./pyproject.toml" -PathType Leaf) {
            Write-Host "Installing dependencies for libkoiki..." -ForegroundColor Cyan
            poetry install
        }
        
        # libkoikiを開発モードでインストール（Poetryを使用）
        Write-Host "Installing libkoiki in development mode from ./libkoiki..." -ForegroundColor Cyan
        Pop-Location
        
        # プロジェクトルートに戻ってからlibkoikiをPoetryの開発モードで追加
        poetry add --editable "./libkoiki"
    } else {
        Write-Error "libkoiki directory not found. Skipping installation."
    }    # Poetryのキャッシュが正常に機能していることを検証
    Write-Host "Verifying poetry environment..." -ForegroundColor Cyan
    $poetryStatus = & poetry --version 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Poetry installation verification failed. Trying to fix..." -ForegroundColor Yellow
        # Poetryのキャッシュをクリア
        if (Test-Path -Path "$HOME/.cache/pypoetry") {
            Remove-Item -Path "$HOME/.cache/pypoetry" -Recurse -Force -ErrorAction SilentlyContinue
        }
        if (Test-Path -Path "$HOME/.poetry") {
            Remove-Item -Path "$HOME/.poetry/cache" -Recurse -Force -ErrorAction SilentlyContinue
        }
    }
    
    # 仮想環境のアクティベート
    Write-Host "Activating virtual environment..." -ForegroundColor Cyan
    poetry shell

    Write-Host "Poetry environment initialized successfully!" -ForegroundColor Green
    Write-Host "You can now run 'poetry run uvicorn app.main:app --reload' to start the application." -ForegroundColor Green
}
catch {
    Write-Host "Error during Poetry environment initialization: $_" -ForegroundColor Red
}
finally {
    # 元のディレクトリに戻る
    Pop-Location
}
