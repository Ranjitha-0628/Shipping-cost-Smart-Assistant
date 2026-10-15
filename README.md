Smart Assistant to monitor Shipping Costs 

The smart assistant shipping cost tracker is a tool that analyses weekly  shipping costs and identifies routes where transportation expenses have increased unexpectedly.

It calculates the cost per tonne-kilometre for each route, compares it with the route's past performance and similar routes, and flags unusual increases for review. It also checks relevant context notes, such as fuel price changes, festivals, and weather disruptions, to determine whether an increase has a documented explanation.

The main goal is to provide evidence-based explanations rather than assumptions.

The key features include:

1. Calculates weekly shipping costs per tonne-kilometre.

2. Compares costs against historical route averages and similar routes.

3. Flags unusual cost increases using configurable thresholds.

4. Retrieves relevant context notes using semantic similarity.

5. Validates notes against the route, date range, and stated cost impact.

6. Generates an output CSV with the required columns.

7. Includes evaluation checks and reproducibility testing.

Pipeline Workflow:

1. Data preparation: Loads shipment records, validates the data, and groups shipments into Monday-to-Sunday weeks.

2. Cost analysis: Calculates weekly cost per tonne-kilometre and compares it with historical and peer-route baselines.

3. Anomaly detection: Identifies unusual cost increases using predefined thresholds.

4. Context retrieval: Searches the available notes for potentially relevant explanations using a local embedding model.

5. Evidence validation: Checks whether a note applies to the route and time period and confirms that it supports an increase in costs.

6. Output generation: Writes the results to output.csv, including the flag, matched note ID, and explanation.


Tech Stack used:

Python — core implementation

Pandas and NumPy — data processing and numerical calculations

Sentence Transformers — semantic retrieval using BAAI/bge-small-en-v1.5

Scikit-learn or NumPy-based similarity calculations — depending on the retrieval implementation

CSV — input data and output reports


Results:

The pipeline analysed the shipment data and identified 13 unusual weeks out of 721 weeks with an available historical baseline.

4 justified increases: Supported by relevant context notes.

9 unexplained increases: No note passed the evidence checks.

The results were tested using manually labelled cases, deliberately incorrect or irrelevant notes, and injected cost increases without supporting explanations. The project also includes checks for consistent output across repeated runs.

Project Structure:

data/
    shipment_records.csv
    context_notes.csv
    sample_outputformat_csv

src/
    metrics.py
    flagging.py
    notes.py
    retrieval.py
    verdict.py
    output.py
    eval.py

evidence/
    eval_results.txt
    repo_results.txt
    cost_log.txt
    threshold_results.txt
    output_run1.csv, output_run2.csv, output_run3.csv

run.py
repro_check.py
cost_log.py
threshold_check.py
output.csv
README.md
requirements.txt

How to Run:

Requirements: Python 3.9 or a compatible environment, and an internet connection for the initial embedding-model download.

- Install the dependencies:

pip install -r requirements.txt

- Run the pipeline:

python run.py

This generates output.csv.

- Run the evaluation checks:

python -m src.eval

- Check reproducibility:

python repro_check.py

- Review the threshold comparisons:

python threshold_check.py

- Limitations and Future Improvements

The system has been developed around a small set of shipment records and context notes. Its detection thresholds and some note date ranges require further validation. Historical averages can also adapt to sustained cost increases, making prolonged changes harder to detect, while small peer groups may limit the usefulness of route comparisons.

Future improvements could include testing on a larger labelled dataset, handling longer-lasting cost changes, automating context-note date extraction, and adding a simple interface for reviewing flagged routes.