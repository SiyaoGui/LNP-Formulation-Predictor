# Hardware: a measuring and control module for microfluidic mixers

Nothing in this folder has been built yet. It describes the module we plan to build, the order we plan to build it in, and the data record every run will write.

## Why hardware

The modelling work in this repository showed that literature data cannot be pooled across labs: every paper uses its own assay, buffer, payload and mixing setup, and the model's advantage disappears as soon as whole papers are held out. More literature data will not change that. What is missing is data measured the same way every time.

A microfluidic mixer already controls the mixing. It does not measure what it makes: particle size is measured offline by DLS after the run, and encapsulation efficiency later still. The module adds that measurement at the outlet, uses it to correct the process, and stores every run in one format. Each run then becomes a comparable data point for the models.

The module fits mixers that labs already own. Pumps and chips are bought off the shelf; the new parts are the sensor and the controller.

## Levels

| Level | What the machine can do | New hardware | Status |
|---|---|---|---|
| L0 | Pumps, mixes and collects at a set total flow rate (TFR) and flow rate ratio (FRR); product is measured offline by DLS | None | Exists in commercial mixers |
| L1 | Suggests a formulation and process settings before a run | None, software only | Next |
| L2 | Knows particle size and aggregation at the outlet in near real time | Flow cell, optical sensor, signal processing | Planned, first prototype |
| L3 | Corrects FRR, TFR or lipid concentration when size drifts from the target | Programmable pumps, flow sensor, controller | Planned |
| L4 | Changes lipid molar ratios, dispenses into well plates and picks the next experiment itself | Independent pumps per lipid stock, fraction collector | Long-term goal |

L2 and L3 are where we start. L1 on its own is a software feature that mixer vendors can add more cheaply than we can, and one vendor we interviewed said it is already building one. L4 is the long-term goal and depends on L2 and L3 working first.

## Architecture

The module is split into five layers so that each can be tested and replaced on its own.

| Layer | Contents | First version |
|---|---|---|
| Fluid interface | Low dead-volume flow cell, 1/4-28 fittings, ethanol-resistant materials (quartz, PEEK, FEP) | Off-the-shelf quartz flow cuvette with standard fittings |
| Optical head | Laser diode with detectors at several angles (90° scatter, forward scatter, transmission), space for a fluorescence channel | Photodiodes with transimpedance amplifiers, based on the open-source OpenDLS design |
| Compute | Sampling, autocorrelation, feature extraction, soft-sensor model | Raspberry Pi and Python; linear or small tree models first |
| Control | Writes pump settings back, with safety limits | Our own open-source syringe pumps, so we do not depend on a vendor opening its interface |
| Data | One standard record per run, local database and export | SQLite with JSON export |

## What the sensor measures

| Generation | Measures | Method | Speed |
|---|---|---|---|
| 1 | Particle size, PDI, particle concentration, aggregation and chip clogging | Laser light scattering at several angles plus transmission; passive, no reagents | Seconds, fast enough to adjust within a batch |
| 2 | Encapsulation efficiency | Near-line. For nucleic-acid payloads: RiboGreen fluorescence before and after lysis with Triton (excitation 485 nm, emission 530 nm). For small-molecule payloads: method not chosen yet | Minutes, so adjustments happen between batches |
| 3 | Nucleic-acid concentration, buffer pH and conductivity, ethanol removal | UV at 260 nm, pH and conductivity probes | Seconds |

Size comes first because it needs no reagents and can be developed on calibration beads and cheap blank liposomes. Encapsulation efficiency matters more to users: the formulation developer we interviewed ranked it first. We have not found a commercial product that puts encapsulation efficiency inside the production loop.

No version of the sensor will measure transfection, biodistribution, toxicity or stability after weeks of storage. Those stay with the models.

### Rules for the first sensor

1. At least two detection angles, using the ratio between them. Scattered intensity depends on both size and concentration, and a single angle cannot separate the two. The absolute intensity is kept separately as a concentration proxy.
2. A thermistor on the flow cell. Size is calculated through viscosity, and viscosity changes with temperature.
3. Record the ethanol fraction, or dilute the sample to a fixed ratio before measuring. Freshly mixed samples contain over 20% ethanol, which changes viscosity and refractive index.
4. Reject bubbles. A sudden jump in both signals marks a bubble; that reading is discarded and repeated.
5. A flow cell that can be taken apart and cleaned. Lipid film on the optical window is expected, and later versions can use a disposable cartridge.

