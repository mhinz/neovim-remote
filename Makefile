default: install

install:
	python3 setup.py install

upload:
	python3 setup.py sdist bdist_wheel
	twine upload dist/*

.PHONY: install upload
