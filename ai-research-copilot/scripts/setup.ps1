param(
    [switch]$Docker,
    [switch]$Seed,
    [switch]$Help
)

$ROOT_DIR = Split-Path -Parent $PSScriptRoot
$BACKEND_DIR = Join-Path $ROOT_DIR "backend"
$FRONTEND_DIR = Join-Path $ROOT_DIR "frontend"

function Write-Step($message) {
    Write-Host "`n==> $message" -ForegroundColor Cyan
}

function Write-Success($message) {
    Write-Host "  [OK] $message" -ForegroundColor Green
}

function Write-Error($message) {
    Write-Host "  [FAIL] $message" -ForegroundColor Red
}

if ($Help) {
    Write-Host @"
ARC - AI Research Copilot Setup Script
========================================

Usage: .\scripts\setup.ps1 [options]

Options:
  -Docker   Use Docker Compose for infrastructure (Postgres, Redis, Qdrant, MinIO)
  -Seed     Seed the database with sample data after setup
  -Help     Show this help message

Examples:
  .\scripts\setup.ps1              # Quick setup (manual infra required)
  .\scripts\setup.ps1 -Docker      # Full Docker-based setup
  .\scripts\setup.ps1 -Docker -Seed # Docker + seed data
"@
    exit 0
}

Write-Host @"

    ╔══════════════════════════════════════════╗
    ║    ARC - AI Research Copilot Setup       ║
    ╚══════════════════════════════════════════╝

"@ -ForegroundColor Magenta

# 1. Environment file
Write-Step "Setting up environment files"
$envFile = Join-Path $ROOT_DIR ".env"
if (-not (Test-Path $envFile)) {
    $envExample = Join-Path $ROOT_DIR ".env.example"
    if (Test-Path $envExample) {
        Copy-Item $envExample $envFile
        Write-Success "Created .env from .env.example"
        Write-Host "  >> Edit .env with your configuration (API keys, secrets, etc.)" -ForegroundColor Yellow
    } else {
        Write-Error ".env.example not found at $envExample"
    }
} else {
    Write-Success ".env already exists"
}

# 2. Docker infrastructure (optional)
if ($Docker) {
    Write-Step "Starting infrastructure with Docker Compose"
    Set-Location $ROOT_DIR
    docker-compose up -d postgres redis qdrant minio
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Infrastructure services started"
    } else {
        Write-Error "Failed to start Docker services. Is Docker running?"
    }
}

# 3. Backend setup
Write-Step "Setting up backend"
Set-Location $BACKEND_DIR

# Create virtual environment
if (-not (Test-Path "venv")) {
    python -m venv venv
    Write-Success "Created Python virtual environment"
} else {
    Write-Success "Virtual environment already exists"
}

# Activate and install
$pip = Join-Path $BACKEND_DIR "venv\Scripts\pip"
$python = Join-Path $BACKEND_DIR "venv\Scripts\python"

if (Test-Path $pip) {
    Write-Step "Installing backend dependencies"
    & $pip install -e ".[dev]"
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Backend dependencies installed"
    } else {
        Write-Error "Failed to install backend dependencies"
    }
}

# Check database connection
Write-Step "Checking database connection"
$envContent = Get-Content $envFile -Raw
if ($envContent -match "DATABASE_URL.*?postgresql.*?@(.*?):") {
    $dbHost = $Matches[1]
    try {
        & $python -c "import asyncio; from app.database.session import engine; asyncio.run(engine.connect()); print('Connected')"
        Write-Success "Database connection verified"
    } catch {
        Write-Warning "Database not reachable. Start Postgres first."
    }
}

# 4. Frontend setup
Write-Step "Setting up frontend"
Set-Location $FRONTEND_DIR

if (Test-Path "node_modules") {
    Write-Success "Node modules already installed"
} else {
    npm install
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Frontend dependencies installed"
    } else {
        Write-Error "Failed to install frontend dependencies"
    }
}

# 5. Database migration
Write-Step "Running database migrations"
Set-Location $BACKEND_DIR
try {
    & $python -m alembic upgrade head
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Database migrations applied"
    }
} catch {
    Write-Warning "Could not run migrations. Check database connection."
}

# 6. Seed data (optional)
if ($Seed) {
    Write-Step "Seeding database"
    try {
        & $python -c "from app.scripts.seed_agents import seed_agents; import asyncio; asyncio.run(seed_agents())"
        Write-Success "Database seeded with sample data"
    } catch {
        Write-Error "Failed to seed database: $_"
    }
}

# Done
Write-Host @"

    ╔══════════════════════════════════════════╗
    ║         Setup Complete!                  ║
    ╚══════════════════════════════════════════╝

"@ -ForegroundColor Green

Write-Host "Start the application:" -ForegroundColor Yellow
Write-Host "  Backend:  cd backend && venv\Scripts\uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
Write-Host "  Frontend: cd frontend && npm run dev"
Write-Host ""
Write-Host "  Then open http://localhost:3000 in your browser" -ForegroundColor Cyan
