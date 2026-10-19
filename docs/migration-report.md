# 迁移审计报告

日期：2026-10-19
范围：对照任务文档"第一步：迁移"的检查清单逐项核实。

## 仓库实际来源说明

这个仓库不是从另一个云端账号迁移过来的。实际过程是：在这次会话里，直接从你电脑上的工作文件夹(`A:\Claude\Liposome AI algorithm-圣草酚`)按白名单挑出代码/模型/数据/文档子集，复制进这个仓库文件夹，建的本地git仓库，首次提交由你自己在PowerShell里`git push`推上去的。白名单明确排除了所有个人文件（身份文件、CV）和商业文件（融资材料、外联邮件等）。记录这一点是因为任务文档里写的"迁移自另一个云端账号"和实际历史不一致，怕以后回头看记录对不上。

## 1. 密钥/敏感信息扫描

扫描范围：当前工作区全部跟踪文件 + 完整git历史(`git log --all -p`)，匹配常见密钥模式(api_key/token/password/AWS key/OpenAI风格key/GitHub token/私钥文件头等)，另外单独检查了`.env`、`.pem`、`.key`、`credential`等敏感文件名。

结果：零命中。没有密钥需要转成环境变量，不需要`.env.example`。

## 2. 大文件 / Git LFS

仓库总大小29MB（`.git`占2.4MB），最大单文件`feature_matrix_sample.csv`15.38MB，其余均在2MB以下。远低于GitHub的100MB硬限制，也低于常见的50MB预警线。

结论：不需要Git LFS。

## 3. 依赖安装测试

在全新环境(Python 3.10.12, Ubuntu 22.04, 全新venv)分别测试两份requirements.txt：

- `M5_streamlit_app/requirements.txt`（版本锁定：streamlit 1.38.0 / pandas 2.3.3 / numpy 2.2.6 / scikit-learn 1.7.2 / rdkit 2024.3.5 / joblib 1.5.3）：安装成功，全部import成功，版本号与锁定完全一致。
- `HF_upload/requirements.txt`（版本不锁定，除scikit-learn==1.7.2外）：安装成功，全部import成功。

## 4. 已修复：5个脚本的硬编码路径

发现`ablate_fix_components_m6.py`、`fix_process_features_m6.py`、`verify_fix_m6.py`、`verify_process_confound_m6.py`、`m4b_stratification_test.py`这5个脚本里硬编码了旧云端会话的绝对路径（`/mnt/user-data/uploads/...`或已失效的`/sessions/charming-focused-tesla/...`），在这个仓库或任何新环境下都无法运行。

已修复为相对脚本自身目录的路径（`os.path.dirname(os.path.abspath(__file__))`）。确认过diff只改了路径常量和新增`import os`，没有改任何计算逻辑。

`merge_schema.py`也有4处类似硬编码路径，但加了说明注释后发现即使修好路径也跑不通：它依赖3个原始源文件（LNP_Atlas原始CSV、Luciani CSV、PMC_IVR sqlite数据库），这3个文件从未被纳入本仓库的迁移白名单（之前的会话已记录"当前环境下不可访问"）。这个脚本目前只能作为合并逻辑的历史记录看，不是可运行脚本。

## 5. 结果复现测试

路径修复后，重新跑了以下脚本并核对关键数字：

| 脚本 | 核心数字 | 对照结果 |
|---|---|---|
| verify_fix_m6.py | ALL分组CV R²=-0.135388 | 与项目里反复引用的"R²=-0.135"精确对上 |
| ablate_fix_components_m6.py | baseline ALL R²=-0.135388 | 同上，精确对上 |
| verify_process_confound_m6.py | WITH process features R²=-0.135388；WITHOUT=-0.043725 | 都对上，且WITHOUT的历史交叉核对数字(文档记录R²=-0.044)精确对上 |

结论：**仓库里公开引用的核心结果(R²=-0.135)在全新环境下精确复现，不是只有数量级对、小数点都对上了。**

### 一个已知、未掩盖的复现缺口

上面几个脚本内部都设计了"修复前 vs 修复后"对比（比如verify_fix_m6.py的BEFORE_fix/AFTER_fix两行）。重新跑的时候，BEFORE和AFTER现在算出来是同一个数字，而仓库里原来commit的BEFORE行是真实不同的历史数字（比如verify_fix_m6.py旧commit里BEFORE ALL R²=-0.000318，这次重跑是-0.135388）。

原因：这几个脚本的输入`feature_matrix.parquet`现在已经是"修复后"的版本（仓库里没有单独保留"修复前"的快照），所以脚本没有真正的"before"状态可比了。**这不是代码逻辑问题**——已经核对过，这次改动只动了路径常量；是历史数据快照没有被单独保留下来。

处理方式：没有用重新跑出来的结果覆盖仓库里原来的`fix_verification_cv_results.csv`、`fix_verification_eta_squared.csv`、`feature_matrix_v2.parquet`、`fix_ablation_cv_results.csv`、`process_feature_ablation_results.csv`，这几个文件保持原样，历史对比数字还在里面。重新跑的结果只用于核实"AFTER/最终"这一半是否复现，没有写回仓库。

`m4b_stratification_test.py`路径修好了，但单次运行超过170秒没跑完，这次没有强行跑完，只做了路径修复，没有做完整复现验证。它是辅助诊断脚本，前面表格里三个核心复现指标都不依赖它。

`train_m4.py` / `m4_experiments.py` / `shap_analysis_m6.py` 本来用的就是相对路径（相对运行目录），没有改动，属于一直可运行的。

## 6. 新发现：模型文件和依赖锁定版本不一致

加载`m4_model.joblib`时sklearn报`InconsistentVersionWarning`：这个模型文件是用scikit-learn 1.8.0存的，但`M5_streamlit_app/requirements.txt`锁定的是1.7.2。目前只是警告，不是报错，能正常加载和推理。

这个不一致是迁移之前就存在的（说明原项目训练模型和跑验证脚本时用的sklearn版本本身不一致），不是这次迁移改动引入的。我没有改requirements.txt的版本锁定，也没有重新训练覆盖模型文件——要不要把锁定版本改成1.8.0，这个决定留给你。

## 7. 自动推送

这次没能搭成功GitHub自动推送（过程中出过一次失误，已经在对话里跟你说明、你也已经撤销了两次误授权的OAuth权限）。目前推送机制维持原状：我commit，你在PowerShell里手动`git push`。

## 新环境下怎么跑这个项目

```bash
git clone https://github.com/SiyaoGui/LNP-Formulation-Predictor.git
cd LNP-Formulation-Predictor
python3 -m venv venv && source venv/bin/activate
pip install -r M5_streamlit_app/requirements.txt   # 或 HF_upload/requirements.txt
python3 verify_fix_m6.py      # 复现核心CV结果
python3 train_m4.py           # 重新训练(会覆盖m4_model.joblib，一般不需要跑)
streamlit run M5_streamlit_app/app.py   # 跑本地demo
```
