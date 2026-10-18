# LNP Formulation Predictor

AI驱动的脂质纳米粒(LNP)/脂质体配方性质预测平台。输入配方组成(四类脂质角色的摩尔百分比:可离子化脂质、辅助脂质、固醇、PEG脂质,加payload类型),预测粒径(nm)和PDI,并给出每个组分对预测结果的贡献拆解。

## 目录结构

- `HF_upload/` : 当前部署在Hugging Face Spaces上的Streamlit应用(模型+前端代码),是面向用户的生产版本
- `M5_streamlit_app/` : 更早版本的Streamlit应用,保留作历史参考
- `featurize_m3.py`、`merge_schema.py`、`train_m4.py`、`m4_experiments.py` 等 : 数据处理与建模脚本
- `ablate_fix_components_m6.py`、`fix_process_features_m6.py`、`verify_fix_m6.py`、`verify_process_confound_m6.py`、`shap_analysis_m6.py`、`m4b_stratification_test.py` : M6阶段(可解释性与精度诊断)相关的实验与验证脚本
- `M1_*.md` 到 `M6_*.md`、`M0-M5_专家批判与角色模拟_优化建议.md`、`LNP任务排期与迭代方案.md`、`部署步骤_HuggingFace.md` : 各阶段技术文档,按编号顺序读可以还原项目的技术演进过程
- `专利文献数据源调研报告.md`、`预印本数据搜索_进展记录_按数据形态.md` : 训练数据扩充的两条调研线(专利文献、预印本),记录了已核实可用/已核实不可用(及原因)的数据线索
- `*.csv`、`*.parquet`、`*.joblib` : 训练数据、特征矩阵、训练好的模型文件,以及各类验证/消融实验的结果
- `patent_candidate_formulations.csv`、`preprint_candidate_formulations.csv`、`rsc_nanoscale_sanofi_table1_reference_not_integrated.csv` : 候选扩充数据集,每一行都标注了核实状态(精确值/区间估计/暂不可用及原因),还没有并入主训练集

## 模型状态(截至2026-09-18的最近一次验证)

- 粒径预测:1,564个配方(LNP Atlas + 一个系统性微流控脂质体数据集 + 一个体外释放数据库),按论文来源分组交叉验证 R² = -0.135(这是诚实评估,随机切分会给出虚高但有误导性的数字,原因见M4/M6文档)
- PDI预测:1,275个配方(60篇文献),分组交叉验证 R² = -0.033,比粒径模型更不成熟
- 包封率(EE%):尚未建模。唯一有完整覆盖的数据来源是LNP Atlas单一来源,现阶段训练出来的会是"貌似三源、实际单源"的模型,所以暂缓
- 瓶颈判断:已测试并排除了几个假设(按脂质化学家族分层建模、显式给模型source_dataset特征),综合来看更像是样本量/数据多样性不足,而不是建模方法本身的问题,这也是对外联系实验室寻求数据合作的主要动机

## 说明

这个仓库只包含代码、训练数据、模型文件和技术文档。原项目文件夹里的个人文件(证件、签名、简历)和商务文件(基金申请草稿、外联邮件、合作意向书模板等)按要求不包含在内。
