default: install

install:
	python3 setup.py install

rst:
	cat README.md | pandoc -f markdown -t rst > README.rst

upload: rst
	python3 setup.py sdist bdist_wheel
	twine upload dist/*

.PHONY: install rst upload
