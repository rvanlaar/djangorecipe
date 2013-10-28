# Makefile for testing on travis with multiple django versions
# See .travis.yml, it uses the DJANGO_VERSION environment variable.

DJANGO_VERSION ?= 1.5

all: build

build:
	@echo Running bootstrap and buildout
	pip install -U setuptools
	# ^^^ This updates setuptools, necessary for bootstrap.
	python bootstrap.py
ifeq ($(DJANGO_VERSION),1.4)
	bin/buildout -c buildout14.cfg
endif
ifeq ($(DJANGO_VERSION),1.5)
	bin/buildout
endif
ifeq ($(DJANGO_VERSION),1.6)
	bin/buildout -c buildout16.cfg
endif

test:
	bin/test
