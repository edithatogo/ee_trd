# Makefile for nextgen_v3 pipelines

PYTHON ?= python

v3-sourcing:
	$(PYTHON) nextgen_v3/cli/run_sourcing.py --costs-au data/cost_inputs_au.csv --costs-nz data/cost_inputs_nz.csv --utilities data/clinical_inputs.csv --provenance-doi data/parameters_psa.csv

v3-cea:
	$(PYTHON) nextgen_v3/cli/run_cea.py --jur AU --perspective health_system
	$(PYTHON) nextgen_v3/cli/run_cea.py --jur NZ --perspective societal

v3-psa:
	$(PYTHON) nextgen_v3/cli/run_psa.py

v3-dsa:
	$(PYTHON) nextgen_v3/cli/run_dsa.py

v3-dcea:
	$(PYTHON) nextgen_v3/cli/run_dcea.py

v3-bia:
	$(PYTHON) nextgen_v3/cli/run_bia.py --jur AU
	$(PYTHON) nextgen_v3/cli/run_bia.py --jur NZ

v3-evi:
	$(PYTHON) nextgen_v3/cli/run_evi.py

v3-regret:
	$(PYTHON) nextgen_v3/cli/run_psa.py  # Regret is included in PSA

v3-ecea:
	$(PYTHON) nextgen_v3/cli/run_cea.py --opportunity-cost

v3-structural:
	$(PYTHON) nextgen_v3/cli/run_cea.py --structural-pack

v3-smoke: v3-test-basic v3-cli-smoke

v3-test-basic:
	@echo "Running nextgen_v3 basic tests..."
	MPLBACKEND=Agg $(PYTHON) -m pytest nextgen_v3/tests/ -v --tb=short -x

v3-cli-smoke:
	@echo "Testing nextgen_v3 CLI imports..."
	$(PYTHON) -c "import nextgen_v3.cli.run_psa; print('PSA CLI import OK')"
	$(PYTHON) -c "import nextgen_v3.cli.run_cea; print('CEA CLI import OK')"
	$(PYTHON) -c "import nextgen_v3.cli.run_evi; print('EVI CLI import OK')"
	$(PYTHON) -c "import nextgen_v3.cli.run_bia; print('BIA CLI import OK')"
	$(PYTHON) -c "import nextgen_v3.cli.run_dcea; print('DCEA CLI import OK')"
	$(PYTHON) -c "import nextgen_v3.cli.run_dsa; print('DSA CLI import OK')"
	$(PYTHON) -c "import nextgen_v3.cli.run_mcda; print('MCDA CLI import OK')"
	$(PYTHON) -c "import nextgen_v3.cli.run_sourcing; print('Sourcing CLI import OK')"
	$(PYTHON) -c "import nextgen_v3.model.psa; print('PSA model import OK')"
	$(PYTHON) -c "import nextgen_v3.model.cea_engine; print('CEA engine import OK')"
	$(PYTHON) -c "import nextgen_v3.model.value_of_info; print('VoI model import OK')"
	$(PYTHON) -c "import nextgen_v3.model.dcea; print('DCEA model import OK')"
	$(PYTHON) -c "import nextgen_v3.model.ecea; print('ECEA model import OK')"
	$(PYTHON) -c "import nextgen_v3.model.mcda; print('MCDA model import OK')"
	@echo "All v3 CLI and model imports successful"

v3-all: v3-sourcing v3-cea v3-psa v3-dsa v3-dcea v3-bia v3-evi v3-regret v3-ecea v3-structural