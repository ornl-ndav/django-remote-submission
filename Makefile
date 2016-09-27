MAKEFLAGS += --warn-undefined-variables
SHELL := bash
.SHELLFLAGS := -eu -o pipefail -c
.DEFAULT_GOAL := all
.DELETE_ON_ERROR:
.SUFFIXES:

################
# Utilities

################
# Environment variables

################
# Exported variables

################
# Standard targets

.PHONY: all
all: run

.PHONY: run
run: .depend.secondary .migrate.secondary
	source venv/bin/activate && \
	python3 manage.py runserver 8008

.PHONY: depend
depend: .depend.secondary

.PHONY: check
check:

.PHONY: clean
clean:

################
# Application specific targets

.PHONY: migrate
migrate: .migrate.secondary

.PHONY: createsuperuser
createsuperuser:
	source venv/bin/activate && \
	python3 manage.py createsuperuser

################
# Source transformations

venv:
	python3 -m virtualenv $@

.SECONDARY: .depend.secondary
.depend.secondary: requirements.txt | venv
	source venv/bin/activate && \
	python -m pip install -r $< && \
	touch $@

.SECONDARY: .migrate.secondary
.migrate.secondary: .depend.secondary $(wildcard */models.py) \
                    server/settings.py
	source venv/bin/activate && \
	python manage.py makemigrations --no-input && \
	python manage.py migrate --no-input && \
	python manage.py collectstatic --no-input && \
	touch $@
