SHELL := /bin/bash

# phony targets
.PHONY: all uv git test coverage

all:
	$(MAKE) uv
	$(MAKE) git
	if command -v code > /dev/null; then code . ; fi
	$(MAKE) remotegit

uv:
	uv python install 3.12
	uv sync
	uv tool install isort
	uv tool install pre-commit
	uv tool install pytest
	uv tool install pyclean

git:
	git init
	git lfs install
	git add .
	uvx pre-commit run --all-files
	git commit -am "First commit after initializing the project."

remotegit:
	git branch -M main
	git remote add origin git@github.com:thomascamminady/my_project.git || true
	git push -u origin main || echo "Warning: Remote repository not linked. Please create it on GitHub and try again."


test:
	uvx pytest .

coverage:
	uvx pytest --cov=cammpweek2025 tests/


preprocess:
	uv run python src/cammpweek2025/preprocess_data.py

plotmap:
	uv run python src/cammpweek2025/plot.py --df_road_path="data/processed/roads.parquet" --df_points_of_interest_path="data/processed/points_of_interest.parquet"  