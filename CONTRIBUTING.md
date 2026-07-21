# Contributing

We welcome engineers, climate scientists, Nepali plant operators, and policy folks.

## Ground rules
1. **Real data beats toy data.** If you can supply Nepali plant data, that's gold.
2. **Verifiable.** Every emission factor must cite IPCC 2006, ecoinvent, or a peer-reviewed source.
3. **Open standards.** GHG Protocol, ISO 14064, Verra VCS, Gold Standard.
4. **Documented in plain English.** Many users are plant managers, not coders.
5. **Reproducible.** `pip install -e .` and one command should run the tool.

## How to add a tool
Each tool lives in `tools/NN-name/` and is self-contained:
```
tools/NN-name/
├── README.md           # what it does, how to run
├── pyproject.toml      # or requirements.txt
├── src/                # source code
├── tests/              # pytest
├── data/               # input data (CC-BY-4.0)
├── app/                # optional Streamlit / web app
├── Dockerfile          # optional container
└── docs/               # methodology notes
```

Open a PR. Tag it with the relevant day number.
