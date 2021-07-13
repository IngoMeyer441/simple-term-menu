PRECOMMIT_VERSION=2.13.0
PRECOMMIT_URL=$\
	https://github.com/pre-commit/pre-commit/releases/download/$\
	v$(PRECOMMIT_VERSION)/pre-commit-$(PRECOMMIT_VERSION).pyz

no-default:
	@echo "There is no default target. Please choose one of the following targets: check, git-hooks-install"
	@exit 1

check-python:
	@if ! command -v python3 >/dev/null 2>&1; then \
		>&2 echo "Please install Python 3 first."; \
		exit 1; \
	fi;

check: check-python
	@TMP_PRECOMMIT_DIR="$$(mktemp -d 2>/dev/null || mktemp -d -t 'tmp' 2>/dev/null)" && \
	curl -L -o "$${TMP_PRECOMMIT_DIR}/pre-commit.pyz" "$(PRECOMMIT_URL)" && \
	git log -1 --pretty=%B > "$${TMP_PRECOMMIT_DIR}/commit_msg" && \
	python3 "$${TMP_PRECOMMIT_DIR}/pre-commit.pyz" run --all-files --hook-stage commit && \
	python3 "$${TMP_PRECOMMIT_DIR}/pre-commit.pyz" run --all-files --hook-stage commit-msg \
		--commit-msg-filename "$${TMP_PRECOMMIT_DIR}/commit_msg" && \
	python3 "$${TMP_PRECOMMIT_DIR}/pre-commit.pyz" run --all-files --hook-stage post-commit && \
	rm -rf "$${TMP_PRECOMMIT_DIR}"

git-hooks-install: check-python
	@TMP_PRECOMMIT_DIR="$$(mktemp -d 2>/dev/null || mktemp -d -t 'tmp' 2>/dev/null)" && \
	curl -L -o "$${TMP_PRECOMMIT_DIR}/pre-commit.pyz" "$(PRECOMMIT_URL)" && \
	python3 "$${TMP_PRECOMMIT_DIR}/pre-commit.pyz" install --hook-type pre-commit && \
	python3 "$${TMP_PRECOMMIT_DIR}/pre-commit.pyz" install --hook-type commit-msg && \
	python3 "$${TMP_PRECOMMIT_DIR}/pre-commit.pyz" install --hook-type post-commit && \
	rm -rf "$${TMP_PRECOMMIT_DIR}"

.PHONY: no-default check-python check git-hooks-install
