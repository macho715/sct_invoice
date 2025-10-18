---
user_rules_settings_v5_0_hybrid:
  output:
    language: "KR concise + EN-inline"
    default_lines_max: 4
    number_format: "2-dec"
    section_order: ["ExecSummary","Visual","Options","Roadmap","Automation","QA"]
    end_with_cmds: 3
  edit_scope:
    allowed_paths: ["src/**"]
  tdd:
    source_of_truth: "plan.md"
    go_behavior: "next_unmarked_test"
    loop: ["Red","Green","Refactor"]
    test_sla: {unit_s: 0.20, integration_s: 2.00, e2e_min: 5.00}
  git:
    commits: "Conventional Commits"
    branch_model: "Trunk + short-lived feature/*"
    structural_types: ["refactor","style","docs","chore"]
    behavioral_types: ["feat","fix","perf","test"]
  ci_quality_security:
    coverage_min: 85.00
    linters: ["black","flake8","isort"]
    security: ["bandit","pip-audit --strict","ggshield"]
    codeowners_required_approvals: 2
  confidence_thresholds:
    safety_critical: 0.97
    compliance_critical: 0.95
    business_critical: 0.95
    general: 0.90
  python_excel:
    excel_new: "XlsxWriter"
    excel_edit: "openpyxl"
    pandas_role: "IO layer"
    sheet_update: 'if_sheet_exists="replace"'
  domain_hvdc:
    triggers:
      rate_change_pct: 10.00
      eta_delay_h: 24.00
      cert_expiry_days_min: 30.00
    human_gate: ["MOIAT"]  # FANR 제거됨
  modes: ["PRIME","ORACLE","ZERO","LATTICE","RHYTHM","COST_GUARD"]
---

# Cursor Rule Pack v5.0 (Hybrid)

구조: .cursor/rules/*.mdc (모듈화) + .cursorrules.project (프로젝트별)
적용: glob 기반 자동 + 프로젝트 오버라이드

## 설치

1) **pre-commit 훅 설치**
```bash
pip install pre-commit
pre-commit install
pre-commit install --hook-type commit-msg  # conventional-pre-commit용
```

2) **브랜치 보호 + Code Owners**
- main/master 브랜치 보호 설정
- Require review from Code Owners 활성화

3) **CI 활성화**
- `.github/workflows/ci.yml` 자동 실행
- Codecov 연동 (선택사항)

## 구조

### .cursor/rules/*.mdc (모듈화 규칙)
- `000-core.mdc`: 핵심 제약사항 (NDA/PII, HallucinationBan)
- `010-tdd-tidy.mdc`: TDD + Tidy First 원칙
- `020-confidence.mdc`: 도메인별 신뢰도 임계값
- `030-commits-branches.mdc`: Git 전략, 커밋 표준
- `040-ci-cd.mdc`: 품질 게이트, 커버리지
- `100-python-excel.mdc`: Python/Excel 표준
- `300-logistics-hvdc.mdc`: 물류 도메인 규칙

### .cursorrules.project (프로젝트별 오버라이드)
- `hitachi/.cursorrules.project`: HVDC Sync 특화 설정
- `HVDC_Invoice_Audit/.cursorrules.project`: MACHO-GPT 설정
- `ML/.cursorrules.project`: ML 파이프라인 설정

## 운영 KPI

- **Coverage ≥ 85%** (신규 코드 95%)
- **Lint 오류 0, Bandit High 0, Secrets 0**
- **PR Gate 통과율 ≥ 95%**
- **CI 파이프라인 < 5분**
- **테스트 SLA**: unit ≤200ms, integration ≤2s, e2e ≤5min

## 주요 기능

### GitGuardian Secrets 스캔
- API 키, 비밀번호, 토큰 자동 감지
- 실시간 보안 위협 탐지

### Conventional Commits 자동 검증
- 커밋 메시지 형식: `[TYPE] scope: description`
- 자동 CHANGELOG 생성 지원

### 도메인별 신뢰도 관리
- Safety Critical: ≥0.97
- Compliance Critical: ≥0.95
- Business Critical: ≥0.95
- General: ≥0.90

### 자동화 도구
- `scripts/validate_rules.py`: 규칙 검증
- `scripts/generate_changelog.py`: CHANGELOG 자동 생성
- `scripts/migrate_to_mdc.py`: 규칙 마이그레이션

## 프로젝트별 설정

### Hitachi (HVDC Sync)
```yaml
master_precedence: always
header_normalization: case_no
performance_target: 30s
color_coding:
  date_change: FFC000
  new_row: FFFF00
```

### MACHO-GPT
```yaml
containment_modes: [PRIME, ORACLE, ZERO, LATTICE, RHYTHM, COST_GUARD]
auto_triggers: enabled
confidence_min: 0.97
command_recommendations: 3
```

### ML Pipeline
```yaml
model_validation: mandatory
training_data_min_samples: 1000
ab_testing: enabled
test_timeout: 10s  # 모델 학습 제외
```

## 문제 해결

### pre-commit 훅 설치 실패
```bash
# 워크스페이스 루트 확인
pwd

# .pre-commit-config.yaml 존재 확인
ls -la .pre-commit-config.yaml

# 재설치
pre-commit uninstall
pre-commit install
```

### 커밋 메시지 형식 오류
```bash
# 올바른 형식
git commit -m "[FEAT] ml: Add new model"

# 잘못된 형식
git commit -m "Add new model"  # [TYPE] 없음
```

### 테스트 커버리지 부족
```bash
# 커버리지 확인
pytest --cov=. --cov-report=term

# 특정 파일 제외
pytest --cov=. --cov-report=term --cov-omit="tests/*,venv/*"
```

## 다른 프로젝트에 적용하기

### 🚀 자동 설치 (권장)

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

### 📋 수동 복사

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

### 🎯 프로젝트별 커스터마이징

#### 도메인별 규칙 추가
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
EOF
```

#### 프로젝트별 오버라이드
```bash
cat > .cursorrules.project << 'EOF'
# Project: E-commerce Platform
## Override Settings
- Coverage threshold: 90% (instead of 85%)
- Language: EN-only (no KR)
EOF
```

### 📚 상세 가이드

- **[DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md)**: 완전한 배포 가이드
- **[RULES_MIGRATION_GUIDE.md](./RULES_MIGRATION_GUIDE.md)**: 기존 프로젝트 마이그레이션

## 지원

- **Tech Lead**: @tech-lead
- **시니어 개발자**: @senior-dev-1, @senior-dev-2
- **ML 팀**: @ml-team-lead
- **보안팀**: @security-team
- **DevOps 팀**: @devops-team

---

**버전**: v5.0 (Hybrid)
**최종 업데이트**: 2025-01-12
**다음 검토**: 2025-04-12
