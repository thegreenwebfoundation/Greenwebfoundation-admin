.PHONY: release venv

# Create Python virtual environment if not yet created.
venv:
	test -d venv || python3 -m venv venv

## Installing
release:
	PIPENV_DOTENV_LOCATION=.env.prod pipenv run sentry-cli releases new -p admin-portal $(shell sentry-cli releases propose-version)
	PIPENV_DOTENV_LOCATION=.env.prod pipenv run sentry-cli releases set-commits --auto $(shell sentry-cli releases propose-version)
	PIPENV_DOTENV_LOCATION=.env.prod pipenv run ansible-playbook ansible/deploy.yml -i ansible/inventories/prod.yml
	PIPENV_DOTENV_LOCATION=.env.prod pipenv run sentry-cli releases finalize $(shell sentry-cli releases propose-version)


dev.test:
	pytest -s --create-db --looponfail --ds=greenweb.settings.testing

dev.test.only:
	pytest -s --create-db --looponfail -m only -v  --ds=greenweb.settings.testing

# Run a basic test(with pytest) that creates a database using the testing settings 
test:
	pytest -s --create-db --ds=greenweb.settings.testing

test.only:
	pytest -s --create-db -m only -v  --ds=greenweb.settings.testing

flake:
	flake8 ./greenweb ./apps ./*.py --count --statistics

black:
	black ./greenweb ./apps ./*.py $(ARGS)

black.check:
	@ARGS="--check --color --diff" make black

ci: | black.check flake

# Build the documentation using Sphinx
docs:
	sphinx-build ./docs _build/

# Build the documentation using Sphinx and keep updating it on every change
docs.watch:
	sphinx-autobuild ./docs _build/
