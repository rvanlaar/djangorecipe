# Makefile for testing on travis with multiple django versions
# See .travis.yml, it uses the DJANGO_VERSION environment variable.
# ^^^ TODO: not yet.

all: build

build:
	@echo Running bootstrap and buildout
	pip install -U setuptools
	# ^^^ This updates setuptools, necessary for bootstrap.
	python bootstrap.py
	bin/buildout

test:
	bin/test
