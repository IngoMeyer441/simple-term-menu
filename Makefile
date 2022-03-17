PRECOMMIT_VERSION = 2.17.0

PRECOMMIT_ENV := $(shell git rev-parse --git-dir 2>/dev/null || echo ".")/.pre-commit_env

no-default:
	@echo "There is no default target. Please choose one of the following targets: check, git-hooks-install"
	@exit 1

check-git:
	@if ! command -v git >/dev/null 2>&1; then \
		>&2 echo "Please install Git first."; \
		exit 1; \
	fi
	@if ! git rev-parse --git-dir >/dev/null 2>&1; then \
		>&2 echo "You are not in a Git repository, but pre-commit requires this."; \
		>&2 echo "Is this an unpacked source code archive?"; \
		exit 1; \
	fi

check-python:
	@if ! command -v python3 >/dev/null 2>&1; then \
		>&2 echo "Please install Python 3 first."; \
		exit 1; \
	fi
	@if ! python3 -m venv --help >/dev/null 2>&1; then \
		>&2 echo "Please install the Python 3 venv module."; \
		exit 1; \
	fi

install-pre-commit: check-git check-python
	@if ! [ -d "$(PRECOMMIT_ENV)" ] || ! "$(PRECOMMIT_ENV)/bin/python" --version >/dev/null 2>&1; then \
		echo "Installing pre-commit to \"$(PRECOMMIT_ENV)\"" && \
		rm -rf "$(PRECOMMIT_ENV)" && \
		python3 -m venv "$(PRECOMMIT_ENV)" && \
		"$(PRECOMMIT_ENV)/bin/pip" install "pre-commit==$(PRECOMMIT_VERSION)" || exit; \
	fi

check: install-pre-commit
	@TMP_PRECOMMIT_DIR="$$(mktemp -d 2>/dev/null || mktemp -d -t 'tmp' 2>/dev/null)" && \
	git log -1 --pretty=%B > "$${TMP_PRECOMMIT_DIR}/commit_msg" && \
	"$(PRECOMMIT_ENV)/bin/pre-commit" run \
		--all-files \
		--show-diff-on-failure \
		--hook-stage commit && \
	"$(PRECOMMIT_ENV)/bin/pre-commit" run \
		--all-files \
		--show-diff-on-failure \
		--hook-stage commit-msg \
		--commit-msg-filename "$${TMP_PRECOMMIT_DIR}/commit_msg" && \
	"$(PRECOMMIT_ENV)/bin/pre-commit" run \
		--all-files \
		--show-diff-on-failure \
		--hook-stage post-commit; \
	RETURN_CODE="$$?"; \
	rm -rf "$${TMP_PRECOMMIT_DIR}"; \
	exit "$${RETURN_CODE}"

git-hooks-install: install-pre-commit
	@"$(PRECOMMIT_ENV)/bin/pre-commit" install --hook-type pre-commit && \
	"$(PRECOMMIT_ENV)/bin/pre-commit" install --hook-type commit-msg && \
	"$(PRECOMMIT_ENV)/bin/pre-commit" install --hook-type post-commit

.PHONY: no-default check-git check-python check git-hooks-install
