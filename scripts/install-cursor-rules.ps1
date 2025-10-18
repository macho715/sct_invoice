# Cursor Rule Pack v5.0 Hybrid 설치 스크립트
# 사용법: .\install-cursor-rules.ps1 -TargetProject "C:\path\to\new-project"

param(
    [string]$TargetProject = ".",
    [switch]$IncludeCI,
    [switch]$IncludeCodeowners,
    [switch]$IncludeScripts,
    [switch]$DryRun,
    [switch]$Force
)

# 색상 정의
$ErrorColor = "Red"
$SuccessColor = "Green"
$WarningColor = "Yellow"
$InfoColor = "Cyan"

# 로그 함수들
function Write-Success($message) { Write-Host "✅ $message" -ForegroundColor $SuccessColor }
function Write-Error($message) { Write-Host "❌ $message" -ForegroundColor $ErrorColor }
function Write-Warning($message) { Write-Host "⚠️ $message" -ForegroundColor $WarningColor }
function Write-Info($message) { Write-Host "ℹ️ $message" -ForegroundColor $InfoColor }

# 메인 시작
Write-Host "🚀 Cursor Rule Pack v5.0 Hybrid 설치 시작..." -ForegroundColor Green
Write-Host ""

# 소스 프로젝트 경로 (현재 스크립트 위치 기준)
$SourceProject = Split-Path -Parent $PSScriptRoot
Write-Info "소스 프로젝트: $SourceProject"
Write-Info "타겟 프로젝트: $TargetProject"
Write-Host ""

# 타겟 프로젝트 존재 확인
if (-not (Test-Path $TargetProject)) {
    Write-Warning "타겟 프로젝트가 존재하지 않습니다: $TargetProject"
    $create = Read-Host "새로 생성하시겠습니까? (y/n)"
    if ($create -eq "y" -or $create -eq "Y") {
        New-Item -ItemType Directory -Path $TargetProject -Force | Out-Null
        Write-Success "타겟 프로젝트 생성됨: $TargetProject"
    }
    else {
        Write-Error "설치를 중단합니다."
        exit 1
    }
}

# 백업 생성
$BackupDir = Join-Path $TargetProject ".backup"
$Timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$BackupPath = Join-Path $BackupDir "before_rule_pack_install_$Timestamp"

if (-not $DryRun) {
    if (Test-Path $BackupPath) {
        Remove-Item $BackupPath -Recurse -Force
    }
    New-Item -ItemType Directory -Path $BackupPath -Force | Out-Null
    Write-Success "백업 디렉토리 생성: $BackupPath"
}

# 설치할 파일들 정의
$FilesToInstall = @{
    # 필수 파일들
    ".cursor/rules/000-core.mdc"             = $true
    ".cursor/rules/010-tdd-tidy.mdc"         = $true
    ".cursor/rules/030-commits-branches.mdc" = $true
    ".cursor/rules/040-ci-cd.mdc"            = $true
    ".pre-commit-config.yaml"                = $true
    "README_RULE_PACK.md"                    = $true
    "RULES_MIGRATION_GUIDE.md"               = $true

    # 선택적 파일들
    ".cursor/rules/100-python-excel.mdc"     = $true
    ".cursor/rules/300-logistics-hvdc.mdc"   = $true
    ".github/workflows/ci.yml"               = $IncludeCI
    ".github/CODEOWNERS"                     = $IncludeCodeowners
}

# scripts 폴더 복사 여부
$ScriptsToInstall = @{
    "scripts/validate_rules.py"     = $IncludeScripts
    "scripts/generate_changelog.py" = $IncludeScripts
}

Write-Info "설치할 파일들:"
foreach ($file in $FilesToInstall.GetEnumerator()) {
    if ($file.Value) {
        Write-Host "  📄 $($file.Key)" -ForegroundColor Gray
    }
}

if ($IncludeScripts) {
    Write-Host "  📁 scripts/ (전체 폴더)" -ForegroundColor Gray
}

Write-Host ""

