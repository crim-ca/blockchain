
# Included custom configs change the value of MAKEFILE_LIST
# Extract the required reference beforehand so we can use it for help target
MAKEFILE_NAME := $(word $(words $(MAKEFILE_LIST)),$(MAKEFILE_LIST))
# Include custom config if it is available
-include Makefile.config

# Application
APP_ROOT    := $(abspath $(lastword $(MAKEFILE_NAME))/..)
APP_NAME    := blockchain
APP_VERSION := 2.0.1
APP_DB_DIR  ?= /tmp/blockchain
APP_PORT    ?= 5000
APP_SECRET  ?= secret

# guess OS (Linux, Darwin,...)
OS_NAME  := $(shell uname -s 2>/dev/null || echo "unknown")
CPU_ARCH := $(shell uname -m 2>/dev/null || uname -p 2>/dev/null || echo "unknown")
SHELL    := bash

# conda
CONDA_ENV_NAME ?= $(APP_NAME)
CONDA_HOME     ?= $(HOME)/.conda
CONDA_ENVS_DIR ?= $(CONDA_HOME)/envs
CONDA_ENV_PATH := $(CONDA_ENVS_DIR)/$(CONDA_ENV_NAME)
# allow pre-installed conda in Windows bash-like shell
ifeq ($(findstring MINGW,$(OS_NAME)),MINGW)
  CONDA_BIN_DIR ?= $(CONDA_HOME)/Scripts
else
  CONDA_BIN_DIR ?= $(CONDA_HOME)/bin
endif
CONDA_BIN := $(CONDA_BIN_DIR)/conda
CONDA_ENV_REAL_TARGET_PATH := $(realpath $(CONDA_ENV_PATH))
CONDA_ENV_REAL_ACTIVE_PATH := $(realpath ${CONDA_PREFIX})

# environment already active - use it directly
ifneq ("$(CONDA_ENV_REAL_ACTIVE_PATH)", "")
  CONDA_ENV_MODE := [using active environment]
  CONDA_ENV_NAME := $(notdir $(CONDA_ENV_REAL_ACTIVE_PATH))
  CONDA_CMD :=
endif
# environment not active but it exists - activate and use it
ifneq ($(CONDA_ENV_REAL_TARGET_PATH), "")
  CONDA_ENV_NAME := $(notdir $(CONDA_ENV_REAL_TARGET_PATH))
endif
# environment not active and not found - create, activate and use it
ifeq ("$(CONDA_ENV_NAME)", "")
  CONDA_ENV_NAME := $(APP_NAME)
endif
# update paths for environment activation
ifeq ("$(CONDA_ENV_REAL_ACTIVE_PATH)", "")
  CONDA_ENV_MODE := [will activate environment]
  CONDA_CMD := source "$(CONDA_BIN_DIR)/activate" "$(CONDA_ENV_NAME)";
endif
# override conda command as desired
CONDA_COMMAND ?= undefined
CONDA_SETUP := 1
ifneq ("$(CONDA_COMMAND)","undefined")
  CONDA_SETUP := 0
  CONDA_ENV_MODE := [using overridden command]
  CONDA_CMD := $(CONDA_COMMAND)
endif

DOWNLOAD_CACHE ?= $(APP_ROOT)/downloads
REPORTS_DIR ?= $(APP_ROOT)/reports
PYTHON_VERSION ?= `python -c 'import platform; print(platform.python_version())'`
PIP_XARGS ?=
PIP_USE_FEATURE := `python -c '\
	import pip; \
	from distutils.version import LooseVersion; \
	print(LooseVersion(pip.__version__) < LooseVersion("21.0"))'`
ifeq ($(findstring "--use-feature=2020-resolver", "$(PIP_XARGS)"),)
  # feature not specified, but needed
  ifeq ("$(PIP_USE_FEATURE)", "True")
    PIP_XARGS := --use-feature=2020-resolver $(PIP_XARGS)
  endif
else
  # feature was specified, but should not (not required anymore, default behavior)
  ifeq ("$(PIP_USE_FEATURE)", "True")
    PIP_XARGS := $(subst "--use-feature=2020-resolver",,"$(PIP_XARGS)")
  endif
endif

