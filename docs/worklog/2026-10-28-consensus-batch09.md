# 第 9 批工作日志：G 北欧合作方，换工具后零额度完成（2026-10-28）

## 一句话

原定给 G 的约 120 次 Consensus 检索**一次没用**，
因为换成 PubMed 后这件事不需要语义检索，而且结果更准（单位是硬字段，不是猜的）。

## 做了什么

1. 先试 OpenAlex（用户原计划里的方案），**本环境网络策略拒绝该域名**（CONNECT 403）。
2. 改试 PubMed E-utilities 与 Crossref，两者都可达。选 PubMed，因为它的 `[ad]` 字段
   直接检索作者单位，且返回的 XML 里每位作者都带完整单位字符串与通信邮箱。
3. 写了三个可复用脚本并入库（`scripts/pubmed_nordic_scan.py`、
   `pubmed_nordic_analyze.py`、`pubmed_nordic_people.py`）。
4. 6 条检索式，解析 1478 条记录、3351 个北欧单位作者条目。
5. 产出写入 `docs/validation-partners.md`，并新增 17 行到主表。

## 一个必须记下来的差错

第一版解析脚本取 DOI 时用了 `art.iter("ArticleId")` 并在循环里反复赋值，
结果取到的是**参考文献列表里最后一个 DOI**，不是论文本身的 DOI。
现象是标题与 DOI 明显不匹配（例如 2022 年的脂质纳米粒论文配了一个 1999 年的
Biomaterials DOI）。发现后改为只读 `PubmedData/ArticleIdList` 下的第一个 DOI
并重新取回全部记录。**没有把错误 DOI 写进任何仓库文件。**

教训：PubMed 的 efetch XML 在 `ReferenceList` 里也带 `ArticleId` 元素，
用 `iter()` 做全树遍历会把参考文献混进来。

## 最有价值的发现

**本项目脑递送证据里最关键的两个定量结果，出自同一个北欧课题组。**

Uppsala 的 Margareta Hammarlund-Udenaes 与 Irena Loryan 组：

- 是 Kp,uu,brain 这个概念与脑切片法、脑微透析方法学的源头
- 是甲氨蝶呤 GSH-PEG 脂质体 Kp,uu 系列（10.1016/j.ejpb.2019.04.004）的作者组
- 也是「苯海拉明包封进 PEG 脂质体后 Kp,uu 从 3.0 降到 1.5」
  （10.1021/acs.molpharmaceut.8b00611）这条关键反向证据的作者组

而我们在 `docs/brain-delivery-evidence.md` 里恰好标出了该组两篇论文之间
一处约 5 倍的 Kp,uu 差异需要澄清（2017 年报 0.28 到 0.32，2019 年报 1.5）。
这给了一个具体、有专业含量、对方有动机回答的接洽理由，
比泛泛发询价信的命中率高得多。建议第一封信就发给这一组。

## 其他三个高价值匹配

| 组 | 为什么 |
|---|---|
| KTH 与 Karolinska 的 Anna Herland 组 | **一人同时跨四类检索**：脂质纳米粒加人源 BBB 芯片加星形胶质细胞三维培养 |
| Aalborg 的 Torben Moos 与 Maj Schneider Thomsen 组 | 转铁蛋白受体靶向纳米粒加血脑屏障体内外模型加跨物种体外 BBB 比较 |
| UiT 的 Nataša Škalko-Basnet 组 | 已有「系统改脂质体组成同时测包封、粒径、zeta、稳定性」的现成工作流，与我们要的数据结构完全一致，而且做过多酚类载荷 |

## 如实记下的三条限制

1. **各组是否用认证参考物质校准粒度仪，全部未核实。**
   PubMed 元数据不含正文方法部分。唯一的间接线索是 DTU National Food Institute
   的 Loeschner 组有公开的 CRM 评价工作。其余只能靠询价问出来。
2. **单位以论文所列为准，当前单位可能已变。** 已发现两例不一致并在文件里标出。
3. **一作或末位作者篇数只是课题组负责人的粗代理**，PubMed 的 XML 不单独标注通信作者。

## 下一步

1. 成本与周期专项（约 40 次 Consensus，低预期），零命中即如实记录「文献无答案，需直接询价」。
2. 四项剩余零额度任务：核实 LNPDB 小分子占比、Zenodo/Figshare 脚本、
   135 篇需全文论文的获取清单（脑递送优先）、更新 `docs/next-actions.md`。
3. 最终五项产出汇总。
