# Dorado workflow

Use Dorado for raw-read basecalling, alignment, demultiplexing, correction, polishing, trimming, summaries, or variant calling.

1. Identify the requested Dorado operation and input path.
2. Query the bundled specification:

```bash
python3 scripts/query_parameters.py dorado --list
python3 scripts/query_parameters.py dorado <subcommand>
```

3. Check only the selected subcommand inside Singularity.
4. Use an installed compatible model; do not download a model unless explicitly requested.
5. Validate the expected file type and inspect a lightweight summary rather than rerunning basecalling.

