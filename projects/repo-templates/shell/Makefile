.PHONY: setup lint test run

setup:
	@echo "Checking for shellcheck..."
	@command -v shellcheck >/dev/null || echo "Please install shellcheck (e.g. sudo apt install shellcheck)"
	@echo "Checking for bats..."
	@command -v bats >/dev/null || echo "Please install bats-core (e.g. git clone bats-core)"

lint:
	shellcheck bash/*.sh || echo "ShellCheck not installed or errors found"

test:
	bats tests/ || echo "Bats not installed or tests failed"

run:
	./bash/example.sh --help
