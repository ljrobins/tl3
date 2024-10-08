.PHONY: all docs init build venv tle exec black pypi sphinx isort test format

sphinx:
	cd docs && sphinx-apidoc -o ./source ../tl3 -f && make html

venv:
	python3 -m venv . --upgrade-deps
	. bin/activate
	pip3 install -r config/requirements.txt

test:
	pytest zscratch/tests.py

format:
	isort .
	ruff check --fix
	ruff format

rm-docs:
	rm -rf docs/source/gallery
	rm -rf docs/html
 
all: venv exec test
build: test black poetry
docs: sphinx
docs-clean: rm-docs docs