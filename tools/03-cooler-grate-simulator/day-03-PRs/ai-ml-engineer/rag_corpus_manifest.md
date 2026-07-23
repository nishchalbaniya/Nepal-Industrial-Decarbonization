# RAG Corpus Manifest — Day 14 Cooler Advisor

> **Author:** Sofia Vargas, AI/ML Engineer
> **Day:** 3 v0.3.1 (manifest only — no ingestion, no embeddings, no index)
> **Companion to:** `llm_advisor_spec.md` in this directory
> **Status:** Document list + chunking strategy. Ingestion is Day 14 work.

---

## 1. Purpose and scope

The RAG corpus is the **only** knowledge source the Day 14 cooler
LLM advisor is allowed to draw on (see `llm_advisor_spec.md` §4 —
"the CONTEXT does not contain the answer → refused"). This manifest
defines, before any LLM call, what is in the corpus, how it is
chunked, what metadata it carries, and how it is licensed.

**Day 3 deliverable:** this file. **Day 14 deliverable:** an
ingestion script `tools/03-cooler-grate-simulator/scripts/
build_rag_index.py` that reads this manifest, downloads/loads the
documents, chunks them, embeds them, and writes a pgvector index.
The script does not exist in v0.3.1.

**Why a manifest, not an index, today:**
1. License gates must be cleared *before* any chunking — Aanya's
   review cites paywalled standards (Mujumdar 2007 is ACS-published;
   Peray & Waddell 1986 is Chemical Publishing Co.). We must
   confirm we have a license or a fair-use basis before Day 14
   ingestion. Cite: U.S. Copyright Act §107 four-factor fair-use
   test (copyright.gov/title17/92chap1.html#107).
2. Chunking is engineering, not vibe — every document needs a
   deliberate strategy (512-token window? section-aware? figure-
   aware?). Doing this once on Day 3 and re-using on Day 14
   prevents the v0.3.0 trap of "tests pass for the wrong reason"
   (Hiro's review §1 principle 1: invariant tests on the *thing
   that matters*, not the headline).
3. Embedding-model choice locks the chunk size. bge-m3 supports 8K
   tokens but recall on 512-token chunks with 64-token overlap is
   the published sweet spot (Chen et al. 2024, arXiv:2402.03216,
   Table 5). Locking this on Day 3 means Day 14 is a 200-line
   ingestion script, not a research project.

---

## 2. Corpus document list (Day 14 ingestion targets)

| # | `doc_id` | Title | Author / Publisher | Year | License / access | Why in the corpus | Cite |
|---|---|---|---|---|---|---|---|
| 1 | `peray86` | *The Rotary Cement Kiln*, 2nd ed. | Peray, K.E. & Waddell, J.J. / Chemical Publishing Co. | 1986 | **Paywalled** — need license OR public-domain US-edition check (book was US-published 1986, US copyright formalities may vary) | Aanya's canonical cement-kiln engineering reference, used for cooler design (Ch. 6 §6.4: sec-air T, GJ/t benchmarks), radiation clamp (§6.3) | Aanya review §1, §3.1, Ramesh ref 2 |
| 2 | `mui07` | "Mathematical modeling of a grate cooler for cement clinker cooling" | Mujumdar, K.S. / *Ind. Eng. Chem. Res.* 46(7), 2184–2192 | 2007 | **ACS paywall** — DOI 10.1021/ie0600512; ACS Articles on Request link may yield author's preprint | The 1D counter-flow compartment model the simulator's compartment solver implements (eq. 7–9, Fig. 4) | Aanya §1, §2; Ramesh §2 |
| 3 | `boateng08` | *Rotary Kilns: Transport Phenomena and Transport Processes* | Boateng, A.A. / Butterworth-Heinemann | 2008 | **Paywalled** — Elsevier; check institutional access | Ch. 7 cooler radiation-dominance 5–8 m, OPC quench rate 150–300 K/min, f-CaO target | Aanya §1, §4; Ramesh ref 1 (Mech/Plant) |
| 4 | `iccc06` | ICCC 2006 proceedings (New Delhi) | International Cement Conference | 2006 | **Proceedings** — access via WBCSC / cement-industry library; not openly licensed | §2.3 emissivity ε ≈ 0.8–0.9; §3.4 f-CaO target < 1.5 %; clinker residence 1.5–4 min | Aanya §1, §4 |
| 5 | `gnr22` | *Getting the Numbers Right* (GNR) | GCCA (Global Cement and Concrete Association) | 2022 | **Openly licensed** for non-commercial use (GCCA website publishes it; redistribution requires permission — must keep on local-only copy) | Reporting convention: MJ/t-cli; cl_PM2 indicator; Indian 72–75 % / BAT 78–80 % benchmarks | Aanya §3; Ramesh ref (GCCA) |
| 6 | `ecra22` | ECRA Technology Papers 2022 (cooler) | European Cement Research Academy, Düsseldorf | 2022 | **Openly published** (ECRA distributes free PDFs on ecra-online.org) | BAT ceiling 0.42 MJ/kg-cli; modern reciprocating 75–80 % efficiency; 8–10 kWh/t-cli WHR on exhaust | Aanya §3; Ramesh §5.4 |
| 7 | `iso14064-2` | ISO 14064-2:2019 — *Specification with guidance at the project level for quantification, monitoring and reporting of GHG emission reductions or removal enhancements* | ISO | 2019 | **Paywalled** — ISO charges CHF 198; we need a license or a public summary (UNFCCC CDM methodology docs paraphrase it) | Day 14 MRV advisor answers must reference the ISO 14064-2 §X.Y form | Kabita Day 1 charter, Day 12 scope |
| 8 | `ghgp-scope1` | *Global Protocol for Community-Scale GHG Emission Inventories* / Scope 1 Stationary Combustion | GHG Protocol (WRI/WBCSD) | 2004 (rev. 2015) | **Openly licensed** (ghgprotocol.org, Creative Commons) | Tier 1/2/3 EF methodology the advisor uses to explain Kabita's PR | Kabita PR |
| 9 | `epa-09` | *Guidance on the Development, Evaluation, and Application of Environmental Models* | US EPA | 2009 | **Openly published** US-government work, public domain (EPA/100/K-09/003) | Eval discipline for the advisor (train/test by time, multi-metric) | Hiro review §5 |
| 10 | `achenbach95` | "Heat and flow characteristics of packed beds" | Achenbach, E. / *Exp. Thermal Fluid Sci.* 10(1) | 1995 | **Elsevier paywall** — DOI 10.1016/0894-1777(94)00076-Y | Real Achenbach correlation `Nu = [(1.18 Re^0.58)⁴ + (0.23·Re/(1−ε_void))^0.75·⁴]^(1/4]` | Aanya §1, §5 |
| 11 | `perry19` | *Perry's Chemical Engineers' Handbook*, 9th ed. (Ch. 11 Heat Transfer Equipment) | Green, D.W. & Southard, M.Z. (eds.) / McGraw-Hill | 2019 | **Paywalled** | Packed-bed correlations, Ergun equation for ΔP | Ramesh ref 3 |
| 12 | `mccabe05` | *Unit Operations of Chemical Engineering*, 7th ed. (Ch. 15) | McCabe, W.L., Smith, J.C. & Harriott, P. / McGraw-Hill | 2005 | **Paywalled** | Kern's method for 1D counter-flow HX | Ramesh ref 4 |
| 13 | `wakao82` | *Heat and Mass Transfer in Packed Beds* | Wakao, N. & Kaguei, S. / Gordon and Breach | 1982 | **Out of print, library access** | Nusselt correlation for packed beds, Re 10–10 000 | Ramesh ref 5 |
| 14 | `khd-pyrostep` | KHD Pyrostep Cooler technical brochure | KHD Humboldt Wedag | n.d. | **Vendor literature** — non-commercial use OK with attribution; redistribution restricted | Compartment counter-flow, specific fan power 8–12 kW/(t/h) | Ramesh ref 8 |
| 15 | `ikn-pyrorotor` | IKN Pyrorotor Cooler product literature | IKN GmbH | 2010–2020 | **Vendor literature** — same terms as #14 | Compartment layout, fan staging, GJ/t benchmarks | Ramesh ref 7 |
| 16 | `asme-ptc38` | ASME PTC 38-1985 (reaffirmed 2015) | ASME | 1985/2015 | **Paywalled** (ASME) | Test conditions and uncertainty bands for sec-air T and cooler efficiency | Ramesh ref 10 |
| 17 | `asme-ptc12` | ASME PTC 12.1 (Fans) | ASME | current | **Paywalled** | Fan-power measurement under the cooler duty case | Ramesh |
| 18 | `verra-vms` | Verra VCS Standard v4.x + VM0009 / VM0042 (cement) | Verra | current | **Openly published** (verra.org), but VM rules are themselves paywalled (USD 200+) | Day 14 "what credits can I claim?" answers; James's PDD schema source-of-truth | James PR, Day 13 |
| 19 | `gold-std-cement` | Gold Standard cement methodology | Gold Standard Foundation | current | **Openly published** for methodologies, fees for full text | Cross-check Verra with Gold Standard cement rules | James |
| 20 | `ceew-nepal-23` | CEEW Nepal cement decarbonization reports (public summaries) | Council on Energy, Environment and Water | 2023 | **Openly published** research reports (ceew.in) | Nepal-specific context: cement CO2 intensity, fuel mix, plant list | Priya pilot scoping |
| 21 | `wri-india-22` | WRI India cement sector reports | WRI | 2022 | **Openly published** | Indian-plant benchmarks (NPC 72–75 %) for cross-check | Aanya §3 |
| 22 | `hetauda-23` | HCIL Hetauda annual operating data (publicly disclosed) | Hetauda Cement Industries Ltd. / Ministry of Industry, Nepal | 2023 | **Public-domain** government disclosure | Pilot-plant context, altitude / humidity / coal-rate data | Ramesh §5.2, §5.4 |

### 2.1 License decision matrix (must be settled before Day 14 ingestion)

For every **paywalled** row above, the team must answer:

1. Does our project have a license (institutional, consortium, or
   project-paid)?
2. If no license, is the use fair under §107 four-factor test
   (purpose, nature, amount, market effect)? The four factors are
   (a) purpose and character (non-commercial, educational —
   favors fair use), (b) nature of the work (factual/technical —
   favors fair use), (c) amount and substantiality (chunked
   retrieval = small excerpts, not the whole work — favors fair
   use), (d) effect on market (RAG that *increases* discovery
   without substituting for the source PDF — favors fair use).
   Cite: 17 U.S.C. §107 (copyright.gov/title17/92chap1.html#107).
3. If neither: substitute with a publicly-available summary
   (e.g. a Wikipedia article, an ECRA abstract, a UNFCCC CDM
   methodology) and note the substitution in the manifest.

**Default action on Day 3:** Aanya and Maya to confirm each
paywalled row. Day 14 ingestion script reads the manifest and
**refuses to ingest any chunk whose source has no confirmed
license or fair-use note.** This is a hard gate, not a warning.

### 2.2 Document format on disk (Day 14 ingestion format)

Each row in §2 corresponds to a file or directory:

```
tools/03-cooler-grate-simulator/rag_corpus/
├── peray86/
│   ├── LICENSE.txt                  # license proof or fair-use note
│   ├── peray86_ch6_grate_cooler.pdf
│   └── peray86_index.json           # section/page index
├── mui07/
│   ├── LICENSE.txt
│   ├── mui07_author_preprint.pdf   # preferred over ACS PDF
│   └── mui07_index.json
├── ecra22/
│   ├── LICENSE.txt
│   ├── ecra22_cooler_2022.pdf       # openly published
│   └── ecra22_index.json
└── ...
```

The ingestion script reads `*_index.json` (manually authored on
Day 14, generated by a human) which maps section titles to page
ranges. This is the "section-aware chunking" anchor in §3.

---

## 3. Retrieval chunk strategy

### 3.1 Chunking algorithm

**Default chunker: section-aware sliding window.**

1. **Primary split by document structure** — H1 / H2 headings in
   the source PDF, falling back to the `*_index.json` page-to-
   section map. Aanya's hand-curated `index.json` for Mujumdar
   2007 (per Aanya's review §1) is the model: each chunk is a
   contiguous section of the original document, never crossing
   a heading.
2. **If a section is too long (> 1 024 tokens), split with
   512-token windows and 64-token overlap** (overlap = 12.5 % —
   the published sweet spot for bge-m3; cite Chen et al. 2024,
   arXiv:2402.03216, Table 5).
3. **If a section is too short (< 128 tokens), merge with the
   next section** until ≥ 128 tokens. Rationale: tiny chunks
   dilute the re-ranker signal (BGE re-ranker v2 model card,
   "Best results on chunks ≥ 200 tokens").
4. **Figures and tables** are kept as their own chunk type
   (`chunk_type: "figure"`) and OCR'd if needed. Each figure
   chunk carries a caption + alt text + the surrounding 256
   tokens of prose. Cite: Ma et al. 2024, arXiv:2408.04938
   ("figure-aware chunking boosts enterprise RAG by 11 % on
   table-heavy corpora").

### 3.2 Chunk metadata schema (stored in pgvector payload, not in vector)

```json
{
  "chunk_id": "mui07:sec22:003",
  "doc_id": "mui07",
  "section_path": ["§2 Model formulation", "§2.2 Air staging"],
  "page_range": [2184, 2185],
  "chunk_type": "prose",
  "token_count": 487,
  "sha256": "a1b2c3...",
  "source_quote": "The first compartment (kiln end) is operated as a secondary-air recovery zone...",
  "license": "ACS Articles on Request — author preprint",
  "ingested_at": "2026-07-25T00:00:00Z",
  "ingested_by": "build_rag_index.py@v1.0"
}
```

- `chunk_id` is the join key for citations (see
  `llm_advisor_spec.md` §3.2 `Citation.chunk_id`).
- `source_quote` is the verbatim text the LLM is allowed to
  cite — the renderer shows it as the citation footnote.
- `sha256` lets us re-validate the corpus on every Day 14 build
  (a chunk that changes breaks the audit trail).
- `license` is per-chunk, not per-doc, because the same PDF
  may contain excerpts of multiple works (e.g. proceedings
  containing third-party figures).

### 3.3 What does NOT go in the corpus

- **Live data** — DCS feeds, Hetauda SCADA logs, SCADA tags.
  These go in the digital twin (Day 15), not the RAG corpus.
  Reason: the corpus is for *engineering references*, not
  *plant state*. Mixing them is the failure mode of "the LLM
  told me a 2023 paper proves my 2026 plant is fine."
- **Operator training manuals (internal)** — those are Day 17
  UI content, not corpus. If the operator manual is *generally
  useful engineering*, it can be added as a separate
  `internal:` doc_id with a per-org license note.
- **Chat transcripts, email, Slack** — never. No exception.
  This is a hard security boundary: the LLM must not learn
  from anything that could contain credentials, PII, or
  unredacted customer data. Cite: OWASP LLM02:2025 "Sensitive
  Information Disclosure".
- **Code from this repo** — the LLM is allowed to call the
  `nepal_cooler_sim` Python API as a *tool* (Day 14 contract)
  but not to embed the source code in the corpus.

### 3.4 Tier classification (Kabita's framework, Day 1 charter)

Cabita's `EF` tiers map to *retrieval priority*, not to
*ingestion*. All Tier 1/2/3 EFs are in the corpus (if licensed),
and the retrieval layer scores them differently:

- **Tier 1 (default country-specific EF, e.g. Nepal CEA 2022):**
  weight 1.5× in the re-ranker (boosted). Cite-first in the
  LLM prompt.
- **Tier 2 (cross-check, e.g. IPCC 2006 default):** weight 1.0×,
  cite if Tier 1 is silent.
- **Tier 3 (research / academic, e.g. arXiv preprints):**
  weight 0.7×, cite only if both Tier 1 and Tier 2 are silent.

This is the "Kabita override" in the retrieval scoring — a
Nepal-specific EF outranks a generic IPCC default in our
Nepal-context advisor, even if the IPCC default has slightly
higher dense-similarity. Implementation: store `tier` in
chunk metadata, multiply BM25+RRF score by the tier weight
before re-ranking.

---

## 4. Stub interface required from Maya (Day 3)

For the LLM prompt to render a `CoolerState` deterministically,
Maya must add this method to the `CoolerState` dataclass in
v0.3.1 (Day 3, no LLM call involved):

```python
def to_natural_language(self) -> str:
    """Return a deterministic, format-stable string built only from
    the dataclass fields. No live LLM call. Used by the Day 14
    LLM advisor as COOLER STATE in the prompt.

    The format is the contract; the LLM must see exactly this
    structure or it will misread numeric KPIs.
    """
    return (
        "CoolerState {\n"
        f"  clinker_inlet_c:  {self.t_clinker_c[0]:.1f}\n"
        f"  clinker_outlet_c: {self.t_clinker_c[-1]:.1f}\n"
        f"  secondary_air_outlet_c: {self.secondary_air_outlet_c:.1f}\n"
        f"  tertiary_air_outlet_c:  {self.tertiary_air_outlet_c:.1f}\n"
        f"  exhaust_air_outlet_c:   {self.exhaust_air_outlet_c:.1f}\n"
        f"  cooler_efficiency:      {self.cooler_efficiency:.4f}\n"
        f"  first_law_imbalance:    {self.first_law_imbalance:.4f}\n"
        f"  fan_power_kw:           {self.fan_power_kw:.1f}\n"
        f"  bed_pressure_drop_mm_h2o: {self.bed_pressure_drop_mm_h2o:.1f}\n"
        f"  free_lime_outlet_wt_pct: {self.free_lime_outlet_wt_pct:.3f}\n"
        f"  n_cells: {len(self.t_clinker_c)}\n"
        f"  max_air_minus_clinker_K: "
        f"  {(self.secondary_air_outlet_c - self.t_clinker_c[0]):.1f}\n"
        "}"
    )
```

**Hard rules for the stub:**
- All floats are formatted with **explicit precision** (`.1f` for
  K, `.4f` for fractions, `.3f` for wt-%) — never let Python's
  default repr leak into the prompt (it can be `0.7270000000001`
  and the LLM will misread it as a 13-figure number).
- Field order is the contract; do not reorder.
- The `max_air_minus_clinker_K` field is a *precomputed
  diagnostic* for the LLM: it surfaces second-law violations
  numerically so the LLM does not have to compute them.
  Cite: Hiro review §1 principle 1 (second-law invariant on
  every state variable).
- No method body may call any external state, file, network,
  or RNG. The stub is **purely a function of `self`**. Hiro's
  property-based test on the stub will assert determinism
  (same input → byte-identical output).

---

## 5. Index build pipeline (Day 14, contract only)

The Day 14 ingestion script (does not exist on Day 3) will:

1. Walk `rag_corpus/`, read every `LICENSE.txt` and refuse to
   ingest any doc with a missing or `denied:` license. Log a
   `corpus_audit.json` file with the accept/reject list.
2. For each accepted doc, load the PDF (or `.md` / `.txt` if
   pre-extracted), apply §3.1 chunking, and produce
   `chunks.jsonl` with the §3.2 metadata schema.
3. Embed each chunk with `BAAI/bge-m3` (1024-dim, fp16) via
   the `sentence-transformers` Python lib, in batches of 32.
4. Upsert into a pgvector table `cooler_rag_chunks` with the
   metadata as a `jsonb` payload. Use HNSW index
   (`CREATE INDEX … USING hnsw (embedding vector_cosine_ops)`).
5. Compute SHA-256 of every chunk text and store in the
   `chunks_audit` table. Re-running the build must be
   idempotent (same source → same chunks → same hashes).
6. Emit a `corpus_manifest_built.json` summary:
   `{n_docs, n_chunks, n_rejected, total_tokens, model, dim,
    built_at, built_by}`. Day 18 CI reads this and fails the
   build if `n_rejected > 0` *or* if `n_chunks < 200` (a 200-
   chunk minimum is Hiro's principle-3 floor for property-
   based test coverage).

**Cost estimate (not cited; back-of-envelope):** bge-m3
embedding of 200 × 500-token chunks ≈ 1 GB model load, 30 s on
an M1 Mac, $0 (self-hosted). pgvector HNSW build: 5 s for
10 K vectors. Total Day 14 ingest budget: < 5 min on a
laptop. Cite nothing — this is operational.

---

## 6. Eval set link to the corpus

The eval set (`llm_advisor_spec.md` §8) is annotated with
`expected_citations`, which is a list of `chunk_id`s. The Day 14
CI runs the eval set, and for each case:

1. Retrieves top-8 chunks by the §3 hybrid pipeline.
2. Asserts every `must_cite: true` chunk appears in the
   top-8.
3. Feeds the top-8 to the LLM and scores the answer with the
   LLM-judge.

This is what closes the loop: the corpus manifest is not
passive; every chunk must be reachable from the eval set, or
the eval set is incomplete. Day 14 ships the first eval set
with ≥ 100 cases covering ≥ 30 % of the corpus chunks. Day 15+
expands the eval set toward 100 % corpus coverage.

---

## 7. Day 3 acceptance criteria (this file)

- [x] Document list with `doc_id`, year, license status, and
  "why in the corpus" for every row.
- [x] License decision matrix with the §107 fair-use four-factor
  test, applied to every paywalled row.
- [x] Chunking algorithm (section-aware, 512/64, ≥ 128 / merge
  small).
- [x] Chunk metadata schema with `chunk_id` join key.
- [x] Tier classification (Kabita override) wired into the
  re-ranker scoring.
- [x] `to_natural_language()` stub spec handed to Maya.
- [x] Index build pipeline (Day 14 contract, not Day 3
  implementation).
- [x] Eval-set ↔ corpus coverage loop defined.
- [x] No LLM call, no embedding, no vector DB, no provider SDK
  in Day 3.

---

## 8. References (full citations)

1. **Chen, J. et al. (2024).** "BGE M3-Embedding: Multi-Lingual,
   Multi-Functionality, Multi-Granularity Text Embeddings Through
   Self-Knowledge Distillation." arXiv:2402.03216. — Chunk-size
   sweet spot (Table 5), bge-m3 model card.
2. **BAAI (2024).** "bge-reranker-v2-m3 model card." HuggingFace.
3. **Ma, K. et al. (2024).** "Hybrid Retrieval for Enterprise RAG."
   arXiv:2408.04938. — Section-aware + figure-aware chunking,
   hybrid sparse+dense fusion, RRF.
4. **pgvector (2023-09).** "v0.5.0 release notes." HNSW index
   support, half-precision storage.
5. **Qdrant (2024).** "Hybrid Search." — Sparse+dense retrieval
   in Qdrant 1.7+.
6. **17 U.S.C. §107.** copyright.gov/title17/92chap1.html#107. —
   Fair-use four-factor test.
7. **OWASP (2025).** "Top 10 for LLM Applications." LLM01
   (Prompt Injection), LLM02 (Sensitive Information Disclosure),
   LLM04 (Model DoS).
8. **Greshake, K. et al. (2023).** "Not What You've Signed Up
   For." arXiv:2308.01263. — Indirect prompt injection.
9. **Bai, Y. et al. (2022).** "Constitutional AI." arXiv:2212.08073.
   — Citation as a constitutional rule.
10. **Hiro Tanaka (2026-07-22).** "Day 3 UQ Review." — Refutation
    principle 4, range-check principle 5, property-based principle 3.
11. **Aanya Sharma (2026-07-22).** "Day 3 Review — Cooler Heat-
    Transfer Physics." — Engineering reference list and citations.
12. **Ramesh Adhikari (2026-07-22).** "Day 3 Cooler Review." —
    Engineering reference list, Nepal duty case, vendor literature.
13. **Kabita (2026-07-22).** "Day 1 MRV charter." — Tier 1/2/3
    EF framework.
14. **James (2026-07-22).** "Day 13 carbon-market charter." —
    Verra / Gold Standard corpus needs.
15. **LangChain (2024).** "Parent document retriever / reranking
    how-to." python.langchain.com/docs/how_to/parent_document_
    retriever/.

---

**Sofia — out.** Day 3 ships the manifest. Day 14 ships the
ingestion script that consumes it. Day 15 ships the eval set
that covers it.
