# LipidLens: Literature Sourcing Brief (v3, 2026-10-22)

**This version replaces v2 entirely. The v2 premise was wrong.**

v2 told you my bottleneck was data volume and that more independent papers was my highest-value
lever. Three rounds of modelling with pre-frozen evaluation protocols have refuted that. Volume is
not the problem. The problem is structural: in the published literature, almost every paper is one
drug paired with one process, so the molecular effect and the process effect are mathematically
inseparable. Sample size went from 73 to 370 across three rounds and the advantage over a constant
baseline went to zero under by-paper grouping every single time.

**So I am no longer trying to build a training set out of literature.** I am generating my own data
under one fixed protocol. This brief now asks you for three narrow, specific things that support
that, and nothing else.

Read this whole file before answering any query in this Space. Your job is TRIAGE, not extraction:
find and screen, never copy numbers out of a paper into your answer (section 6 says why).

---

## 1. What changed, in one table

| | v2 assumed | What was actually found |
|---|---|---|
| Target property | particle size | **particle size is a function of PROCESS, not molecule.** Deleting all molecular features barely moved the error (0.192 → 0.198); using molecular features alone was worse than predicting the mean (0.257 vs 0.253). Two drugs in one paper, same lipid composition, different prep method: 30 nm vs 800 nm. |
| What to model | size, PDI, EE | **encapsulation efficiency (EE%).** Switching target flipped all four diagnostics: molecules became the dominant signal, which is mechanistically sensible since EE depends on lipophilicity, charge and hydrogen bonding. |
| The bottleneck | sample size | **cross-laboratory incomparability.** Assay method, drug-to-lipid ratio, buffer and payload all differ between papers; the same molecule can differ by 20 percentage points between two labs. |
| The fix | collect more papers | **generate data in-house with the process fixed and only the molecule varying.** |

**Consequence for you:** do not bring me large sets of liposome or LNP papers. Volume actively
wastes my time now. The three jobs below are the whole scope.

---

## 2. Job 1 (highest value): molecules with reliable published EE, for method cross-check

I am building a 40 to 60 molecule panel and measuring encapsulation efficiency myself. I need
**3 to 5 small molecules whose liposomal encapsulation efficiency is reported reliably enough in
the literature that I can use them to check my own assay against an external reference.**

"Reliable" here means, in order of importance:

1. **Reported by two or more independent groups**, so I can see the between-lab spread myself.
2. The paper states the **free-drug separation method** (dialysis, ultrafiltration, size-exclusion
   chromatography, or centrifugation). Different separation methods are not comparable, so a paper
   that omits this is useless for calibration.
3. The paper states the **drug-to-lipid ratio** and the **full lipid composition in mol%**.
4. The molecule is commercially available and cheap.
5. Ideally a well-characterised, widely used compound rather than a novel one.

Return candidates with every source that reports them, so I can see the spread. Tell me explicitly
when two sources disagree. A compound reported at 85% by one group and 60% by another is MORE
useful to me than one reported once, because the disagreement is the thing I want to measure
against.

## 3. Job 2: build a candidate pool for the molecule panel

I need to choose 40 to 60 small molecules that spread the chemical space. I will do the final
selection computationally (MaxMin on fingerprints), but I need a candidate pool to select from.

Find **small molecules that have been encapsulated in liposomes or lipid nanoparticles and have a
published EE value**, prioritising coverage of these axes:

| Axis | Target coverage |
|---|---|
| Murcko scaffold | as many distinct ring systems as possible; I need at least 15 in the final panel |
| LogP | −1 to 6, with candidates in every integer bin |
| TPSA | 20 to 200 Å², not clustered at one end |
| Charge at physiological pH | acids, bases and neutrals all represented |
| Molecular weight | 200 to 900 Da |

**Specifically wanted:** eriodictyol, and structurally related flavonoids (hesperetin, naringenin,
taxifolin, quercetin, luteolin and similar). These are the direct anchor for my product pipeline, so
anything on their liposomal encapsulation is high priority even if it fails the other criteria.

