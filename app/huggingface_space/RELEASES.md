# Space releases

The Hugging Face Space at https://huggingface.co/spaces/AliceSnack/lnp-formulation-predictor is deployed from this folder. Each release is tagged in both repositories, so any version can be restored.

| Version | Date | GitHub tag | Space commit | Space tag | What changed |
|---|---|---|---|---|---|
| v1 | 2026-10-28 | `space-v1-2026-11-09` | `21bc612` | `before-vi-redesign-2026-11-09` | Project page with four tabs; earlier model kept as a demo |
| v2 | 2026-11-09 | `space-v2-2026-11-09` | `6300e29` | | Restyled to the LipidLens visual identity: header, status strip, cream section titles, ruled tables, dot-and-interval chart for round 2, SCHEMATIC label, liposome illustration, dashed PREDICTED frames, footer. Styles moved to `src/style.css`. Models and predictions unchanged |
| v2.1 | 2026-11-09 | `space-v2.1-2026-11-09` | see the Space history | | Smoother scrolling: the full-width colour bands no longer make the page 5 px wider than the scroll area, the scroll area has an opaque background so the browser can scroll it on the GPU, and the liposome illustration is a 94 KB WebP instead of a 180 KB SVG with hundreds of gradients and a blur filter that was redrawn on every scroll frame |
| v2.2 | 2026-11-10 | `space-v2.2-2026-11-10` | see the Space history | | Fixes scrolling on huggingface.co, where the app sits in an iframe sized to its content. v2.1 set `overscroll-behavior: contain` on the scroll area, so after the 16 px it could scroll inside the iframe, the wheel never reached the outer page (70 wheel steps moved the page 15 px). The footer also stuck out 16 px below the content that Hugging Face measures. v2.2 removes the containment and pads the content by 16 px, so the iframe has nothing left to scroll and the wheel moves the page directly |

## Rolling back the Space

From a clone of the Space repository (`git clone https://huggingface.co/spaces/AliceSnack/lnp-formulation-predictor`):

```bash
git revert --no-edit 6300e29
git push origin main
```

This adds a new commit that restores v1 and keeps the history. Pushing needs a Hugging Face access token with write permission. The Space rebuilds in a few minutes.

To restore this folder on GitHub to v1 instead:

```bash
git checkout space-v1-2026-11-09 -- app/huggingface_space
git commit -m "Restore the Space to v1"
```

## Checks done before v2 was released

- The four model functions are unchanged, and the same inputs give the same output in v1 and v2 (144.5 nm, PDI 0.10, identical sensitivity table), checked with Streamlit's AppTest.
- Rendered locally with Streamlit 1.66.1: no server errors, no horizontal scrolling at 375 px width.
