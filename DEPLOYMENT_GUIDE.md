# Cursor Rule Pack v5.0 Hybrid 배포 가이드

## 개요

이 가이드는 **Cursor Rule Pack v5.0 Hybrid**를 다른 프로젝트에 배포하는 방법을 설명합니다.

## 🚀 빠른 시작

### 방법 1: 자동 설치 스크립트 (권장)

#### Windows (PowerShell)
```powershell
# 기본 설치
.\scripts\install-cursor-rules.ps1

# 모든 옵션 포함 설치
.\scripts\install-cursor-rules.ps1 -TargetProject "C:\path\to\project" -IncludeCI -IncludeCodeowners -IncludeScripts

# 미리보기 (실제 설치하지 않음)
.\scripts\install-cursor-rules.ps1 -DryRun
```

#### Linux/macOS (Bash)
```bash
# 실행 권한 부여
chmod +x scripts/install-cursor-rules.sh

# 기본 설치
./scripts/install-cursor-rules.sh

# 모든 옵션 포함 설치
./scripts/install-cursor-rules.sh -t /path/to/project --include-ci --include-codeowners --include-scripts

# 미리보기 (실제 설치하지 않음)
./scripts/install-cursor-rules.sh --dry-run
```

### 방법 2: 수동 복사

```bash
# 1. 필수 파일/폴더 복사
cp -r .cursor .
cp .pre-commit-config.yaml .
cp README_RULE_PACK.md .
cp RULES_MIGRATION_GUIDE.md .

# 2. 선택적 파일 복사
cp -r .github .  # CI/CD 포함
cp -r scripts .  # 유틸리티 스크립트 포함

# 3. 설치
pip install pre-commit
git init  # Git 저장소가 없다면
pre-commit install
pre-commit install --hook-type commit-msg

# 4. Cursor IDE 재시작
# Ctrl+Shift+P → "Reload Window"
```

## 📋 설치 옵션

### 필수 구성 요소
- `.cursor/rules/*.mdc` - 핵심 규칙 파일들
- `.pre-commit-config.yaml` - Git 훅 설정
- `README_RULE_PACK.md` - 사용 가이드
- `RULES_MIGRATION_GUIDE.md` - 마이그레이션 가이드

### 선택적 구성 요소

#### CI/CD 파이프라인 (`-IncludeCI` / `--include-ci`)
- `.github/workflows/ci.yml` - GitHub Actions 워크플로우
- 자동화된 테스트, 린팅, 보안 스캔

#### 코드 소유권 (`-IncludeCodeowners` / `--include-codeowners`)
- `.github/CODEOWNERS` - 코드 리뷰 정책
- 핵심 경로에 대한 2인 승인 강제

#### 유틸리티 스크립트 (`-IncludeScripts` / `--include-scripts`)
- `scripts/validate_rules.py` - 규칙 검증 도구
- `scripts/generate_changelog.py` - CHANGELOG 자동 생성

## 🎯 프로젝트별 커스터마이징

### 1. 도메인별 규칙 추가

새로운 도메인 규칙을 추가하려면 `.cursor/rules/` 디렉토리에 새 파일을 생성하세요:

```bash
# 예: 금융 도메인 규칙
cat > .cursor/rules/400-finance.mdc << 'EOF'
---
description: Finance domain rules
globs: ["finance/**", "accounting/**"]
---

# Finance Domain Rules

## SOX Compliance
- All financial calculations must have audit trail
- Minimum 4-eye principle for transactions >$10K

## Precision
- Use Decimal type for money (never float)
- Round to 2 decimals for display
EOF
```

### 2. 프로젝트별 오버라이드

프로젝트 루트에 `.cursorrules.project` 파일을 생성하여 설정을 오버라이드할 수 있습니다:

```bash
cat > .cursorrules.project << 'EOF'
# Project: E-commerce Platform

## Override Settings
- Coverage threshold: 90% (instead of 85%)
- Test timeout: 5s (instead of default)
- Language: EN-only (no KR)

## Additional Rules
- All API responses must be <200ms
- Redis cache for hot data (>1000 req/min)
EOF
```

### 3. 기존 프로젝트 통합

