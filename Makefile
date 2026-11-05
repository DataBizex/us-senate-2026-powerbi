PYTHON ?= python

.PHONY: help install validate validate-verbose

help:
	@echo "make install           install pandas and pytest"
	@echo "make validate          run every data-model check"
	@echo "make validate-verbose  same, listing each check"

install:
	$(PYTHON) -m pip install -r requirements-dev.txt

validate:
	$(PYTHON) -m pytest

validate-verbose:
	$(PYTHON) -m pytest -v
