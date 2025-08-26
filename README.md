# BibTeX Reference Optimizer

A Python tool that uses the DBLP API to optimize BibTeX reference files.

## Features

  - Reads paper entries from a BibTeX file.
  - Uses the DBLP API to search for and retrieve standardized publication information based on paper titles.
  - Extracts information such as authors, title, conference/journal name, pages, volume, and number.
  - Generates an optimized BibTeX file.
  - Preserves the original citation keys (cite keys).
  - Reports entries that failed to be processed.

## Dependencies

```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

```bash
python refine_bib.py
```

This will read the `ref_input.bib` file and generate an `ref_output.bib` file.

### Specifying Input and Output Files

```bash
python refine_bib.py input.bib output.bib
```

### Setting the API Request Interval

```bash
python refine_bib.py --delay 10.0
```

The default request interval is 10 seconds to avoid overly frequent API calls.

## Argument Explanations

  - `input_file`: Path to the input BibTeX file (Default: ref\_input.bib)
  - `output_file`: Path to the output BibTeX file (Default: ref\_output.bib)
  - `--delay`: API request interval in seconds (Default: 10.0)

## Example

The project includes an example `ref_input.bib` file containing several common machine learning paper citations. After running the tool, an optimized `ref_output.bib` file will be generated.

## Notes

1.  The tool searches DBLP based on the paper title. If the title is not accurate, a matching result may not be found.
2.  To avoid excessive requests to the DBLP server, it is recommended to maintain a reasonable request interval.
3.  Failed entries will be reported in the console, and their original information will be preserved in the output file.

## DBLP API

This tool uses DBLP's public search API:

  - API Endpoint: [https://dblp.org/search/publ/api](https://dblp.org/search/publ/api)
