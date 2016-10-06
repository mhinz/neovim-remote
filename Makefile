default: install

install:
	python3 setup.py install

upload:
	python3 setup.py sdist bdist_wheel
	twine upload dist/*

clean:
	rm -r build dist neovim_remote.egg-info

.PHONY: install upload
