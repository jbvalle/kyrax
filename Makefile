# Catch numeric args (e.g., `make 42`)
ifneq (,$(filter-out $(firstword $(MAKEFILE_LIST)),$(MAKECMDGOALS)))
  NUMBER := $(word 1, $(MAKECMDGOALS))
  # Ignore the arg as an actual target
  $(eval $(NUMBER):;@:)
endif

all: test

test:
	echo $(NUMBER)

habit:
	@source env/bin/activate
	python3 ky.py habit


