PRECOMMIT_VERSION=2.13.0
PRECOMMIT_URL=$\
	https://github.com/pre-commit/pre-commit/releases/download/$\
	v$(PRECOMMIT_VERSION)/pre-commit-$(PRECOMMIT_VERSION).pyz

git-hooks-install:
	@if ! command -v python3 >/dev/null 2>&1; then \
		>&2 echo "Please install Python 3 first."; \
		exit 1; \
	fi; \
	TMP_PRECOMMIT_DIR="$$(mktemp -d 2>/dev/null || mktemp -d -t 'tmp' 2>/dev/null)" && \
	curl -L -o "$${TMP_PRECOMMIT_DIR}/pre-commit.pyz" "$(PRECOMMIT_URL)" && \
	python3 "$${TMP_PRECOMMIT_DIR}/pre-commit.pyz" install && \
	python3 "$${TMP_PRECOMMIT_DIR}/pre-commit.pyz" install --hook-type commit-msg && \
	rm -rf "$${TMP_PRECOMMIT_DIR}"

.PHONY: git-hooks-install
