default: install

install:
	python3 setup.py install

upload: clean
	python3 setup.py sdist bdist_wheel
	twine upload dist/*

clean:
	rm -rf build dist neovim_remote.egg-info

.PHONY: install upload
