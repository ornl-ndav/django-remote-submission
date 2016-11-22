MAKEFLAGS += --warn-undefined-variables
SHELL := bash
.SHELLFLAGS := -eu -o pipefail -c
.DEFAULT_GOAL := all
.DELETE_ON_ERROR:
.SUFFIXES:

################
# Utilities

# Used for backups
date := $(shell date +%Y%m%d%H%M%S)

# Used for debugging
.PHONY: echo.%
echo.%:
	@echo $*=$($*)

# Used to make specific .env files
make-env = ./scripts/env.bash subst < $< > $@

# Used to load specific .env files
load-env = set -o allexport && unset $$(./scripts/env.bash variables) && source $< && set +o allexport

################
# Environment variables

ifndef PYTHON
PYTHON := python3
endif

################
# Sanity checks and local variables

ifndef VIRTUAL_ENV
$(error Not inside a virtual environment)
endif

################
# Exported variables

export DATE := $(date)

################
# Includes

################
# Standard targets

.PHONY: all
all: run

.PHONY: run
run:
	$(MAKE) -j 2 \
		run-server \
		run-celery

.PHONY: depend
depend: .depend.secondary

.PHONY: check
check:

.PHONY: clean
clean:
	find . -name '*~' -print -delete

################
# Application specific targets

.PHONY: run-server
run-server: .depend.secondary .migrate.secondary .loaddata.secondary
	$(PYTHON) manage.py runserver 8808

.PHONY: run-celery
run-celery: .depend.secondary .migrate.secondary
	$(PYTHON) -m celery -A server worker --loglevel=info

.PHONY: migrate
migrate: .migrate.secondary

.PHONY: createsuperuser
createsuperuser: .superuser.secondary

.PHONY: loaddata
loaddata: .loaddata.secondary

################
# Source transformations

.superuser.secondary: .migrate.secondary
	$(PYTHON) manage.py createsuperuser
	touch $@

.loaddata.secondary: $(wildcard fixtures/*.json) .migrate.secondary
	$(PYTHON) manage.py loaddata $(filter fixtures/%,$^)
	touch $@

.migrate.secondary: server/settings.py .depend.secondary
	$(PYTHON) manage.py makemigrations
	$(PYTHON) manage.py migrate
	touch $@

.depend.secondary: requirements.txt
	$(PYTHON) -m pip install -r requirements.txt
	touch $@

.env: .env.base
	touch $@
	cp $@ $@.$(date)
	./scripts/env.bash merge $@.$(date) $< > $@

.env.makefile: .env
	./scripts/env.bash to-makefile > $@
