PY?=poetry run python
PELICAN?=poetry run pelican
PELICANOPTS=

BASEDIR=$(CURDIR)
INPUTDIR=$(BASEDIR)/content
OUTPUTDIR=$(BASEDIR)/docs
CONFFILE=$(BASEDIR)/pelicanconf.py
PUBLISHCONF=$(BASEDIR)/publishconf.py

LOCAL_SITEURL=http://127.0.0.1:8000
GITHUB_PAGES_SITEURL=https://rakhmaevao.github.io/yanashbelyak

GITHUB_PAGES_BRANCH=gh-pages


DEBUG ?= 0
ifeq ($(DEBUG), 1)
	PELICANOPTS += -D
endif

RELATIVE ?= 0
ifeq ($(RELATIVE), 1)
	PELICANOPTS += --relative-urls
endif

SERVER ?= "0.0.0.0"

PORT ?= 0
ifneq ($(PORT), 0)
	PELICANOPTS += -p $(PORT)
endif


help:
	@echo 'Makefile for a pelican Web site                                           '
	@echo '                                                                          '
	@echo 'Usage:                                                                    '
	@echo '   make clean                          remove the generated files         '
	@echo '   make publish                        generate using production settings '
	@echo '   make devserver                      serve and regenerate together      '
	@echo '   make github                         upload the web site via gh-pages   '
	@echo '   make local_content                  generate content for local site    '
	@echo '   make format                         format code                        '
	@echo '                                                                          '

clean:
	[ ! -d "$(OUTPUTDIR)" ] || rm -rf "$(OUTPUTDIR)"
	rm -f content/persons/*
	rm -f content/images/tree.svg

devserver:
	SITEURL=$(LOCAL_SITEURL) $(PELICAN) -t theme -lr "$(INPUTDIR)" -o "$(OUTPUTDIR)" -s "$(CONFFILE)" $(PELICANOPTS)

publish:
	SITEURL=$(GITHUB_PAGES_SITEURL) $(PY) content_generator/content_generator.py
	SITEURL=$(GITHUB_PAGES_SITEURL) $(PELICAN) -t theme "$(INPUTDIR)" -o "$(OUTPUTDIR)" -s "$(PUBLISHCONF)" $(PELICANOPTS)

github: publish
	poetry run ghp-import -m "Generate Pelican site" -b $(GITHUB_PAGES_BRANCH) "$(OUTPUTDIR)"
	git push origin $(GITHUB_PAGES_BRANCH)

local_content:
	SITEURL=$(LOCAL_SITEURL) $(PY) content_generator/main.py
	SITEURL=$(LOCAL_SITEURL) $(PELICAN) content -t theme

py_format:
	poetry run ruff format content_generator pelicanconf.py tasks.py publishconf.py publishconf.py
	poetry run ruff --fix content_generator/src pelicanconf.py tasks.py publishconf.py publishconf.py

all_format: py_format
	npx prettier --write README.md
	npx prettier --write content

lint:
	@echo "Линтинг"
	poetry run ruff content_generator pelicanconf.py tasks.py publishconf.py publishconf.py

pytest:
	cd content_generator && poetry run pytest -vv -s --disable-warnings tests -k "test_many_womans"

.PHONY: help clean devserver publish github local_content, dfg