# 파일 복사 함수
function Copy-ProjectFile {
    param(
        [string]$SourceFile,
        [string]$TargetFile,
        [bool]$Required = $true
    )

    $SourcePath = Join-Path $SourceProject $SourceFile
    $TargetPath = Join-Path $TargetProject $TargetFile

    if (-not (Test-Path $SourcePath)) {
        if ($Required) {
            Write-Error "필수 파일이 없습니다: $SourceFile"
            return $false
        }
        else {
            Write-Warning "선택 파일이 없습니다: $SourceFile (건너뜀)"
            return $true
        }
    }

    if ($DryRun) {
        Write-Info "[DRY-RUN] 복사할 예정: $SourceFile → $TargetFile"
        return $true
    }

    # 타겟 디렉토리 생성
    $TargetDir = Split-Path $TargetPath -Parent
    if (-not (Test-Path $TargetDir)) {
        New-Item -ItemType Directory -Path $TargetDir -Force | Out-Null
    }

    # 기존 파일 백업
    if (Test-Path $TargetPath) {
        $BackupFile = Join-Path $BackupPath $TargetFile
        $BackupFileDir = Split-Path $BackupFile -Parent
        if (-not (Test-Path $BackupFileDir)) {
            New-Item -ItemType Directory -Path $BackupFileDir -Force | Out-Null
        }
        Copy-Item $TargetPath $BackupFile -Force
        Write-Info "백업됨: $TargetFile"
    }

    # 파일 복사
    Copy-Item $SourcePath $TargetPath -Force
    Write-Success "설치됨: $TargetFile"
    return $true
}

# 파일들 복사
Write-Info "파일 복사 중..."
$AllSuccess = $true

foreach ($file in $FilesToInstall.GetEnumerator()) {
    if ($file.Value) {
        $success = Copy-ProjectFile -SourceFile $file.Key -TargetFile $file.Key -Required $true
        if (-not $success) {
            $AllSuccess = $false
        }
    }
}

# scripts 폴더 복사
if ($IncludeScripts) {
    $ScriptsSource = Join-Path $SourceProject "scripts"
    $ScriptsTarget = Join-Path $TargetProject "scripts"

    if (Test-Path $ScriptsSource) {
        if (-not $DryRun) {
            if (Test-Path $ScriptsTarget) {
                $ScriptsBackup = Join-Path $BackupPath "scripts"
                Copy-Item $ScriptsTarget $ScriptsBackup -Recurse -Force
                Write-Info "백업됨: scripts/"
            }
            Copy-Item $ScriptsSource $ScriptsTarget -Recurse -Force
            Write-Success "설치됨: scripts/"
        }
        else {
            Write-Info "[DRY-RUN] 복사할 예정: scripts/ → scripts/"
        }
    }
    else {
        Write-Warning "scripts 폴더가 없습니다: $ScriptsSource"
        $AllSuccess = $false
    }
}

if (-not $AllSuccess) {
    Write-Error "일부 파일 설치에 실패했습니다."
    exit 1
}

# pre-commit 설치
if (-not $DryRun) {
    Write-Info "pre-commit 설치 중..."

    # Git 저장소 확인/초기화
    $GitDir = Join-Path $TargetProject ".git"
    if (-not (Test-Path $GitDir)) {
        Set-Location $TargetProject
        git init | Out-Null
        Write-Success "Git 저장소 초기화됨"
        Set-Location $SourceProject
    }

    # pre-commit 설치
    Set-Location $TargetProject
    try {
        pip install pre-commit | Out-Null
        Write-Success "pre-commit 패키지 설치됨"

        pre-commit install | Out-Null
        Write-Success "pre-commit 훅 설치됨"

        pre-commit install --hook-type commit-msg | Out-Null
        Write-Success "commit-msg 훅 설치됨"
    }
    catch {
        Write-Warning "pre-commit 설치 중 오류: $($_.Exception.Message)"
        Write-Warning "수동으로 설치해주세요: pip install pre-commit && pre-commit install"
    }
    finally {
        Set-Location $SourceProject
    }
}

# 설치 완료 메시지
Write-Host ""
Write-Success "🎉 Cursor Rule Pack v5.0 Hybrid 설치 완료!"
Write-Host ""
Write-Info "다음 단계:"
Write-Host "  1. Cursor IDE 재시작 (Ctrl+Shift+P → 'Reload Window')" -ForegroundColor Gray
Write-Host "  2. 규칙 검증: python scripts/validate_rules.py --verbose" -ForegroundColor Gray
Write-Host "  3. 첫 커밋으로 테스트" -ForegroundColor Gray
Write-Host ""
Write-Info "백업 위치: $BackupPath"
Write-Host ""

if ($DryRun) {
    Write-Warning "이것은 DRY-RUN이었습니다. 실제 설치를 원하면 -DryRun 없이 다시 실행하세요."
}
