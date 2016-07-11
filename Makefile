upload:
	cat README.md | pandoc -f markdown -t rst > README.rst
	python3 setup.py sdist bdist_wheel
	twine upload dist/*
	rm README.rst
