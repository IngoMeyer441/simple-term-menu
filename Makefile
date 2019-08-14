upload: clean
	@[ "$$(git symbolic-ref -q HEAD)" = "refs/heads/master" ] || \
		{ echo "Uploading can only be done on the master branch."; exit 1; }
	python3 setup.py sdist && \
	python3 setup.py bdist_wheel && \
	twine upload dist/*

clean:
	rm -rf build dist *.egg-info

.PHONY: clean upload
