.PHONY: test test-verbose test-file help

# Run all tests
test:
	bats test/*.bats

# Run tests with verbose output
test-verbose:
	bats --tap test/*.bats

# Run a specific test file (usage: make test-file FILE=argument_parsing)
test-file:
	bats test/$(FILE).bats

# Show help
help:
	@echo "Available targets:"
	@echo "  make test          - Run all bats tests"
	@echo "  make test-verbose  - Run tests with TAP output"
	@echo "  make test-file FILE=name - Run specific test file (e.g., FILE=argument_parsing)"
