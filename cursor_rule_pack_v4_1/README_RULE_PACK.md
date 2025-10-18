# Cursor Rule Pack v4.1

구조: Core → TDD/Tidy → Commits/Branches → CI/CD → Python → Logistics(HVDC)
적용: .cursor/rules/*.mdc 는 globs 기준 자동 적용. 팀 전역 규칙은 평문으로 유지.

설치
1) 저장소 루트에 본 파일 구조 그대로 복사
2) pre-commit 설치: pip install pre-commit && pre-commit install && pre-commit install --hook-type commit-msg
3) 브랜치 보호: main 보호 + Require review from Code Owners
4) CI 활성화: .github/workflows/ci.yml

운영 KPI
- Coverage ≥ 85.00
- Lint 오류 0, Bandit High 0, Secrets 0
- PR Gate 통과율 ≥ 95.00
