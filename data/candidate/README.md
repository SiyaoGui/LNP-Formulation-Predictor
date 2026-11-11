# Candidate data

Hand-transcribed formulation data from two papers. **Not part of the training set.**
Section 4 says why.

Every number here was read cell by cell from the source PDF by a person, not extracted
automatically. Where the source contradicts itself, both readings are kept and flagged.
Nothing was silently corrected.

| File | Rows | Cols | Contents |
|---|---|---|---|
| `lokras2025_afm_si_measurements.csv` | 77 | 40 | Supporting Information tables S1 to S14: every formulation with size, PDI and encapsulation efficiency, plus full molar composition, cargo, dispersant and measurement state |
| `lokras2025_afm_maintext_measurements.csv` | 19 | 13 | Every physicochemical value printed in the main text, each with the verbatim sentence it came from |
| `mitra2025_mixing_ethanol_removal.csv` | 16 | 49 | One fixed composition made eight ways, before and after dialysis, with SAXS Rg and Dmax |
| `lokras2025_afm_compositions.csv` | 9 | 19 | Molar compositions from main-text Table 1 |
| `lokras2025_afm_si_pka.csv` | 4 | 9 | Apparent pKa values, which appear only in the Figure S1 caption |
| `derived_lokras2025_replicate_spread.csv` | 13 | 29 | **Derived, not transcribed.** Batch-to-batch size spread for the same nominal formulation in one laboratory |

## 1. Sources

**Lokras et al. 2025**, *Adv. Funct. Mater.* 35:e05627, DOI 10.1002/adfm.202505627.
Corresponding author Camilla Foged. Open access, CC BY. Replacing cholesterol with MMG-1.
The main text cites tables S1 to S7; the Supporting Information actually holds **fourteen**
tables, S8 to S14 being cited nowhere in the paper.

**Mitra et al. 2025**, bioRxiv, DOI 10.1101/2025.11.07.686408. Purdue, University of Sydney,
ANSTO. One fixed composition (ALC-0315 : DSPC : cholesterol : DMG-PEG2000 = 50 : 10 : 38.5 : 1.5,
yeast total RNA), varying only the mixing method, flow ratio, total flow rate and dialysis.

## 2. Checks that were run

- All 77 rows of the SI file sum to 100 mol% within 0.05.
- Three values printed in the main text reproduce exactly from the SI tables.
- The main text says binary cholesterol/MMG mixtures ranged "approx 180 to 215 nm"; the SI gives
  193.9, 214.8 and 181.0.
- Helix post-dialysis size growth computes to 12.44% from the table; the paper states 12.43%.

## 3. Contradictions in the sources, recorded rather than resolved

1. **Table S1 lists Cholesterol 38.5 / MMG-1 0 for a formulation named MMG (100%)**, which
   contradicts both its own name and Table S3. Transcribed as printed, flagged in
   `ambiguity_flag`. **The printed mol% still sums to 100, so an arithmetic check will not
   catch it.** Any merge script needs a name-versus-value consistency check as well.
2. Table S6 (cre mRNA) is numerically near-identical to Table S4 (spike mRNA). Two different
   cargoes giving the same size, PDI and EE is implausible.
3. Table S5 reports encapsulation efficiencies identical to S4 and S6 while sizes differ.
4. Apparent pKa: the Figure S1 caption gives SM-102 as 6.69, the main text as 6.67. The caption
   also cites Table S2 for pKa, but S2 has no pKa column and no SM-102 rows.
5. The main text claims EE above 94% for all compositions; Table S1 lists one at 82.0%.
6. Mitra: N/P ratio is 4 in Figure 1 and 5 in the Methods. Both are recorded, in
   `np_ratio_figure` and `np_ratio_methods`.
7. Mitra: the lipid order in the Methods sentence implies DSPC 38.5 / cholesterol 10, while
   Figure 1 labels DSPC 10 / cholesterol 38.5. Figure 1 was followed; this is a judgement.
8. Mitra: hand-mixing post-dialysis EE is 88.24% in Table 1 and 89.74% in the text (89.74 being
   the Ignite non-dialysed value). The table value is used.
9. Lokras main text gives two different sizes for what reads as the same formulation with spike
   mRNA. Both are kept, flagged.

## 4. Why this is not in the training set

Three reasons, in order:

1. **Cross-source encapsulation efficiency is not comparable.** This is the central finding of
   the modelling work (`docs/round2-review-2026-10-23.md`): knowing only which paper a sample
   came from predicts EE better than a model with 2,090 chemical descriptors. Pooling these rows
   with other sources dilutes rather than adds.
2. **Mitra is a fixed-composition set.** All 16 rows share one composition, so the composition
   signal is zero and the process signal is strong. Feeding it to a composition-to-size model
   pushes the weights further toward process features.
3. **Payload mismatch.** Mitra uses yeast total RNA, neither mRNA nor siRNA.

## 5. What it is useful for right now

**A noise floor, measured in someone else's laboratory.** `derived_lokras2025_replicate_spread.csv`
groups rows sharing composition, cargo and dispersant, and reports the spread across separately
reported batches. SM-102 with spike mRNA spans 78.0 to 109.0 nm across six batches, a 33.9%
spread, in one laboratory. That number is the reason the phase-one acceptance criterion in
`docs/phase1-design.md` is stated as an ICC rather than a fixed nanometre tolerance.

**Evidence that dispersant matters.** Table S12 versus S11: identical composition, D-PBS gives
138.2 nm and Tris plus sucrose gives 181.5 nm, a 31% shift with no composition change. Most
papers never report this column. `dispersant` and `dispersant_ph` are columns here.

**Composition-varying rows from one laboratory.** Restricted to fluc cargo, D-PBS and the
as-formulated state, the SI file gives 32 rows over 25 distinct nominal compositions and seven
different ionisable lipids, all from one group under one protocol.

## 6. Three flag columns that must survive any merge

| Column | Why |
|---|---|
| `composition_inferred` | Table S10 does not print mol%. Those 8 rows were filled from the parent formulation and are marked TRUE. Filter on this or treat them separately. |
| `measurement_state` | Stressed, freeze-thawed, prime and boost rows are not independent samples of the as-formulated state. |
| `dispersant` | See section 5. If one paper mixes two dispersants, a pair drawn across them is a process-varying pair, not a composition-varying one. |

## 7. Rebuilding

The build scripts are not in this repository. Both source PDFs are open access; the file layout
and the checks in section 2 are enough to reproduce the transcription. Budget a full day.
