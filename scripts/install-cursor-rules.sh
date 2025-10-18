#!/bin/bash
# Cursor Rule Pack v5.0 Hybrid 설치 스크립트 (Linux/macOS용)
# 사용법: ./install-cursor-rules.sh -t /path/to/new-project

set -e  # 오류 시 종료

# 기본값 설정
TARGET_PROJECT="."
INCLUDE_CI=false
INCLUDE_CODEOWNERS=false
INCLUDE_SCRIPTS=false
DRY_RUN=false
FORCE=false

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 로그 함수들
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️ $1${NC}"; }
log_info() { echo -e "${BLUE}ℹ️ $1${NC}"; }

# 도움말 표시
show_help() {
    cat << EOF
Cursor Rule Pack v5.0 Hybrid 설치 스크립트

사용법: $0 [옵션]

옵션:
    -t, --target PATH        타겟 프로젝트 경로 (기본값: 현재 디렉토리)
    -c, --include-ci         CI 워크플로우 포함
    -o, --include-codeowners CODEOWNERS 파일 포함
    -s, --include-scripts    scripts 폴더 포함
    -d, --dry-run           실제 설치하지 않고 미리보기만
    -f, --force             강제 설치 (기존 파일 덮어쓰기)
    -h, --help              이 도움말 표시

예시:
    $0 -t /path/to/project
    $0 -t /path/to/project --include-ci --include-scripts
    $0 --dry-run

EOF
}

# 인자 파싱
while [[ $# -gt 0 ]]; do
    case $1 in
        -t|--target)
            TARGET_PROJECT="$2"
            shift 2
            ;;
        -c|--include-ci)
            INCLUDE_CI=true
            shift
            ;;
        -o|--include-codeowners)
            INCLUDE_CODEOWNERS=true
            shift
            ;;
        -s|--include-scripts)
            INCLUDE_SCRIPTS=true
            shift
            ;;
        -d|--dry-run)
            DRY_RUN=true
            shift
            ;;
        -f|--force)
            FORCE=true
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            log_error "알 수 없는 옵션: $1"
            show_help
            exit 1
            ;;
    esac
done

# 메인 시작
echo -e "${GREEN}🚀 Cursor Rule Pack v5.0 Hybrid 설치 시작...${NC}"
echo ""

# 소스 프로젝트 경로 (스크립트 위치 기준)
SOURCE_PROJECT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
log_info "소스 프로젝트: $SOURCE_PROJECT"
log_info "타겟 프로젝트: $TARGET_PROJECT"
echo ""

# 타겟 프로젝트 존재 확인
if [[ ! -d "$TARGET_PROJECT" ]]; then
    log_warning "타겟 프로젝트가 존재하지 않습니다: $TARGET_PROJECT"
    read -p "새로 생성하시겠습니까? (y/n): " create
    if [[ "$create" =~ ^[Yy]$ ]]; then
        mkdir -p "$TARGET_PROJECT"
        log_success "타겟 프로젝트 생성됨: $TARGET_PROJECT"
    else
        log_error "설치를 중단합니다."
        exit 1
    fi
fi

# 백업 생성
BACKUP_DIR="$TARGET_PROJECT/.backup"
TIMESTAMP=$(date +"%Y%m%d-%H%M%S")
BACKUP_PATH="$BACKUP_DIR/before_rule_pack_install_$TIMESTAMP"

if [[ "$DRY_RUN" == false ]]; then
    mkdir -p "$BACKUP_PATH"
    log_success "백업 디렉토리 생성: $BACKUP_PATH"
fi

# 설치할 파일들 정의
declare -A FILES_TO_INSTALL
FILES_TO_INSTALL[".cursor/rules/000-core.mdc"]=true
FILES_TO_INSTALL[".cursor/rules/010-tdd-tidy.mdc"]=true
FILES_TO_INSTALL[".cursor/rules/030-commits-branches.mdc"]=true
FILES_TO_INSTALL[".cursor/rules/040-ci-cd.mdc"]=true
FILES_TO_INSTALL[".pre-commit-config.yaml"]=true
FILES_TO_INSTALL["README_RULE_PACK.md"]=true
FILES_TO_INSTALL["RULES_MIGRATION_GUIDE.md"]=true
FILES_TO_INSTALL[".cursor/rules/100-python-excel.mdc"]=true
FILES_TO_INSTALL[".cursor/rules/300-logistics-hvdc.mdc"]=true

# 선택적 파일들
if [[ "$INCLUDE_CI" == true ]]; then
    FILES_TO_INSTALL[".github/workflows/ci.yml"]=true
fi

if [[ "$INCLUDE_CODEOWNERS" == true ]]; then
    FILES_TO_INSTALL[".github/CODEOWNERS"]=true
fi

