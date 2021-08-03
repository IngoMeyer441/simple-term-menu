PRECOMMIT_VERSION=2.13.0

no-default:
	@echo "There is no default target. Please choose one of the following targets: check, git-hooks-install"
	@exit 1

check-python:
	@if ! command -v python3 >/dev/null 2>&1; then \
		>&2 echo "Please install Python 3 first."; \
		exit 1; \
	fi;
	@if ! python3 -m venv --help >/dev/null 2>&1; then \
		>&2 echo "Please install the Python 3 venv module."; \
		exit 1; \
	fi;

check: check-python
	@TMP_PRECOMMIT_DIR="$$(mktemp -d 2>/dev/null || mktemp -d -t 'tmp' 2>/dev/null)" && \
	python3 -m venv "$${TMP_PRECOMMIT_DIR}" && \
	"$${TMP_PRECOMMIT_DIR}/bin/pip" install "pre-commit==$(PRECOMMIT_VERSION)" && \
	git log -1 --pretty=%B > "$${TMP_PRECOMMIT_DIR}/commit_msg" && \
	"$${TMP_PRECOMMIT_DIR}/bin/pre-commit" run --all-files --hook-stage commit && \
	"$${TMP_PRECOMMIT_DIR}/bin/pre-commit" run --all-files --hook-stage commit-msg \
		--commit-msg-filename "$${TMP_PRECOMMIT_DIR}/commit_msg" && \
	"$${TMP_PRECOMMIT_DIR}/bin/pre-commit" run --all-files --hook-stage post-commit && \
	rm -rf "$${TMP_PRECOMMIT_DIR}"

git-hooks-install: check-python
	@TMP_PRECOMMIT_DIR="$$(mktemp -d 2>/dev/null || mktemp -d -t 'tmp' 2>/dev/null)" && \
	python3 -m venv "$${TMP_PRECOMMIT_DIR}" && \
	"$${TMP_PRECOMMIT_DIR}/bin/pip" install "pre-commit==$(PRECOMMIT_VERSION)" && \
	"$${TMP_PRECOMMIT_DIR}/bin/pre-commit" install --hook-type pre-commit && \
	"$${TMP_PRECOMMIT_DIR}/bin/pre-commit" install --hook-type commit-msg && \
	"$${TMP_PRECOMMIT_DIR}/bin/pre-commit" install --hook-type post-commit && \
	rm -rf "$${TMP_PRECOMMIT_DIR}"

.PHONY: no-default check-python check git-hooks-install