기존 프로젝트에 통합할 때는 다음 단계를 따르세요:

1. **백업 생성**: 자동 설치 스크립트가 백업을 생성합니다
2. **충돌 해결**: 기존 설정과 충돌하는 부분을 확인하고 조정
3. **점진적 적용**: 핵심 규칙부터 단계적으로 적용
4. **팀 교육**: 새로운 규칙과 워크플로우에 대한 팀 교육

## 🔧 고급 배포 방법

### Git Submodule 방식 (중앙 관리)

```bash
# 1. Rule Pack을 별도 저장소로 만들기
cd /path/to/HVDC_Invoice_Audit
git init cursor-rule-pack
cd cursor-rule-pack
cp -r ../.cursor .
cp -r ../.github .
cp ../.pre-commit-config.yaml .
cp ../README_RULE_PACK.md .
cp -r ../scripts .
git add .
git commit -m "feat: initialize cursor rule pack v5.0"
git remote add origin <your-repo-url>
git push -u origin main

# 2. 다른 프로젝트에서 사용
cd /path/to/new-project
git submodule add <your-repo-url> .cursor-rules
ln -s .cursor-rules/.cursor .
ln -s .cursor-rules/.github .
ln -s .cursor-rules/.pre-commit-config.yaml .
```

### 패키지화 (고급)

```python
# pyproject.toml 생성
[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "cursor-hvdc-rules"
version = "5.0.0"
description = "HVDC Project Cursor Rules Pack"

# 설치
pip install cursor-hvdc-rules
cursor-rules install  # 자동 설치 스크립트
```

## 🛠️ 트러블슈팅

### 일반적인 문제들

#### 1. PowerShell 실행 정책 오류
```powershell
# 해결 방법
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

#### 2. pre-commit 설치 실패
```bash
# Python 가상환경 확인
python --version
pip --version

# 수동 설치
pip install pre-commit
pre-commit install
```

#### 3. Git 저장소 없음
```bash
# Git 초기화
git init
git add .
git commit -m "feat: add cursor rule pack v5.0"
```

#### 4. 파일 권한 문제 (Linux/macOS)
```bash
# 실행 권한 부여
chmod +x scripts/install-cursor-rules.sh
chmod +x scripts/*.py
```

### 검증 및 테스트

#### 설치 검증
```bash
# 규칙 파일 검증
python scripts/validate_rules.py --verbose

# pre-commit 훅 테스트
pre-commit run --all-files
```

#### 기능 테스트
```bash
# 테스트 커밋
git add .
git commit -m "feat: test cursor rule pack installation"

# CI 파이프라인 테스트 (GitHub Actions가 설정된 경우)
git push origin main
```

## 📊 성능 최적화

### CI 파이프라인 최적화

```yaml
# .github/workflows/ci.yml에서 최적화 옵션
strategy:
  matrix:
    project: [hitachi, macho, ml]
  fail-fast: true  # 하나 실패 시 전체 중단
  max-parallel: 3  # 병렬 실행 수 제한
```

### Pre-commit 훅 최적화

```yaml
# .pre-commit-config.yaml에서 최적화
default_language_version: python3.11
fail_fast: false  # 모든 훅 실행 후 실패 보고
```

## 🔄 업데이트 및 유지보수

### 규칙 업데이트

```bash
# 최신 Rule Pack으로 업데이트
git pull origin main
./scripts/install-cursor-rules.sh --force

# 특정 규칙만 업데이트
cp .cursor/rules/000-core.mdc /path/to/project/.cursor/rules/
```

### 버전 관리

```bash
# Rule Pack 버전 확인
grep "version.*5.0" README_RULE_PACK.md

# 호환성 확인
python scripts/validate_rules.py --check-compatibility
```

## 📞 지원 및 피드백

### 문제 신고
- GitHub Issues를 통해 버그 신고
- 개선 제안은 Pull Request로 제출

### 커뮤니티
- Cursor Discord 서버에서 질문
- Stack Overflow에 `cursor-rules` 태그로 질문

---

**다음 단계**: 설치 완료 후 [README_RULE_PACK.md](./README_RULE_PACK.md)를 참조하여 규칙 시스템을 활용하세요.
