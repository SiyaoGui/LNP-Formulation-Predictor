---
title: LipidLens
emoji: 🔬
colorFrom: green
colorTo: gray
sdk: streamlit
sdk_version: 1.66.1
app_file: src/streamlit_app.py
pinned: false
short_description: Measuring and control module for lipid nanoparticle mixers
---

# LipidLens

LipidLens is a measuring and control module for the microfluidic mixers that labs already use to make lipid nanoparticles and liposomes. This Space explains the project and keeps our first formulation model as a demo.

The page has four tabs. The overview covers the problem and what we are building. The data tab summarises three modelling rounds on published formulations: within one experimental setting, molecular structure predicts encapsulation efficiency, but the advantage disappears once whole papers are held out, because labs prepare and measure samples differently. The hardware tab describes the planned module, its sensor and control loop, and the prototype stages. The last tab is the particle-size and PDI model from September 2026, kept to show the pipeline; under a fair test it does no better than predicting the average.

The hardware has not been built yet, and nothing here has been validated by an independent lab.

Code, data and the full modelling report: https://github.com/SiyaoGui/LNP-Formulation-Predictor

Siyao Gui and Akanksha Appaiah
