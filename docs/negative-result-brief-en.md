# What we tested, and what we found

LipidLens · October 2026 · Siyao Gui, Akanksha

*One page. Written for people deciding whether to spend time or a laboratory on us.*

---

## The question

Can published lipid nanoparticle literature support a model that predicts formulation
outcomes for a new molecule?

Almost everyone building in this space assumes the answer is yes. We decided to test it
before building anything on top of it.

## How we tested it

The evaluation protocol was written, frozen and committed to version control **before any
model was run**. The commit timestamps are public and independently checkable: the protocols
land 4 h 23 m and 1 h 26 m ahead of the first result files.

Each round compared every model against four reference points: always predict the mean;
copy the most chemically similar molecule; formulation features only; molecule features
only. Each ran under three ways of holding data out (whole molecules, whole chemical
scaffolds, whole papers), five random seeds, with confidence intervals bootstrapped over
molecules rather than rows. Pass and fail thresholds were fixed in advance and are not
negotiable after the fact.

## What we found

**1. Scale did not help.** Three rounds, two target properties, sample size from 73 to 370
analysis units. Under paper-grouped validation the advantage over a constant baseline went
to zero every time.

**2. Particle size is a property of the process, not of the molecule.** Deleting every
molecular descriptor barely moved the error. Using molecular descriptors alone was worse
than predicting the mean. In one paper, two drugs with identical lipid composition and
different mixing gave 30 nm and 800 nm.

**3. The model was recognising the laboratory.** On encapsulation efficiency, knowing only
which paper a sample came from gives a mean absolute error of 12.7 percentage points. The
best model, with 2,090 chemical features, gives 13.9. Of nine models, none beat the paper
label. Assay method, lipid-to-payload ratio and buffer differ between publications, so the
same molecule can differ by twenty points between two laboratories.

## What we are careful not to claim

- Not one of our models beat an experienced chemist copying the most similar known molecule.
  Until that changes, we do not describe the model as useful.
- The paper-grouped result is "no detectable signal", not "no signal". With 37 papers the
  interval is wide enough to hide a modest effect.
- Conclusion 2 rests on our ablations plus mechanism and prior knowledge. The statistical
  support for the positive half of it, in our data, is weaker than the negative half.

## What follows

The binding constraint is measurement, not algorithms. A model cannot be built on pooled
public data because the data was never comparable. It has to be built on data generated on
one instrument, under one protocol, with everything but one variable held fixed.

So the next thing we do is not more modelling. It is a methodology study, with its pass mark
written in advance: a chemically diverse panel of molecules, three independently prepared
batches each, and an intraclass correlation above 0.8, meaning batch-to-batch variation
under a quarter of molecule-to-molecule variation. That number is the ceiling on any model's
accuracy in this system and nobody has published it.

## What we are looking for

- **A laboratory bench** for roughly 40 preparations over eight weeks: fume hood, particle
  sizing, and a way to quantify each compound.
- **Collaborators with their own formulation data.** Not a request for a dataset. We will
  train on your data under your terms and give you the model and the evaluation back. Our
  finding is precisely that cross-laboratory pooling fails, which is why a model fitted to
  one laboratory's data is worth more than one fitted to everyone's.
- **An independent laboratory** willing to measure a set of formulations against predictions
  we lock and timestamp first.

Everything above, including the code, the frozen protocols, the per-row predictions and the
rounds that failed, is public at **github.com/SiyaoGui/LNP-Formulation-Predictor**.
