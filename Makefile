# Makefile mainly for testing on travis with both buildout 1.x and 2.x.
# See .travis.yml, it uses the BUILDOUT_VERSION environment variable.

BUILDOUT_VERSION ?= 1

all: build

build:
	@echo Running bootstrap and buildout
ifeq ($(BUILDOUT_VERSION),1)
	python bootstrap.py
	bin/buildout
endif
ifeq ($(BUILDOUT_VERSION),2)
	python bootstrap2.py -t
	bin/buildout -c buildout2.cfg
endif

test:
	bin/test
