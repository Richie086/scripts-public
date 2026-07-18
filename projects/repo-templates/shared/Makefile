.PHONY: setup lint test run clean

setup:
	@if [ -d backend ] && [ -f backend/Makefile ]; then $(MAKE) -C backend setup; fi
	@if [ -d frontend ] && [ -f frontend/Makefile ]; then $(MAKE) -C frontend setup; fi
	@if [ -d scripts ] && [ -f scripts/Makefile ]; then $(MAKE) -C scripts setup; fi

lint:
	@if [ -d backend ] && [ -f backend/Makefile ]; then $(MAKE) -C backend lint; fi
	@if [ -d frontend ] && [ -f frontend/Makefile ]; then $(MAKE) -C frontend lint; fi
	@if [ -d scripts ] && [ -f scripts/Makefile ]; then $(MAKE) -C scripts lint; fi

test:
	@if [ -d backend ] && [ -f backend/Makefile ]; then $(MAKE) -C backend test; fi
	@if [ -d frontend ] && [ -f frontend/Makefile ]; then $(MAKE) -C frontend test; fi
	@if [ -d scripts ] && [ -f scripts/Makefile ]; then $(MAKE) -C scripts test; fi

run:
	@if [ -d backend ] && [ -f backend/Makefile ]; then $(MAKE) -C backend run; fi
	@if [ -d frontend ] && [ -f frontend/Makefile ]; then $(MAKE) -C frontend run; fi
