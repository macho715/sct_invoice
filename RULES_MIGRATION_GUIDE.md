# Cursor Rules 마이그레이션 가이드 v1.0

## 📋 목차

1. [개요](#개요)
2. [변경 사항 요약](#변경-사항-요약)
3. [기존 규칙 → 새 규칙 매핑](#기존-규칙--새-규칙-매핑)
4. [마이그레이션 절차](#마이그레이션-절차)
5. [팀원별 체크리스트](#팀원별-체크리스트)
6. [FAQ](#faq)
7. [문제 해결](#문제-해결)

---

## 개요

### 목적
9개 이상의 분산된 규칙 파일을 단일 계층 구조로 통합하여:
- 중복/충돌 규칙 제거
- 누락 항목 보완 (Git 전략, 보안 도구, CI/CD)
- 프로젝트별 오버라이드 지원
- 일관된 개발 워크플로 확립

### 새 규칙 구조

```
.cursorrules                              # 전역 규칙 (루트)
├── hitachi/.cursorrules.project          # Hitachi 프로젝트 설정
├── HVDC_Invoice_Audit/.cursorrules.project  # MACHO-GPT 설정
└── ML/.cursorrules.project               # ML 파이프라인 설정
```

---

## 변경 사항 요약

### ✅ 통합된 규칙

| 기존 규칙 | 새 규칙 | 변경 내용 |
|---------|--------|---------|
| Kent Beck TDD | `.cursorrules` 섹션 1 | 통합 (Red-Green-Refactor) |
| Tidy First v3.7 | `.cursorrules` 섹션 2 | 통합 (Structural vs Behavioral) |
| MACHO-GPT v3.6 | `HVDC_Invoice_Audit/.cursorrules.project` | 프로젝트별로 분리 |
| HVDC Sync Rules | `hitachi/.cursorrules.project` | 프로젝트별로 분리 |
| Python×Excel Rules | `.cursorrules` 섹션 6 | 통합 (Excel Processing Standards) |

### ➕ 추가된 규칙

- **Git 브랜치 전략**: 보호 브랜치, PR 요구사항, force push 차단
- **테스트 커버리지**: 최소 80% (신규 코드 90%)
- **보안 스캔 도구**: bandit, safety, semgrep, cargo-audit
- **pre-commit 훅**: `.pre-commit-config.yaml` 신규 생성
- **CI/CD 파이프라인**: `.github/workflows/ci.yml` 신규 생성
- **CODEOWNERS**: `.github/CODEOWNERS` 신규 생성

### 🔄 변경된 규칙

#### 커밋 메시지 형식

**기존 (혼재)**:
```
[STRUCTURAL] / [BEHAVIORAL]     # Kent Beck
structural: / behavioral:       # v3.7
[STRUCT] / [FEAT] / [FIX]      # MACHO
```

**새 규칙 (통일)**:
```
[TYPE] scope: description

TYPE = STRUCT | FEAT | FIX | PERF | MODE | CMD | TEST | DOCS
```

#### 테스트 SLA

**기존 (충돌)**:
- Kent Beck: ≤200ms
- MACHO: <2초
- v3.7: PR ≤5분

**새 규칙 (계층화)**:
```yaml
test_sla:
  unit: 200ms
  integration: 2s
  e2e: 5min
  logistics_safety: 3s
```

#### 신뢰도 임계값

**기존 (불일치)**:
- MACHO v3.4: ≥0.90
- MACHO v3.6: ≥0.97

**새 규칙 (도메인별)**:
```yaml
confidence_threshold:
  safety_critical: 0.97       # FANR/압력계산
  compliance_critical: 0.95   # MOIAT/감사
  business_critical: 0.95     # KPI/예측
  general: 0.90              # 일반 물류
```

---

## 기존 규칙 → 새 규칙 매핑

### 커밋 메시지 매핑표

| 기존 | 새 규칙 | 예시 |
|------|--------|------|
| `[STRUCTURAL]` | `[STRUCT]` | `[STRUCT] hitachi: Extract header detection` |
| `[BEHAVIORAL]` | `[FEAT]` / `[FIX]` | `[FEAT] macho: Add OCR engine` |
| `structural:` | `[STRUCT]` | `[STRUCT] ml: Rename variables` |
| `behavioral:` | `[FEAT]` | `[FEAT] ml: Add A/B testing` |
| `feat:` | `[FEAT]` | (동일) |
| `fix:` | `[FIX]` | (동일) |

### 테스트 명령어 매핑

| 기존 | 새 규칙 | 설명 |
|------|--------|------|
| `pytest` | `pytest -m "not integration" --timeout=200` | 단위 테스트만 |
| `pytest --all` | `pytest --timeout=120` | 전체 테스트 |
| `cargo test` | `cargo test --quiet` | Rust 테스트 |
| `/automate test-pipeline` | 동일 (유지) | 전체 파이프라인 |

### 파일명 규칙 매핑

| 프로젝트 | 기존 | 새 규칙 |
|---------|------|--------|
| Hitachi | `data_synchronizer.py` | `[module]_[function].py` (동일) |
| MACHO | `logi_invoice_audit.py` | `logi_[function]_[YYMMDD].py` |
| ML | `unified_ml_pipeline.py` | `[component]_[function].py` (동일) |

---

## 마이그레이션 절차

### Phase 1: 준비 (Week 1)

#### 1.1 새 규칙 읽기
- [ ] `.cursor/rules/*.mdc` 파일들 전체 읽기 (20분)
- [ ] 본인 프로젝트의 `.cursorrules.project` 파일 읽기 (10분)
- [ ] `README_RULE_PACK.md` 읽기 (5분)
- [ ] 변경 사항 요약 확인 (5분)
- [ ] [Cursor Rules 공식 가이드](https://forum.cursor.com/t/cursor-rules-files-format-arent-clear/51419) 읽기 (10분)

#### 1.2 로컬 환경 설정
```bash
# 1. 워크스페이스 루트로 이동
cd /path/to/HVDC_Invoice_Audit-20251012T195441Z-1-001

# 2. 새 규칙 파일 존재 확인
ls -la .cursor/rules/*.mdc
ls -la hitachi/.cursorrules.project
ls -la HVDC_Invoice_Audit/.cursorrules.project
ls -la ML/.cursorrules.project
ls -la README_RULE_PACK.md

# 3. pre-commit 훅 설치 ([공식 문서](https://pre-commit.com/))
pip install pre-commit
pre-commit install
pre-commit install --hook-type commit-msg  # conventional-pre-commit용

# 4. 규칙 검증 실행
python scripts/validate_rules.py --verbose
```

#### 1.3 Git 설정 확인
```bash
# 현재 브랜치 확인
git branch

# 보호 브랜치 확인 (main/master는 직접 푸시 금지)
git remote -v
```

### Phase 2: 적응 (Week 2)

#### 2.1 커밋 메시지 연습
```bash
# 예시: Structural 변경
git commit -m "[STRUCT] hitachi: Extract date parser into separate function"

# 예시: Feature 추가
git commit -m "[FEAT] macho: Add FANR compliance auto-verification"

# 예시: Bug 수정
git commit -m "[FIX] ml: Correct feature scaling in preprocessing"
```

#### 2.2 pre-commit 훅 체험
```bash
# 파일 수정 후 커밋 시도
git add .
git commit -m "[FEAT] test: Add new feature"

# pre-commit 훅이 자동 실행됨:
# - Black formatting check
# - isort import 정렬
# - flake8 linting
# - Bandit security scan
# - GitGuardian secrets scan
# - Pytest unit tests (85% 커버리지)
# - Conventional commits 검증

# 실패 시 자동으로 수정되거나 오류 표시
```

#### 2.3 테스트 실행 연습
```bash
# 단위 테스트만 (85% 커버리지 강제)
pytest -m "not integration" --timeout=200 --cov-fail-under=85

# 전체 테스트
pytest --cov --cov-report=term --cov-fail-under=85

# 특정 프로젝트
cd hitachi && pytest -v --cov-fail-under=85

# ML 프로젝트 (긴 학습 제외)
cd ML && pytest -m "not slow" --cov-fail-under=85

# 통합 테스트
pytest -m "integration" --timeout=300
```

### Phase 3: 통합 (Week 3)

#### 3.1 CI/CD 파이프라인 활성화
- [ ] `.github/workflows/ci.yml` 파일 확인
- [ ] 첫 PR 생성 시 CI 자동 실행 확인
- [ ] 테스트/보안 스캔 결과 확인

#### 3.2 CODEOWNERS 적용
- [ ] `.github/CODEOWNERS` 파일 확인
- [ ] 본인이 소유한 코드 경로 확인
- [ ] PR 시 자동 리뷰 요청 확인

#### 3.3 CHANGELOG 자동화
```bash
# CHANGELOG 생성
python scripts/generate_changelog.py

# 특정 태그 이후
python scripts/generate_changelog.py --since v1.0.0

# 결과 확인
cat CHANGELOG.md
```

### Phase 4: 정착 (Week 4)

#### 4.1 프로젝트별 규칙 숙지
- **Hitachi 팀**: `hitachi/.cursorrules.project` 재확인
  - Master precedence 원칙
  - 헤더 정규화 규칙
  - 성능 목표 30초

- **MACHO 팀**: `HVDC_Invoice_Audit/.cursorrules.project` 재확인
  - Containment modes
  - Auto-trigger 조건
  - 명령어 추천 3개 이상

- **ML 팀**: `ML/.cursorrules.project` 재확인
  - 모델 검증 필수
  - A/B 테스팅 활성화
  - 학습 데이터 최소 1,000 샘플

#### 4.2 첫 완전 준수 PR
- [ ] 브랜치 생성: `feature/[ticket-id]-description`
- [ ] TDD 사이클 준수: Red → Green → Refactor
- [ ] 커밋 메시지 표준 준수
- [ ] 모든 테스트 통과
- [ ] pre-commit 훅 통과
- [ ] CI 파이프라인 통과
- [ ] 2인 리뷰 승인
- [ ] CODEOWNERS 승인

---

## 팀원별 체크리스트

### 개발자 (All)

- [ ] `.cursorrules` 파일 읽기 완료
- [ ] 본인 프로젝트 `.cursorrules.project` 읽기 완료
- [ ] pre-commit 훅 설치 완료
- [ ] 새 커밋 메시지 형식 숙지
- [ ] TDD 사이클 (Red-Green-Refactor) 이해
- [ ] 테스트 SLA 이해 (단위 200ms, 통합 2s)
- [ ] 신뢰도 임계값 숙지 (본인 도메인)
- [ ] Git 브랜치 전략 이해
- [ ] 첫 PR 성공

### 시니어 개발자

- [ ] 위 개발자 체크리스트 완료
- [ ] CODEOWNERS 역할 이해
- [ ] 코드 리뷰 기준 업데이트
- [ ] 주니어 개발자 멘토링
- [ ] 규칙 검증 스크립트 실행

### 팀 리더

- [ ] 전체 마이그레이션 계획 이해
- [ ] 팀원 진행 상황 모니터링
- [ ] CI/CD 파이프라인 설정 검토
- [ ] 보안 스캔 결과 검토
- [ ] 첫 4주 롤아웃 완료

---

## FAQ

### Q1: 기존 커밋 히스토리는 어떻게 되나요?
**A**: 기존 커밋은 그대로 유지됩니다. 새 규칙은 앞으로의 커밋부터 적용됩니다.

### Q2: pre-commit 훅이 너무 느립니다.
**A**: 다음 옵션을 사용하세요:
```bash
# 특정 훅만 실행
SKIP=pylint git commit -m "..."

# 훅 완전 우회 (비상시만)
git commit --no-verify -m "..."
```

### Q3: 신뢰도 임계값이 애매합니다.
**A**: 도메인별 기준:
- Safety-critical (압력계산, FANR): 0.97
- Compliance (감사, MOIAT): 0.95
- Business (KPI, 예측): 0.95
- General (일반 물류): 0.90

### Q3-1: .cursor/rules/*.mdc 파일이 어떻게 작동하나요?
**A**: Cursor IDE가 자동으로 로드:
- YAML frontmatter의 `globs` 패턴에 따라 자동 적용
- `alwaysApply: true`는 모든 파일에 적용
- 프로젝트별 `.cursorrules.project`가 오버라이드 역할

### Q4: 프로젝트별 규칙이 전역 규칙과 충돌하면?
**A**: 프로젝트별 규칙이 우선합니다 (`overrides` 섹션).

### Q5: CI 파이프라인이 실패하면 PR을 머지할 수 없나요?
**A**: 네, CI 통과가 머지 조건입니다. 실패 원인을 수정해야 합니다.

### Q6: CODEOWNERS가 없는 파일은?
**A**: 기본 `@logistics-team`이 리뷰합니다.

### Q7: 테스트 커버리지 85%를 달성하기 어렵습니다.
**A**:
1. 기존 코드는 제외 가능 (exclude_patterns: tests/*, venv/*, __pycache__/*)
2. 신규 코드만 95% 목표
3. 점진적 적용 (Week 1-2: 경고, Week 3-4: 강제)
4. 특정 파일 제외: `--cov-omit="tests/*,venv/*"`

### Q8: Rust 프로젝트는 어떻게 하나요?
**A**: `.cursorrules`의 Rust-specific 섹션 참조:
- `cargo clippy -- -D warnings`
- `cargo fmt --check`
- `cargo audit`
- Option/Result 콤비네이터 우선

---

## 문제 해결

### 문제 1: pre-commit 훅 설치 실패

**증상**:
```bash
$ pre-commit install
Error: .pre-commit-config.yaml not found
```

**해결**:
```bash
# 워크스페이스 루트 확인
pwd

# .pre-commit-config.yaml 존재 확인
ls -la .pre-commit-config.yaml

# 없으면 재생성
python scripts/validate_rules.py --fix
```

### 문제 2: 테스트 타임아웃

**증상**:
```bash
FAILED tests/test_slow.py::test_ml_training - Timeout >200ms
```

**해결**:
```bash
# 느린 테스트 마킹
@pytest.mark.slow
def test_ml_training():
    ...

# 실행 시 제외
pytest -m "not slow"

# 또는 ML 프로젝트는 10초 허용
cd ML && pytest --timeout=10
```

### 문제 3: 커밋 메시지 형식 오류

**증상**:
```bash
error: commit message does not follow format: [TYPE] scope: description
```

**해결**:
```bash
# 올바른 형식:
git commit -m "[FEAT] ml: Add new model"

# 잘못된 형식:
git commit -m "Add new model"  # [TYPE] 없음
git commit -m "[FEATURE] ml: Add new model"  # FEATURE는 FEAT로
```

### 문제 4: CODEOWNERS 승인 대기

**증상**: PR이 통과했지만 머지가 안 됨

**해결**:
1. `.github/CODEOWNERS` 확인
2. 해당 경로의 소유자 확인
3. 소유자에게 리뷰 요청
4. 긴급 시: Tech Lead 승인

### 문제 5: 규칙 검증 실패

**증상**:
```bash
$ python scripts/validate_rules.py
❌ 검증 실패: .mdc 파일 YAML frontmatter 오류
```

**해결**:
```bash
# 상세 정보 확인
python scripts/validate_rules.py --verbose

# .cursor/rules/*.mdc 파일 수정
# YAML frontmatter 형식 확인

# 재검증
python scripts/validate_rules.py

# 자동 마이그레이션 도구 사용 (향후)
python scripts/migrate_to_mdc.py
```

---

## 추가 리소스

### 프로젝트 문서
- [README_RULE_PACK.md](../README_RULE_PACK.md) - 간결한 설치/운영 가이드
- [.cursor/rules/*.mdc](../.cursor/rules/) - 모듈화된 규칙 파일들
- [Hitachi 프로젝트 규칙](../hitachi/.cursorrules.project)
- [MACHO-GPT 규칙](../HVDC_Invoice_Audit/.cursorrules.project)
- [ML 파이프라인 규칙](../ML/.cursorrules.project)

### 자동화 도구
- [규칙 검증 스크립트](../scripts/validate_rules.py) - .mdc 파일 검증
- [CHANGELOG 생성 스크립트](../scripts/generate_changelog.py)
- [마이그레이션 도구](../scripts/migrate_to_mdc.py) - .cursorrules → .mdc 변환
- [pre-commit 설정](../.pre-commit-config.yaml) - GitGuardian + conventional-pre-commit
- [CI 파이프라인](../.github/workflows/ci.yml) - 간소화된 단일 job

### 공식 문서 및 가이드

#### Cursor IDE
- [Cursor Rules 파일 형식 가이드](https://forum.cursor.com/t/cursor-rules-files-format-arent-clear/51419) - Cursor 커뮤니티 공식 가이드

## v4.1.1 하이브리드 업그레이드

### 업그레이드 완료 사항 (v5.0 → v5.0 Hybrid)

#### ✅ YAML 설정 블록 추가
README_RULE_PACK.md 상단에 구조화된 YAML 설정 블록 추가:
```yaml
---
user_rules_settings_v5_0_hybrid:
  output:
    language: "KR concise + EN-inline"
    default_lines_max: 4
    number_format: "2-dec"
    section_order: ["ExecSummary","Visual","Options","Roadmap","Automation","QA"]
    end_with_cmds: 3
  # ... 전체 설정 구조화
---
```

#### ✅ Pre-commit 간소화
- 88줄 → 40줄로 간소화
- pylint 제거 (flake8로 충분)
- YAML 형식 최적화

#### ✅ CI 파이프라인 최적화
- `ggshield secret scan repo -v --all-history` 추가
- Matrix 전략 유지 (프로젝트별 테스트)

#### ✅ 규칙 파일 간소화
- **000-core.mdc**: 30줄 → 20줄
- **040-ci-cd.mdc**: 44줄 → 35줄 (confidence 통합)
- **020-confidence.mdc**: 삭제 (040에 통합)

### 최종 구조 (v5.0 Hybrid)

```
.cursor/rules/
├── 000-core.mdc              # 20줄 (간소화) ✨
├── 010-tdd-tidy.mdc          # 30줄 (유지)
├── 030-commits-branches.mdc  # 46줄 (유지)
├── 040-ci-cd.mdc            # 35줄 (간소화 + confidence 통합) ✨
├── 100-python-excel.mdc     # 71줄 (유지)
└── 300-logistics-hvdc.mdc   # 55줄 (유지)

총 6개 파일 (7개 → 6개로 간소화)
```

### v4.1.1 요소 통합 완료

#### ✅ YAML 중심 설계
- 구조화된 설정 블록
- 간결한 pre-commit (40줄)
- 성능 최적화된 CI

#### ✅ v5.0 구조 유지
- 모듈화된 규칙 파일
- 프로젝트별 오버라이드
- Matrix CI 전략
- 상세 문서화
- 검증/자동화 스크립트

### 롤백 방법 (필요시)
```bash
# 백업에서 복원
cp -r .backup/v5.0_before_v4.1.1_upgrade/rules .cursor/
cp .backup/v5.0_before_v4.1.1_upgrade/README_RULE_PACK.md .
cp .backup/v5.0_before_v4.1.1_upgrade/.pre-commit-config.yaml .
cp .backup/v5.0_before_v4.1.1_upgrade/ci.yml .github/workflows/
```
- [Cursor Rules 기능 사용법](https://forum.cursor.com/t/can-anyone-help-me-use-this-new-cursor-rules-functionality/45692) - 신규 기능 활용법
- [Cursor 베스트 프랙티스](https://github.com/digitalchild/cursor-best-practices) - AI 에디터 최적 사용법

#### Git & 브랜치 전략
- [Trunk Based Development](https://trunkbaseddevelopment.com/) - 트렁크 기반 개발 전략
- [DORA Trunk-based Development](https://dora.dev/capabilities/trunk-based-development/) - DevOps 성능 지표
- [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) - 표준 커밋 메시지 형식

#### 코드 품질 & 테스트
- [Tidy First](https://www.oreilly.com/library/view/tidy-first/9781098151232/) - Kent Beck의 리팩토링 원칙
- [pre-commit 공식 문서](https://pre-commit.com/) - Git 훅 자동화
- [pytest-cov 설정 가이드](https://pytest-cov.readthedocs.io/en/latest/config.html) - 테스트 커버리지 도구
- [Bandit 보안 스캐너](https://bandit.readthedocs.io/) - Python 보안 취약점 검사

#### CI/CD & 협업
- [GitHub Actions Python 가이드](https://docs.github.com/actions/guides/building-and-testing-python) - GitHub Actions Python 빌드/테스트
- [GitHub CODEOWNERS 문서](https://docs.github.com/articles/about-code-owners) - 코드 소유권 관리
- [GitHub Actions 개요](https://docs.github.com/actions) - GitHub Actions 전체 가이드

### 지원 및 연락처
- **Tech Lead**: @tech-lead
- **시니어 개발자**: @senior-dev-1, @senior-dev-2
- **ML 팀**: @ml-team-lead
- **보안팀**: @security-team
- **DevOps 팀**: @devops-team
- **컴플라이언스팀**: @compliance-team

---

**마이그레이션 가이드 버전**: v1.0
**최종 업데이트**: 2025-01-12
**다음 검토**: 2025-02-12 (첫 롤아웃 4주 후)