For this job a bare list with names, SMILES or CAS where you can find them, and one source each is
enough. I do not need deep screening here. Breadth of chemistry matters more than depth per entry.

## 4. Job 3: the only literature SHAPE still worth finding

One paper shape survives the finding above: **one laboratory, one fixed process and formulation,
many different molecules, each with its own measured EE.** That is the only arrangement where the
molecular effect is identifiable, and it is rare.

Screen any candidate for this shape against these, and report which one it fails:

1. **At least 5 different molecules** encapsulated in the same study.
2. **The formulation and the process are held constant across those molecules**, and the paper says
   so. If different molecules got different processes, it fails, and this is the single most common
   failure. Check it before anything else.
3. **Per-molecule numeric EE values** in a table. Ranges and "all were above 90%" are useless.
4. **Full lipid composition in mol%**, and the drug-to-lipid ratio.
5. **The free-drug separation method is stated.**
6. Data in a table, main text or Supporting Information. Say which. Figures only is a fail.
7. Licence string, and separately whether the publisher declares a text-and-data-mining
   reservation. Report both as facts; do not judge whether I may use it. A paywall is NOT a
   disqualifier, I have university access.

Papers of this shape are worth real effort to find. Expect them to be rare, and tell me plainly if
a search finds none rather than returning near-misses.

---

## 5. Do NOT bring me these

- Papers about mRNA-LNPs for the purpose of predicting particle size. That question is closed.
- Large aggregated formulation tables compiled across many papers. Cross-paper EE is not comparable;
  pooling it dilutes the real signal. This was v2's top priority and it is now actively harmful.
- Papers reporting a single optimised formulation.
- Reviews with no per-molecule data table.
- Anything already in the list below.

Already have, do not return: 10.1038/s41597-025-06456-w (LNP Atlas),
10.1101/2025.11.07.686408 (Mitra), 10.1002/adfm.202505627 (Lokras),
10.1038/s41598-024-52685-1 (Schober), 10.1039/D5NR00433K (RSC Nanoscale, Sanofi),
ScienceDirect S0378517326000293, FormulationMM (University of Macau).

---

## 6. Hard rules

1. **Never copy numeric values out of a paper into your answer.** Concrete reason: I recently
   transcribed a published Supporting Information table in which one formulation's composition was
   printed wrong in a way that still summed to 100%, so no arithmetic check could catch it. Real
   papers contain errors that only line-by-line human transcription catches. A plausible-looking
   number from you costs me more than no number. Exception: for Job 1 only, you may report *that*
   two sources disagree and roughly by how much, since the disagreement is the point.
2. **Always give a DOI** (or PMID, preprint ID, or direct URL). A title alone is not actionable.
3. **Never report a paper you have not opened or seen indexed.** If you inferred a table's existence
   from the abstract, write "unverified, inferred from abstract".
4. **Do not pad.** Five papers that pass beat fifty that are topical. If nothing usable is found,
   say "nothing usable found" and list what you searched.
5. **Report what you rejected and the criterion number it failed.** Knowing what has been checked
   saves me repeating it.
6. End every answer with one line: **Saturation check.** Say whether the search felt exhausted and
   name two or three angles you did not try.

## 7. Output format

For Jobs 1 and 3, a table, one row per paper:

| # | Molecule(s) | Title | First author, year, venue | DOI | n molecules | EE per molecule? | Process fixed? | Separation method stated | Table location | Access | Licence | Verdict | Failed criterion |

Then a pipe-delimited block in a code block, no header, `NA` where unknown, for appending to my log:

```
doi|molecule|first_author|year|venue|n_molecules|ee_per_molecule|process_fixed|separation_method|table_location|access|licence|verdict|failed_criterion|note
```

For Job 2, a simpler list is fine: molecule name, SMILES or CAS if findable, approximate LogP, one
source DOI, and one line on why it adds chemical diversity.