# choose conda installer depending on your OS
CONDA_URL = https://repo.continuum.io/miniconda
ifeq ("$(OS_NAME)", "Linux")
  FN := Miniconda3-latest-Linux-x86_64.sh
else ifeq ("$(OS_NAME)", "Darwin")
  FN := Miniconda3-latest-MacOSX-x86_64.sh
else
  FN := unknown
endif

# docker
APP_DOCKER_REPO := blockchain
APP_DOCKER_TAG  := $(APP_DOCKER_REPO):$(APP_VERSION)
APP_LATEST_TAG  := $(APP_DOCKER_REPO):latest

.DEFAULT_GOAL := help

## --- Informative targets --- ##

.PHONY: all
all: help

# Auto documented help targets & sections from comments
#	- detects lines marked by double octothorpe (#), then applies the corresponding target/section markup
#   - target comments must be defined after their dependencies (if any)
#	- section comments must have at least a double dash (-)
#
# 	Original Reference:
#		https://marmelab.com/blog/2016/02/29/auto-documented-makefile.html
# 	Formats:
#		https://misc.flogisoft.com/bash/tip_colors_and_formatting
_SECTION := \033[34m
_TARGET  := \033[36m
_NORMAL  := \033[0m
_SPACING := 24
.PHONY: help
# note: use "\#\#" to escape results that would self-match in this target's search definition
help:	## print this help message (default)
	@echo "$(_SECTION)=== $(APP_NAME) help ===$(_NORMAL)"
	@echo "Please use 'make <target>' where <target> is one of:"
#	@grep -E '^[a-zA-Z_-]+:.*?\#\# .*$$' $(MAKEFILE_LIST) \
#		| awk 'BEGIN {FS = ":.*?\#\# "}; {printf "    $(_TARGET)%-24s$(_NORMAL) %s\n", $$1, $$2}'
	@grep -E '\#\#.*$$' "$(APP_ROOT)/$(MAKEFILE_NAME)" \
		| awk ' BEGIN {FS = "(:|\-\-\-)+.*?\#\# "}; \
			/\--/ 		{printf "$(_SECTION)%s$(_NORMAL)\n", $$1;} \
			/:/   		{printf "   $(_TARGET)%-$(_SPACING)s$(_NORMAL) %s\n", $$1, $$2;} \
			/\-only:/   {gsub(/-only/, "", $$1); \
						 printf "   $(_TARGET)%-$(_SPACING)s$(_NORMAL) %s (preinstall dependencies)\n", $$1, $$2;} \
		'

.PHONY: version
version:	## display current version
	@-echo "$(APP_NAME) version: $(APP_VERSION)"

.PHONY: info
info:		## display make information
	@echo "Information about your make execution:"
	@echo "  OS Name                $(OS_NAME)"
	@echo "  CPU Architecture       $(CPU_ARCH)"
	@echo "  Conda Home             $(CONDA_HOME)"
	@echo "  Conda Prefix           $(CONDA_ENV_PATH)"
	@echo "  Conda Env Name         $(CONDA_ENV_NAME)"
	@echo "  Conda Env Path         $(CONDA_ENV_REAL_ACTIVE_PATH)"
	@echo "  Conda Binary           $(CONDA_BIN)"
	@echo "  Conda Activation       $(CONDA_ENV_MODE)"
	@echo "  Conda Command          $(CONDA_CMD)"
	@echo "  Application Root       $(APP_ROOT)"
	@echo "  Application Name       $(APP_NAME)"
	@echo "  Application Version    $(APP_VERSION)"
	@echo "  Download Cache         $(DOWNLOAD_CACHE)"
	@echo "  Test Reports           $(REPORTS_DIR)"
	@echo "  Docker Tag             $(APP_DOCKER_TAG)"

## --- Cleanup targets --- ##

.PHONY: clean
clean: clean-all	## alias for 'clean-all' target

.PHONY: clean-all
clean-all: clean-build clean-pyc clean-test clean-docs	## remove all artifacts

.PHONY: clean-build
clean-build:	## remove build artifacts
	@echo "Cleaning build artifacts..."
	@-rm -fr build/
	@-rm -fr dist/
	@-rm -fr downloads/
	@-rm -fr .eggs/
	@find . -type d -name '*.egg-info' -exec rm -fr {} +
	@find . -type f -name '*.egg' -exec rm -f {} +

# rm without quotes important below to allow regex
.PHONY: clean-docs
clean-docs:		## remove doc artifacts
	@echo "Cleaning doc artifacts..."
	@-find "$(APP_ROOT)/docs/" -type f -name "$(APP_NAME)*.rst" -delete
	@-rm -f "$(APP_ROOT)/docs/modules.rst"
	@-rm -f "$(APP_ROOT)/docs/api.json"
	@-rm -rf "$(APP_ROOT)/docs/autoapi"
	@-rm -rf "$(APP_ROOT)/docs/_build"

.PHONY: clean-pyc
clean-pyc:		## remove Python file artifacts
	@echo "Cleaning Python artifacts..."
	@find . -type f -name '*.pyc' -exec rm -f {} +
	@find . -type f -name '*.pyo' -exec rm -f {} +
	@find . -type f -name '*~' -exec rm -f {} +
	@find . -type f -name '__pycache__' -exec rm -fr {} +

.PHONY: clean-test
clean-test:		## remove test and coverage artifacts
	@echo "Cleaning tests artifacts..."
	@-rm -fr .tox/
	@-rm -fr .pytest_cache/
	@-rm -f .coverage*
	@-rm -f coverage.*
	@-rm -fr "$(APP_ROOT)/coverage/"
	@-rm -fr "$(REPORTS_DIR)"

.PHONY: clean-docker
clean-docker: docker-clean	## alias for 'docker-clean' target

## --- Documentation targets --- ##

DOCS_DIR 		:= $(APP_ROOT)/docs
DOCS_BUILD_DIR 	:= $(DOCS_DIR)/_build
DOCS_SCHEMA_DIR := $(DOCS_DIR)/schemas
DOCS_LOCATION 	:= $(DOCS_BUILD_DIR)/html/index.html

$(DOCS_LOCATION):
	@echo "Building docs..."
	@bash -c '$(CONDA_CMD) \
		sphinx-apidoc -o "$(APP_ROOT)/docs/" "$(APP_ROOT)/$(APP_NAME)"; \
		"$(MAKE)" -C "$(APP_ROOT)/docs" html;'
	@-echo "Documentation available: file://$(DOCS_LOCATION)"

.PHONY: _force_docs
_force_docs:
	@-rm -f "$(DOCS_LOCATION)"

DOCS := openapi toc
DOCS := $(addprefix docs-, $(DOCS))
DOCS_BUILD := $(DOCS_LOCATION) _force_docs
DOCS_OPENAPI_TAG ?= $(APP_VERSION)
DOCS_OPENAPI_DEST ?= schema

$(DOCS): docs-%: install-dev docs-%-only

# use tmp dir to avoid losing the original schema if formatted destination is the source file and error occurs
.PHONY: docs-openapi-format
docs-openapi-format:
	@-echo "Generating latest OpenAPI documentation [$(DOCS_SCHEMA_DIR)/$(DOCS_OPENAPI_DEST).json]..."
	@$(eval DOC_TMP_DIR := $(shell mktemp -d))
	@bash -c "$(CONDA_CMD) \
		python -c '\
import json; \
print(json.dumps(json.load(open(\"$(DOCS_SCHEMA_DIR)/openapi-$(DOCS_OPENAPI_TAG).json\")), indent=4))' \
	" > "$(DOC_TMP_DIR)/$(DOCS_OPENAPI_DEST).json"
	@mv "$(DOC_TMP_DIR)/$(DOCS_OPENAPI_DEST).json" "$(DOCS_SCHEMA_DIR)/$(DOCS_OPENAPI_DEST).json"
	@-rm -fr $(DOC_TMP_DIR)

.PHONY: docs-openapi-current
docs-openapi-current:  ## applies the current version OpenAPI schema as the latest schema reference for Postman
	@$(MAKE) -C "$(APP_ROOT)" \
		DOCS_OPENAPI_TAG=$(DOCS_OPENAPI_TAG) \
		DOCS_OPENAPI_DEST=schema \
		docs-openapi-format

.PHONY: docs-openapi-dev
docs-openapi-dev: install-pkg  ## applies the current code OpenAPI schema as the development schema reference for Postman
	@$(MAKE) -C "$(APP_ROOT)" \
		DOCS_OPENAPI_TAG=dev \
		DOCS_OPENAPI_DEST=openapi-$(APP_VERSION)-dev \
		docs-openapi-only docs-openapi-format
	@-rm "$(DOCS_SCHEMA_DIR)/openapi-dev.json"

# must install package to apply new version as necessary to be reflected in generated OpenAPI
.PHONY: docs-openapi-only
docs-openapi-only:
	@-echo "Building OpenAPI schema documentation"
	@$(MAKE) -C "$(APP_ROOT)" start-app
	@mkdir -p "$(DOCS_SCHEMA_DIR)"
	@curl --silent -H "Accept: application/json" "http://0.0.0.0:$(APP_PORT)/json" \
		> "$(DOCS_SCHEMA_DIR)/openapi-$(DOCS_OPENAPI_TAG).json"
	@$(MAKE) -C "$(APP_ROOT)" \
		DOCS_OPENAPI_TAG=$(DOCS_OPENAPI_TAG) \
		DOCS_OPENAPI_DEST=openapi-$(DOCS_OPENAPI_TAG) \
		docs-openapi-format
	@$(MAKE) -C "$(APP_ROOT)" \
		DOCS_OPENAPI_TAG=$(DOCS_OPENAPI_TAG) \
		docs-openapi-current
	@$(MAKE) -C "$(APP_ROOT)" stop

.PHONY: docs-openapi
docs-openapi: install-pkg docs-openapi-only

.PHONY: docs-toc-only
docs-toc-only:
	@-echo "Updating markdown TOC in README..."
	@npx markdown-toc -i "$(APP_ROOT)/README.md"

.PHONY: docs-toc
docs-toc: install-npm-markdown-doc docs-toc-only  ## generate markdown TOC automatically

.PHONY: docs-only
docs-only: $(addsuffix -only, $(DOCS)) $(DOCS_BUILD)	## generate documentation without requirements installation or cleanup

# NOTE: we need almost all base dependencies because package needs to be parsed to generate OpenAPI
.PHONY: docs
docs: install-docs install-pkg clean-docs docs-only		## generate Sphinx HTML documentation, including API docs

.PHONY: docs-show
docs-show: $(DOCS_LOCATION)	## display HTML webpage of generated documentation (build docs if missing)
	@-test -f "$(DOCS_LOCATION)" || $(MAKE) -C "$(APP_ROOT)" docs
	$(BROWSER) "$(DOCS_LOCATION)"

## --- Versioning targets --- ##

# Bumpversion 'dry' config
# if 'dry' is specified as target, any bumpversion call using 'BUMP_XARGS' will not apply changes
BUMP_XARGS ?= --verbose --allow-dirty
BUMP_DRY := 0
ifeq ($(filter dry, $(MAKECMDGOALS)), dry)
	BUMP_XARGS := $(BUMP_XARGS) --dry-run
	BUMP_DRY := 1
endif

.PHONY: dry
dry: setup.cfg	## run 'bump' target without applying changes (dry-run)
ifeq ($(findstring bump, $(MAKECMDGOALS)),)
	$(error Target 'dry' must be combined with a 'bump' target)
endif

.PHONY: bump
bump:	## bump version using VERSION specified as user input (make VERSION=<X.Y.Z> bump)
	@-echo "Updating package version ..."
	@[ "${VERSION}" ] || ( echo ">> 'VERSION' is not set"; exit 1 )
	@-bash -c '$(CONDA_CMD) test -f "$(CONDA_ENV_PATH)/bin/bump2version" || pip install $(PIP_XARGS) bump2version'
	@-bash -c '$(CONDA_CMD) bump2version $(BUMP_XARGS) --new-version "${VERSION}" patch;'
	@[ ${BUMP_DRY} -ne 1 ] && ( \
		$(MAKE) -C "$(APP_ROOT)" DOCS_OPENAPI_TAG="${VERSION}" docs-openapi && \
		git add "$(DOCS_SCHEMA_DIR)/openapi-${VERSION}.json" "$(DOCS_SCHEMA_DIR)/schema.json" && \
		git commit --amend --no-edit && \
		git tag -f "${VERSION}" \
	) || echo "Would generate OpenAPI schema [$(DOCS_SCHEMA_DIR)/openapi-${VERSION}.json]";

## --- Installation targets --- ##

.PHONY: dist
dist: clean conda-env	## package for distribution
	@echo "Creating distribution..."
	@bash -c '$(CONDA_CMD) python setup.py sdist'
	@bash -c '$(CONDA_CMD) python setup.py bdist_wheel'
	ls -l dist

.PHONY: install
install: install-all	## alias for 'install-all' target

.PHONY: install-all
install-all: install-pkg install-dev install-docs	## install every dependency and package definition

.PHONY: install-pkg
install-pkg: 	## install the package to the active Python's site-packages
	@echo "Installing package..."
	@bash -c '$(CONDA_CMD) python setup.py install_egg_info'
	@bash -c '$(CONDA_CMD) pip install $(PIP_XARGS) --upgrade -e "$(APP_ROOT)" --no-cache'

.PHONY: install-req
install-req: conda-env	 ## install package base requirements without installing main package
	@bash -c '$(CONDA_CMD) pip install $(PIP_XARGS) -r "$(APP_ROOT)/requirements.txt"'
	@echo "Successfully installed base requirements."

.PHONY: install-docs
install-docs: conda-env  ## install package requirements for documentation generation
	@(test -f "$(APP_ROOT)/requirements-doc.txt" && \
	  bash -c '$(CONDA_CMD) pip install $(PIP_XARGS) -r "$(APP_ROOT)/requirements-doc.txt"' && \
	  echo "Successfully installed dev requirements." \
	 ) || echo "No doc requirements to install."

.PHONY: install-dev
install-dev: conda-env	## install package requirements for development and testing
	@(test -f "$(APP_ROOT)/requirements-dev.txt" && \
	  bash -c '$(CONDA_CMD) pip install $(PIP_XARGS) -r "$(APP_ROOT)/requirements-dev.txt"' && \
	  echo "Successfully installed dev requirements." \
	 ) || echo "No dev requirements to install."

# install locally to ensure they can be found by config extending them
.PHONY: install-npm
install-npm:    		## install npm package manager if it cannot be found
	@[ -f "$(shell which npm)" ] || ( \
		echo "Binary package manager npm not found. Attempting to install it."; \
		apt-get install npm \
	)

.PHONY: install-npm-stylelint
install-npm-stylelint: install-npm 	## install stylelint checker using npm
	@[ `npm ls -only dev -depth 0 2>/dev/null | grep -V "UNMET" | grep stylelint-config-standard | wc -l` = 1 ] || ( \
		echo "Install required libraries for style checks." && \
		npm install stylelint@13.13.1 stylelint-config-standard@22.0.0 --save-dev \
	)

.PHONY: install-npm-markdown-doc
install-npm-markdown-doc: install-npm 	## install markdown-doc TOC generator using npm
	@[ `npm ls -only dev -depth 0 2>/dev/null | grep -V "UNMET" | grep markdown-doc | wc -l` = 1 ] || ( \
		echo "Install required libraries for docs generation." && \
		npm install markdown-doc --save-dev \
	)

## --- Launchers targets --- ##

.PHONY: start
start: install start-app  ## start application instance with gunicorn after installation of dependencies

.PHONY: start-app
start-app: stop		## start application instance with single worker
	@echo "Starting $(APP_NAME)..."
	@mkdir -p "$(APP_DB_DIR)"
	@test -d "$(APP_DB_DIR)" || '$(CONDA_CMD) python "$(APP_ROOT)/blockchain/app.py --new --db "$(APP_DB_DIR)"'
	@bash -c '$(CONDA_CMD) \
		python "$(APP_ROOT)/blockchain/app.py" \
			--secret $(APP_SECRET) \
			--port $(APP_PORT) \
			--db "$(APP_DB_DIR)" &'
	@sleep 5
	@curl --silent -H "Accept: application/json" "http://0.0.0.0:$(APP_PORT)" 2>&1 | grep "Blockchain Node"

.PHONY: stop
stop: 		## kill application instance(s) started with gunicorn
	@(lsof -t -i :$(APP_PORT) | xargs kill) 2>/dev/null || echo "No $(APP_NAME) process to stop"

.PHONY: stat
stat: 		## display processes with PID(s) of gunicorn instance(s) running the application
	@lsof -i :$(APP_PORT) || echo "No instance running"

## --- Docker targets --- ##

.PHONY: docker-info
docker-info:	## tag version of docker image for build/push
	@echo "Image will be built as:"
	@echo "$(APP_DOCKER_TAG)"

.PHONY: docker-build
docker-build: ## build docker image
	docker build "$(APP_ROOT)" -t "$(APP_LATEST_TAG)"
	docker tag "$(APP_LATEST_TAG)" "$(APP_DOCKER_TAG)"

.PHONY: docker-clean
docker-clean: 	## remove any leftover images from docker target operations
	docker rmi $(docker images -f "reference=$(APP_DOCKER_REPO)" -q)
	docker-compose $(DOCKER_TEST_COMPOSES) down

## --- Static code check targets ---

.PHONY: mkdir-reports
mkdir-reports:
	@mkdir -p "$(REPORTS_DIR)"

# autogen check variants with pre-install of dependencies using the '-only' target references
CHECKS := pep8 lint security doc8 links imports css
CHECKS := $(addprefix check-, $(CHECKS))

$(CHECKS): check-%: install-dev check-%-only

.PHONY: check
check: check-all  ## alias for 'check-all' target

.PHONY: check-only
check-only: $(addsuffix -only, $(CHECKS))

.PHONY: check-all
check-all: install-dev $(CHECKS)  ## run all code checks

.PHONY: check-pep8-only
check-pep8-only: mkdir-reports		## run PEP8 code style checks
	@echo "Running PEP8 code style checks..."
	@-rm -fr "$(REPORTS_DIR)/check-pep8.txt"
	@bash -c '$(CONDA_CMD) \
		flake8 --config="$(APP_ROOT)/setup.cfg" --output-file="$(REPORTS_DIR)/check-pep8.txt" --tee'

.PHONY: check-lint-only
check-lint-only: mkdir-reports		## run linting code style checks
	@echo "Running linting code style checks..."
	@-rm -fr "$(REPORTS_DIR)/check-lint.txt"
	@bash -c '$(CONDA_CMD) \
		pylint \
			--load-plugins pylint_quotes \
			--rcfile="$(APP_ROOT)/.pylintrc" \
			--reports y \
			"$(APP_ROOT)/$(APP_NAME)" "$(APP_ROOT)/docs" "$(APP_ROOT)/tests" \
		1> >(tee "$(REPORTS_DIR)/check-lint.txt")'

.PHONY: check-security-only
check-security-only: mkdir-reports	## run security code checks
	@echo "Running security code checks..."
	@-rm -fr "$(REPORTS_DIR)/check-security.txt"
	@bash -c '$(CONDA_CMD) \
		bandit -v --ini "$(APP_ROOT)/setup.cfg" -r \
		1> >(tee "$(REPORTS_DIR)/check-security.txt")'

.PHONY: check-docs-only
check-docs-only: check-doc8-only check-docf-only	## run every code documentation checks

.PHONY: check-doc8-only
check-doc8-only: mkdir-reports		## run PEP8 documentation style checks
	@echo "Running PEP8 doc style checks..."
	@-rm -fr "$(REPORTS_DIR)/check-doc8.txt"
	@bash -c '$(CONDA_CMD) \
		doc8 --config "$(APP_ROOT)/setup.cfg" "$(APP_ROOT)/docs" \
		1> >(tee "$(REPORTS_DIR)/check-doc8.txt")'

# FIXME: move parameters to setup.cfg when implemented (https://github.com/myint/docformatter/issues/10)
# NOTE: docformatter only reports files with errors on stderr, redirect trace stderr & stdout to file with tee
# NOTE:
#	Don't employ '--wrap-descriptions 120' since they *enforce* that length and rearranges format if any word can fit
#	within remaining space, which often cause big diffs of ugly formatting for no important reason. Instead only check
#	general formatting operations, and let other linter capture docstrings going over 120 (what we really care about).
.PHONY: check-docf-only
check-docf-only: mkdir-reports	## run PEP8 code documentation format checks
	@echo "Checking PEP8 doc formatting problems..."
	@-rm -fr "$(REPORTS_DIR)/check-docf.txt"
	@bash -c '$(CONDA_CMD) \
		docformatter \
			--pre-summary-newline \
			--wrap-descriptions 0 \
			--wrap-summaries 120 \
			--make-summary-multi-line \
			--check \
			--recursive \
			"$(APP_ROOT)" \
		1>&2 2> >(tee "$(REPORTS_DIR)/check-docf.txt")'

.PHONY: check-links-only
check-links-only: mkdir-reports		## check all external links in documentation for integrity
	@echo "Running link checks on docs..."
	@bash -c '$(CONDA_CMD) $(MAKE) -C "$(APP_ROOT)/docs" linkcheck'

.PHONY: check-imports-only
check-imports-only: mkdir-reports	## run imports code checks
	@echo "Running import checks..."
	@-rm -fr "$(REPORTS_DIR)/check-imports.txt"
	@bash -c '$(CONDA_CMD) \
	 	isort --check-only --diff --recursive $(APP_ROOT) \
		1> >(tee "$(REPORTS_DIR)/check-imports.txt")'

.PHONY: check-css-only
check-css-only: mkdir-reports install-npm
	@echo "Running CSS style checks..."
	@npx stylelint \
		--config "$(APP_ROOT)/.stylelintrc.json" \
		--output-file "$(REPORTS_DIR)/fixed-css.txt" \
		"$(APP_ROOT)/**/*.css"

# autogen fix variants with pre-install of dependencies using the '-only' target references
FIXES := imports lint docf
FIXES := $(addprefix fix-, $(FIXES))

$(FIXES): fix-%: install-dev fix-%-only

.PHONY: fix
fix: fix-all 	## alias for 'fix-all' target

.PHONY: fix-only
fix-only: $(addsuffix -only, $(FIXES))

.PHONY: fix-all
fix-all: install-dev $(FIXES)  ## fix all code check problems automatically

.PHONY: fix-imports-only
fix-imports-only: 	## fix import code checks corrections automatically
	@echo "Fixing flagged import checks..."
	@-rm -fr "$(REPORTS_DIR)/fixed-imports.txt"
	@bash -c '$(CONDA_CMD) \
		isort --recursive $(APP_ROOT) \
		1> >(tee "$(REPORTS_DIR)/fixed-imports.txt")'

.PHONY: fix-lint-only
fix-lint-only: mkdir-reports	## fix some PEP8 code style problems automatically
	@echo "Fixing PEP8 code style problems..."
	@-rm -fr "$(REPORTS_DIR)/fixed-lint.txt"
	@bash -c '$(CONDA_CMD) \
		autopep8 -v -j 0 -i -r $(APP_ROOT) \
		1> >(tee "$(REPORTS_DIR)/fixed-lint.txt")'

# FIXME: move parameters to setup.cfg when implemented (https://github.com/myint/docformatter/issues/10)
.PHONY: fix-docf-only
fix-docf-only: mkdir-reports	## fix some PEP8 code documentation style problems automatically
	@echo "Fixing PEP8 code documentation problems..."
	@-rm -fr "$(REPORTS_DIR)/fixed-docf.txt"
	@bash -c '$(CONDA_CMD) \
		docformatter \
			--pre-summary-newline \
			--wrap-descriptions 0 \
			--wrap-summaries 120 \
			--make-summary-multi-line \
			--in-place \
			--recursive \
			$(APP_ROOT) \
		1> >(tee "$(REPORTS_DIR)/fixed-docf.txt")'

## --- Test targets --- ##


# -v:  list of test names with PASS/FAIL/SKIP/ERROR/etc. next to it
# -vv: extended collection of stdout/stderr on top of test results
TEST_VERBOSITY ?= -vv

# autogen tests variants with pre-install of dependencies using the '-only' target references
TESTS := custom
TESTS := $(addprefix test-, $(TESTS))

$(TESTS): test-%: install install-dev test-%-only

.PHONY: test
test: clean-test test-all   ## alias for 'test-all' target

.PHONY: test-all
test-all: install install-dev test-only  ## run all tests (including long running tests)

.PHONY: test-only
test-only: mkdir-reports		 ## run all tests combinations without pre-installation of dependencies
	@echo "Running tests..."
	@bash -c '$(CONDA_CMD) pytest tests $(TEST_VERBOSITY) --junitxml "$(APP_ROOT)/tests/results.xml"'

.PHONY: test-custom-only
test-custom-only:		## run custom marker tests using SPEC="<marker-specification>"
	@echo "Running custom tests..."
	@[ "${SPEC}" ] || ( echo ">> 'TESTS' is not set"; exit 1 )
	@bash -c '$(CONDA_CMD) pytest tests $(TEST_VERBOSITY) -m "${SPEC}" --junitxml "$(APP_ROOT)/tests/results.xml"'

# coverage file location cannot be changed
COVERAGE_FILE     := $(APP_ROOT)/.coverage
COVERAGE_HTML_DIR := $(REPORTS_DIR)/coverage
COVERAGE_HTML_IDX := $(COVERAGE_HTML_DIR)/index.html
$(COVERAGE_FILE): install-dev
	@echo "Running coverage analysis..."
	@bash -c '$(CONDA_CMD) coverage run --source "$(APP_ROOT)/$(APP_NAME)" \
		`which pytest` tests -m "not remote" || true'
	@bash -c '$(CONDA_CMD) coverage xml -i -o "$(REPORTS_DIR)/coverage.xml"'
	@bash -c '$(CONDA_CMD) coverage report -m'
	@bash -c '$(CONDA_CMD) coverage html -d "$(COVERAGE_HTML_DIR)"'
	@-echo "Coverage report available: file://$(COVERAGE_HTML_IDX)"

.PHONY: coverage-only
coverage-only: $(COVERAGE_FILE)

.PHONY: coverage
coverage: install-dev install coverage-only		## check code coverage and generate an analysis report

.PHONY: coverage-show
coverage-show: $(COVERAGE_HTML_IDX)		## display HTML webpage of generated coverage report (run coverage if missing)
	@-test -f "$(COVERAGE_HTML_IDX)" || $(MAKE) -C "$(APP_ROOT)" coverage
	$(BROWSER) "$(COVERAGE_HTML_IDX)"

## --- Conda setup targets --- ##

.PHONY: conda-base
conda-base:	 ## obtain a base distribution of conda if missing and required
	@[ $(CONDA_SETUP) -eq 0 ] && echo "Conda setup disabled." || ( ( \
		test -f "$(CONDA_HOME)/bin/conda" || test -d "$(DOWNLOAD_CACHE)" || ( \
			echo "Creating download directory: $(DOWNLOAD_CACHE)" && \
			mkdir -p "$(DOWNLOAD_CACHE)") ) ; ( \
		test -f "$(CONDA_HOME)/bin/conda" || \
		test -f "$(DOWNLOAD_CACHE)/$(FN)" || ( \
			echo "Fetching conda distribution from: $(CONDA_URL)/$(FN)" && \
		 	curl "$(CONDA_URL)/$(FN)" --insecure --location --output "$(DOWNLOAD_CACHE)/$(FN)") ) ; ( \
		test -f "$(CONDA_HOME)/bin/conda" || ( \
		  	bash "$(DOWNLOAD_CACHE)/$(FN)" -b -u -p "$(CONDA_HOME)" && \
		 	echo "Make sure to add '$(CONDA_HOME)/bin' to your PATH variable in '~/.bashrc'.") ) \
	)

.PHONY: conda-cfg
conda_config: conda-base	## update conda package configuration
	@echo "Updating conda configuration..."
	@"$(CONDA_HOME)/bin/conda" config --set ssl_verify true
	@"$(CONDA_HOME)/bin/conda" config --set use_pip true
	@"$(CONDA_HOME)/bin/conda" config --set channel_priority true
	@"$(CONDA_HOME)/bin/conda" config --set auto_update_conda false
	@"$(CONDA_HOME)/bin/conda" config --add channels defaults

# the conda-env target's dependency on conda-cfg above was removed, will add back later if needed

.PHONY: conda-env
conda-env: conda-base	## create conda environment if missing and required
	@[ $(CONDA_SETUP) -eq 0 ] || ( \
		test -d "$(CONDA_ENV_PATH)" || ( \
			echo "Creating conda environment at '$(CONDA_ENV_PATH)'..." && \
		 	"$(CONDA_HOME)/bin/conda" create -y -n "$(CONDA_ENV_NAME)" python=$(PYTHON_VERSION)) \
		)


# vi: tabstop=4 expandtab shiftwidth=2 softtabstop=2