log_info "설치할 파일들:"
for file in "${!FILES_TO_INSTALL[@]}"; do
    if [[ "${FILES_TO_INSTALL[$file]}" == true ]]; then
        echo "  📄 $file"
    fi
done

if [[ "$INCLUDE_SCRIPTS" == true ]]; then
    echo "  📁 scripts/ (전체 폴더)"
fi

echo ""

# 파일 복사 함수
copy_project_file() {
    local source_file="$1"
    local target_file="$2"
    local required="${3:-true}"

    local source_path="$SOURCE_PROJECT/$source_file"
    local target_path="$TARGET_PROJECT/$target_file"

    if [[ ! -f "$source_path" ]]; then
        if [[ "$required" == true ]]; then
            log_error "필수 파일이 없습니다: $source_file"
            return 1
        else
            log_warning "선택 파일이 없습니다: $source_file (건너뜀)"
            return 0
        fi
    fi

    if [[ "$DRY_RUN" == true ]]; then
        log_info "[DRY-RUN] 복사할 예정: $source_file → $target_file"
        return 0
    fi

    # 타겟 디렉토리 생성
    local target_dir=$(dirname "$target_path")
    mkdir -p "$target_dir"

    # 기존 파일 백업
    if [[ -f "$target_path" ]]; then
        local backup_file="$BACKUP_PATH/$target_file"
        local backup_dir=$(dirname "$backup_file")
        mkdir -p "$backup_dir"
        cp "$target_path" "$backup_file"
        log_info "백업됨: $target_file"
    fi

    # 파일 복사
    cp "$source_path" "$target_path"
    log_success "설치됨: $target_file"
    return 0
}

# 파일들 복사
log_info "파일 복사 중..."
all_success=true

for file in "${!FILES_TO_INSTALL[@]}"; do
    if [[ "${FILES_TO_INSTALL[$file]}" == true ]]; then
        if ! copy_project_file "$file" "$file" true; then
            all_success=false
        fi
    fi
done

# scripts 폴더 복사
if [[ "$INCLUDE_SCRIPTS" == true ]]; then
    local scripts_source="$SOURCE_PROJECT/scripts"
    local scripts_target="$TARGET_PROJECT/scripts"

    if [[ -d "$scripts_source" ]]; then
        if [[ "$DRY_RUN" == false ]]; then
            if [[ -d "$scripts_target" ]]; then
                cp -r "$scripts_target" "$BACKUP_PATH/"
                log_info "백업됨: scripts/"
            fi
            cp -r "$scripts_source" "$scripts_target"
            log_success "설치됨: scripts/"
        else
            log_info "[DRY-RUN] 복사할 예정: scripts/ → scripts/"
        fi
    else
        log_warning "scripts 폴더가 없습니다: $scripts_source"
        all_success=false
    fi
fi

if [[ "$all_success" == false ]]; then
    log_error "일부 파일 설치에 실패했습니다."
    exit 1
fi

# pre-commit 설치
if [[ "$DRY_RUN" == false ]]; then
    log_info "pre-commit 설치 중..."

    # Git 저장소 확인/초기화
    if [[ ! -d "$TARGET_PROJECT/.git" ]]; then
        cd "$TARGET_PROJECT"
        git init > /dev/null 2>&1
        log_success "Git 저장소 초기화됨"
        cd - > /dev/null
    fi

    # pre-commit 설치
    cd "$TARGET_PROJECT"
    if command -v pip &> /dev/null; then
        pip install pre-commit > /dev/null 2>&1 || log_warning "pip install pre-commit 실패"
        log_success "pre-commit 패키지 설치됨"

        pre-commit install > /dev/null 2>&1 || log_warning "pre-commit install 실패"
        log_success "pre-commit 훅 설치됨"

        pre-commit install --hook-type commit-msg > /dev/null 2>&1 || log_warning "commit-msg 훅 설치 실패"
        log_success "commit-msg 훅 설치됨"
    else
        log_warning "pip이 설치되지 않았습니다. 수동으로 설치해주세요: pip install pre-commit && pre-commit install"
    fi
    cd - > /dev/null
fi

# 설치 완료 메시지
echo ""
log_success "🎉 Cursor Rule Pack v5.0 Hybrid 설치 완료!"
echo ""
log_info "다음 단계:"
echo "  1. Cursor IDE 재시작 (Ctrl+Shift+P → 'Reload Window')"
echo "  2. 규칙 검증: python scripts/validate_rules.py --verbose"
echo "  3. 첫 커밋으로 테스트"
echo ""
log_info "백업 위치: $BACKUP_PATH"
echo ""

if [[ "$DRY_RUN" == true ]]; then
    log_warning "이것은 DRY-RUN이었습니다. 실제 설치를 원하면 --dry-run 없이 다시 실행하세요."
fi
