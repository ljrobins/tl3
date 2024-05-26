.PHONY: all docs init build venv tle exec black pypi sphinx isort synthetic

sphinx:
	cd docs && sphinx-apidoc -o ./source ../twomillionlines -f && make html
	cp -R docs/build/html/ ../twomillionlines-docs
	touch ../twomillionlines-docs/.nojekyll

venv:
	python3 -m venv . --upgrade-deps
	. bin/activate
	pip3 install -r config/requirements.txt


rm-docs:
	rm -rf docs/source/gallery
	rm -rf docs/html
 
all: venv exec test
build: test black poetry
docs: sphinx
docs-clean: rm-docs docs