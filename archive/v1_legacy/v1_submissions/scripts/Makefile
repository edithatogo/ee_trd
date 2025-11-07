# Makefile to run analyses
PY=python

all: psa dsa forest bia

psa:
	$(PY) psa_cea_model.py

dsa:
	$(PY) dsa_run.py
	$(PY) tornado_plot.py

forest:
	$(PY) forest_plot.py

bia:
	$(PY) bia_model.py

clean:
	rm -f psa_results.csv ceac.csv ceac.png dsa_results.csv tornado_plot.png forest_plot.png forest_plot_R.png