### Near-line, not in-line

Standard DLS cannot measure a flowing sample, because the flow destroys the correlation signal. The first version therefore diverts a small volume through a three-way valve into a static flow cell, measures it and flushes. A delay of 30 to 60 seconds is acceptable for process control.

## The control loop

1. The user sets a target size for the current formulation.
2. The machine runs two or three TFR settings.
3. The sensor estimates size for each.
4. The machine fits the local relationship between flow and size for this formulation.
5. It solves for the settings that hit the target, runs them and checks the result.
6. A sample goes to offline DLS to recalibrate the sensor model.

The loop does not need the literature model to be accurate. Size falls monotonically with total flow rate for a fixed formulation, so a local fit from a few runs is enough. A good prior from the literature model only saves a run or two.

Flow rate alone has limited reach. Above a certain flow, mixing is faster than self-assembly and size stops falling. Our second lever is total lipid concentration, set by an extra dilution pump on the ethanol line. The first job on the bench is to measure the range of sizes the setup can reach, so that targets are set inside it.

## Three different models

| Model | Task | Difficulty | Status |
|---|---|---|---|
| Literature model | Predict size, PDI and encapsulation across papers | Hardest, because every paper uses different equipment and assays | Results in `docs/algorithm-results-en.md` |
| Soft-sensor model | Turn optical signals into a size estimate on one machine | Much easier: one machine, paired ground truth from the same sample | Not started; an open-source design reports about 11% error on standard beads |
| Process model | How flow and concentration change size for the current formulation | A monotonic curve, fitted from three to five runs | Not started |

The hardware replaces one hard extrapolation problem with two interpolation problems.

## What the algorithm does in the loop

For quantities the machine can measure (size, PDI, and encapsulation efficiency from generation 2), the model gives a starting point and the measurement corrects it. The measure of success is how many runs the prior saves, not R².

For quantities the machine cannot measure (which lipids, which ratios, behaviour in vivo), the model is the only source and is shown to the user with its uncertainty. These predictions never drive the loop.

Every run record holds both the prediction and the offline measurement. That makes each run a prospective test of the model, which is a stronger check than grouped cross-validation on literature data.

## Run record

Every run writes one record in the format shown in `run_record.v1.example.json`. The device, chip and calibration fields are what the literature data lacks: in our own data the source of every measurement is recorded explicitly, so batch effects can be corrected rather than guessed. The `in_domain` field marks whether a prediction falls inside the model's training data; predictions outside it are stored but not used for decisions.

## Prototype plan

| Stage | Planned timing | Work | Pass if |
|---|---|---|---|
| 0 | Oct to Nov 2026 | Read the key papers, book DLS time, fix the run record | Optical and fluid layout drawn; record format agreed |
| 1 Optical bench | Nov 2026 to Jan 2027 | Laser, two-angle photodiodes, thermistor, Raspberry Pi, quartz cuvette, calibration beads | Size and concentration separated on a 3 × 3 bead matrix; under 15% error on standard beads |
| 2 Mixing bench | Feb 2027 | Two or three open-source syringe pumps including the dilution line, glass herringbone chip, blank liposomes from cheap lipids | Reproducible, tunable liposomes; near-line reading tracks offline DLS; at least 30 paired data points |
| 3 Closed loop | Mar to Apr 2027 | Three-way valve, automatic flushing, automatic targeting with both levers | Two target sizes inside the reachable range, three independent runs each within ±10% |
| 4a Encapsulation sensor | May to Jun 2027 | Generation 2 sensor | Near-line encapsulation within 5 percentage points of the offline value |
| 4b Composition | Second half of 2027 | Independent pumps per lipid stock; first unit in an external lab | Runs in an outside lab |

Stages 1 to 3 together are budgeted at 14,000 to 21,000 DKK. Prices for pumps, chips and the flow sensor are from supplier listings; the rest is an estimate until we have quotes. Stage 2 onward needs a fume hood and borrowed DLS time.

The 30 paired data points in stage 2 are the first result worth showing outside the team: measurements from one machine, in one format, with offline ground truth.

## Related work

In September 2026, a group at MIT published autonomous lipid nanoparticle formulation with closed-loop control of particle size (ACS Nano, doi:10.1021/acsnano.6c15600). Their loop uses a commercial DLS instrument and adjusts the residence time between two mixing stages. Our module aims at a lower-cost sensor, at encapsulation efficiency inside the loop, and at a price that fits a research lab.
