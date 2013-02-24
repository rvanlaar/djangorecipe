# Makefile mainly for testing on travis with both buildout 1.x and 2.x.
# See .travis.yml, it uses the BUILDOUT_VERSION environment variable.

all: build

build:
	@echo Running bootstrap and buildout
	python bootstrap.py
	bin/buildout

test:
	bin/test
