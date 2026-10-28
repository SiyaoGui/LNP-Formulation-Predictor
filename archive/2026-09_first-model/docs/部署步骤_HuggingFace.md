# 部署到 Hugging Face Spaces —— 15分钟流程

不需要 GitHub，不需要命令行，全程浏览器操作。

## 要上传的文件（都在 `M5_streamlit_app` 文件夹里）

```
app.py
requirements.txt          ← 已更新，版本已锁定
README.md                 ← 已重写，含配置头
lipid_lookup.json
m4_model.joblib
m4_feature_columns.joblib
```

六个文件，总共约 430 KB。

---

## 步骤

**1. 注册 / 登录**
https://huggingface.co/join —— 邮箱注册，1分钟。

**2. 创建 Space**
右上角头像 → **New Space**，填：

| 字段 | 填什么 |
|---|---|
| Space name | `lnp-formulation-predictor` |
| License | `mit` |
| **SDK** | **Streamlit** ← 别选错 |
| Hardware | CPU basic (free) |
| Visibility | **Public** ← 必须公开，评审才能打开 |

点 Create Space。

**3. 上传文件**
进入 Space 后点 **Files** 标签 → **Add file** → **Upload files**
把上面六个文件**全部拖进去**（可以一次全选），下面 Commit message 随便写，点 **Commit changes to main**。

⚠️ README.md 会覆盖 HF 自动生成的那个，这是对的——我们的版本里有配置头（`sdk: streamlit`、`app_file: app.py`）。

**4. 等构建**
回到 **App** 标签，右上角会显示 *Building*。第一次装 rdkit 比较慢，**3–8分钟**。
构建完变成 *Running*，页面就出来了。

**5. 拿到网址**
形如：`https://huggingface.co/spaces/<你的用户名>/lnp-formulation-predictor`

---

## 如果构建失败

点 **Logs** 看报错，最常见两种：

**`ModuleNotFoundError: No module named 'rdkit'`**
→ 把 requirements.txt 里的 `rdkit==2024.3.5` 改成 `rdkit-pypi`，重新提交。

**joblib / sklearn 版本警告或报错**
→ 模型是用 scikit-learn 1.7.2 训练的，requirements.txt 已经锁死这个版本。如果 HF 说找不到该版本，改成 `scikit-learn` 不带版本号，通常仍能加载（可能有警告，不影响运行）。

---

## 部署成功之后

**1. 截图**（输入一个配方 → 显示预测结果那一屏），发给我，我加成附录第4页。

**2. 网址加进申请**。执行质量第二题的 Status 那句可以改成：

> ...gradient-boosted models; a working web demo at 【网址】.

这一句让评审能**直接点开验证**，比任何描述都有力。

---

## 时间判断

**如果20分钟内没跑起来，就停。** 截一张本地运行的图，或者干脆维持现在的三页附录。

申请正文和附件都已经完成，这一步是加分项不是必需项——**按时提交远比多一个网址重要**。
