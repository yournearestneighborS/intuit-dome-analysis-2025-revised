.PHONY: test data charts notebook analysis

test:
	python -m unittest discover -s tests -v

data:
	@test -n "$(WORKBOOK)" || (echo "Set WORKBOOK=/path/to/challenge-dataset.xlsx" && exit 1)
	python scripts/build_public_data.py --workbook "$(WORKBOOK)"

charts:
	python scripts/render_charts.py

notebook:
	python scripts/build_notebook.py

analysis: test charts notebook

