#!/usr/bin/env bash
# sync_from_project.sh
#
# Copies the whitelisted code/model/data/doc files from the parent project
# folder ("Liposome AI algorithm-圣草酚") into this repo folder
# (LNP-Formulation-Predictor), then commits any changes.
#
# This is a deliberate whitelist, not "copy everything new in the parent
# folder". The parent folder also holds personal documents (residence
# permit, signature, CV) and business documents (grant drafts, outreach
# emails) that must never end up in this git repo. Adding a new file to the
# sync just means adding its name to FILES or DIRS below.
#
# This script does NOT push on its own unless git already has credentials
# available. Run it, review `git status` / `git diff`, then `git push`
# yourself if it did not push automatically.
#
# Usage: bash sync_from_project.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DST="$SCRIPT_DIR"
SRC="$(dirname "$DST")"

if [ ! -d "$DST/.git" ]; then
  echo "error: $DST is not a git repo (expected .git here). Aborting." >&2
  exit 1
fi

FILES=(
  "AGENTS.md" "ablate_fix_components_m6.py" "featurize_m3.py" "fix_process_features_m6.py"
  "m4_experiments.py" "m4b_stratification_test.py" "merge_schema.py" "shap_analysis_m6.py"
  "train_m4.py" "verify_fix_m6.py" "verify_process_confound_m6.py"
  "部署步骤_HuggingFace.md" "M0-M5_专家批判与角色模拟_优化建议.md" "M1_LNP_Atlas_data_dictionary.md"
  "M2_合并总结.md" "M2_Luciani_data_dictionary.md" "M2_PMC_IVR_data_dictionary.md"
  "M3_特征工程说明.md" "M4_建模说明.md" "M6_可解释性与精度提升方案.md" "M6_独立验证_制备参数假设.md"
  "LNP任务排期与迭代方案.md" "专利文献数据源调研报告.md" "预印本数据搜索_进展记录_按数据形态.md"
  "LNP_Atlas_DB_202509_v1_utf8.csv" "PMC_IVR_lipid_component_smiles.csv"
  "merged_formulations.csv" "merged_formulations.parquet" "merged_formulations_v2.csv" "merged_formulations_v2.parquet"
  "feature_matrix.parquet" "feature_matrix_v2.parquet" "feature_matrix_sample.csv"
  "failed_smiles_log.csv" "status_summary.csv"
  "m4_model.joblib" "m4_feature_columns.joblib" "m4_cv_predictions.csv" "m4_cv_predictions_before_fix_archive.csv"
  "m4_experiments_results.csv" "m4_per_source_metrics.csv" "m4_per_source_metrics_before_fix_archive.csv"
  "m4_pdi_cv_results.csv" "m4b_stratification_results.txt"
  "fix_ablation_cv_results.csv" "fix_BC_only_cv_results.csv" "fix_verification_cv_results.csv" "fix_verification_eta_squared.csv"
  "process_feature_ablation_results.csv" "shap_feature_importance.csv" "shap_stability_check.csv" "step9_scaffold_cluster_feasibility.csv"
  "patent_candidate_formulations.csv" "preprint_candidate_formulations.csv" "rsc_nanoscale_sanofi_table1_reference_not_integrated.csv"
  # Add new whitelisted files above this line. One filename per line, matching
  # the name in the parent folder exactly.
)
DIRS=(
  "HF_upload"
  "M5_streamlit_app"
  # Add new whitelisted directories above this line.
)

echo "Syncing from: $SRC"
echo "Into:         $DST"
echo ""

MISSING=()
for f in "${FILES[@]}"; do
  if [ -f "$SRC/$f" ]; then
    cp "$SRC/$f" "$DST/$f"
  else
    MISSING+=("$f")
  fi
done

for d in "${DIRS[@]}"; do
  if [ -d "$SRC/$d" ]; then
    rm -rf "$DST/$d"
    cp -r "$SRC/$d" "$DST/$d"
  else
    MISSING+=("$d/")
  fi
done

if [ "${#MISSING[@]}" -gt 0 ]; then
  echo "warning: these whitelisted paths were not found in the parent folder (skipped):"
  printf '  %s\n' "${MISSING[@]}"
  echo ""
fi

cd "$DST"
git add -A

if git diff --cached --quiet; then
  echo "No changes to commit. Already in sync."
  exit 0
fi

echo "=== changes staged ==="
git diff --cached --stat

STAMP="$(date -u +%Y-%m-%d)"
git commit -q -m "Sync from project folder ($STAMP)"
echo ""
echo "Committed locally. Run 'git push' from this folder to update GitHub."

if git push 2>/tmp/sync_push_err.txt; then
  echo "Pushed to GitHub too. Nothing left to do."
else
  echo "(did not push automatically: $(cat /tmp/sync_push_err.txt | tail -1))"
  echo "Run 'git push' yourself to finish."
fi
