# Token Flow Scanner 项目计划

**目标**：3 月底交付可用的 Token 漏洞扫描器  
**节奏**：每日约 2 小时，可持续执行  
**当前**：2026 年 1 月下旬 → **截止**：2026 年 3 月 31 日  

---

## 一、时间与阶段总览

| 阶段 | 周期 | 总时长 | 主要产出 |
|------|------|--------|----------|
| 1. 漏洞分类与 Benchmark 设计 | 第 1–2 周 | ~10h | taxonomy、benchmark 名单、标注表头 |
| 2. Benchmark 精选与标注 | 第 3–4 周 | ~12h | 10–15 个合约的 multi-label + root cause + 负样本 |
| 3. Scanner 架构与 MVP | 第 5–6 周 | ~14h | 规则/LLM 管线、能跑通的初版 |
| 4. 评估与迭代 | 第 7–8 周 | ~12h | 按类型 recall/precision、hold-out、FP 报告 |
| 5. 文档与交付 | 第 9 周 | ~6h | 使用说明、benchmark 说明、示例输出 |

**合计**：约 54h 核心工作 + 缓冲，按 2h/天 × 5 天/周 ≈ 5–6 周可完成；留 2–3 周应对延期与打磨。

---

## 二、阶段 1：漏洞分类与 Benchmark 设计（第 1–2 周）

**目标**：敲定 taxonomy，确定 benchmark 候选名单与标注规范。

### 1.1 漏洞分类表（Taxonomy）—— 2 天 × 2h

- [ ] **D1**：起草 `taxonomy.md`  
  - 从 DeFiHackLabs / 审计报告摘出 10–12 个 Token 相关类型。  
  - 每类：ID、中文名、英文名、一句话定义、典型代码特征、1 个参考案例。  
  - 产出：`docs/taxonomy.md` 初稿。

- [ ] **D2**：评审并定稿 taxonomy  
  - 合并重叠类型，统一命名，确保与后续“按类型选 benchmark”一一对应。  
  - 产出：`docs/taxonomy.md` 定稿。

### 1.2 Benchmark 设计规范 —— 2 天 × 2h

- [ ] **D3**：编写 `BENCHMARK_SPEC.md`  
  - 正样本：每类型 1–2 个，优先有 PoC 的 `*_exp.sol`。  
  - 负样本：3–4 个“有 fee/reward 但实现正确”的合约或简化版。  
  - 多漏洞样本：1–2 个。  
  - Hold-out：固定 4–5 个只用于最终评估，不参与设计/调参。  
  - 产出：`docs/BENCHMARK_SPEC.md`。

- [ ] **D4**：从仓库筛选候选 + 建表  
  - 在 `src/test` 按 taxonomy 逐类找有 `_exp.sol` 的案例，填到 `benchmark_candidates.csv`（路径、类型、有否 PoC、可否做负样本、是否 hold-out）。  
  - 产出：`benchmark/benchmark_candidates.csv`。

### 1.3 标注表头与模板 —— 1 天 × 2h

- [ ] **D5**：  
  - 定义 `benchmark_labels.csv` 表头：`contract_path, vuln_types (多标签), root_cause_1line, has_poc, is_negative, is_holdout, notes`。  
  - 写一个 `annotation_template.md`，方便每天标注时复制。  
  - 产出：`benchmark/benchmark_labels.csv`（空表+表头）、`docs/annotation_template.md`。

**阶段 1 完成标准**：taxonomy 定稿、benchmark 名单落表、标注规范可执行。

---

## 三、阶段 2：Benchmark 精选与标注（第 3–4 周）

**目标**：完成 10–15 个合约的 multi-label 标注，且每个正样本有 root cause、PoC 可跑；负样本明确“为何安全”。

### 2.1 正样本标注（按类型轮流）—— 6 天 × 2h

按 `taxonomy` 顺序，每天专注 1–2 个合约，避免疲劳。

- [ ] **D6**：fee 类  
  - 例：`MTToken`、`futureswap`（或你选的同类型）。  
  - 跑通 `forge test`，写 root cause 一行，填 `vuln_types`。

- [ ] **D7**：deflationary / fee-on-transfer 类  
  - 例：`3913`、`MFT`、`NORMIE` 等中选 1–2 个。  
  - 同上：PoC + root cause + 多标签。

- [ ] **D8**：reward 类  
  - 例：`SWAPPStaking`、`LPMine`、`SorStaking`、`VTF` 等中选 1–2 个。  
  - 同上。

- [ ] **D9**：reentrancy / transfer-hook / 与 pair 的交互  
  - 例：`CAROL`、`MFT`、`PRXVT` 等中选 1–2 个。  
  - 同上。

- [ ] **D10**：arithmetic / oracle / slippage 等  
  - 例：`Truebit`、`yETH`、`NGP`、`DCFToken`、`Pump` 等中选 1–2 个。  
  - 同上。

- [ ] **D11**：查漏与多漏洞样本  
  - 确保 taxonomy 每类至少有 1 个；若有合约兼备多类，标成多标签。  
  - 选定 1–2 个“多漏洞”样本并标全。

### 2.2 负样本与 hold-out 划定 —— 2 天 × 2h

- [ ] **D12**：负样本  
  - 从仓库或自己写 3–4 个：正确 fee、正确 reward、或明确加固的 token。  
  - 在 `benchmark_labels.csv` 中标 `is_negative=1`，`vuln_types` 为空，`notes` 写“为何视为安全”。

- [ ] **D13**：hold-out 与交叉检查  
  - 在已标合约中选 4–5 个作 hold-out，在表中标 `is_holdout=1`。  
  - 快速过一遍：PoC 都能跑、标签与 taxonomy 一致、无重复编号。

**阶段 2 完成标准**：`benchmark_labels.csv` 填满，每个正样本有 PoC+root cause，负样本与 hold-out 明确。

---

## 四、阶段 3：Scanner 架构与 MVP（第 5–6 周）

**目标**：实现可运行的扫描管线，能对单个 `.sol` 输入产出“漏洞类型 + 位置 + 根因 + severity”的结构化结果。

### 3.1 技术选型与目录 —— 1 天 × 2h

- [ ] **D14**：  
  - 确定：纯 LLM / 规则+LLM 混合 / 是否用 slither 等做预处理。  
  - 定目录：如 `scanner/`（入口、规则）、`scanner/llm/`（prompt、调用）、`scanner/io/`（读 sol、写报告）。  
  - 产出：`scanner/README.md` 中的“架构说明”小节。

### 3.2 输入输出与跑通一例 —— 2 天 × 2h

- [ ] **D15**：  
  - 实现：读入 `path/to/xxx.sol`，可选 `--target contract名`。  
  - 输出：JSON 或 Markdown，含 `{vuln_type, location, root_cause, severity}`。  
  - 用 1 个 benchmark（如 MTToken）跑通 E2E，即使结果粗也可以。

- [ ] **D16**：  
  - 加上 `--benchmark-dir`：对 `benchmark/` 下列出的合约批量跑，结果落 `output/`。  
  - 产出：`scanner/run.sh` 或 `scanner/main` 的使用说明。

### 3.3 规则层（若采用混合架构）—— 3 天 × 2h

- [ ] **D17**：fee / balance 相关规则  
  - 如：检测 `sum(percentages)` 未与 100 比较、`balanceOf` 与 `amount` 混用、`SupportingFeeOnTransfer` 与 `balance` 假设。  
  - 输出与 LLM 同格式，便于合并。

- [ ] **D18**：reward / 时间与权限相关规则  
  - 如：`block.number`/`block.timestamp` 在 reward 公式中的危险用法、无 access control 的 fee/reward  setter。

- [ ] **D19**：规则与 LLM 的串联  
  - 规则先跑，结果作为“疑似”；LLM 只对疑似做确认与润色，或对全文件做补充。  
  - 保证对 MTToken、futureswap、至少 1 个 deflationary、1 个 reward 能产出有意义结果。

### 3.4 LLM 集成与 Prompt —— 3 天 × 2h

- [ ] **D20**：  
  - 选定 API（OpenAI/Claude/本地等），实现 `scanner/llm/client`。  
  - 将 `taxonomy.md` 压成“类型列表+简短定义”放进 system prompt。

- [ ] **D21**：  
  - 设计 user prompt：源码片段 + “请按给定类型列表，输出 JSON：vuln_type, location, root_cause, severity”。  
  - 用 2 个 benchmark 试跑，看格式是否稳定。

- [ ] **D22**：  
  - 加入 1–2 个 few-shot 例子（从已标 benchmark 抽），减少幻觉与格式漂移。  
  - 确保 ` severity` 与 taxonomy 或自定等级一致（如 H/M/L）。

**阶段 3 完成标准**：对 benchmark 目录能批量跑，输出结构化；规则（如有）与 LLM 已串联。

---

## 五、阶段 4：评估与迭代（第 7–8 周）

**目标**：按类型算 recall/precision，在负样本上算 FP，并在 hold-out 上做最终校验。

### 4.1 评估脚本 —— 2 天 × 2h

- [ ] **D23**：  
  - 实现 `eval/score.py`（或等价脚本）：读 `benchmark_labels.csv` 与 `output/` 下 scanner 结果。  
  - 按 `vuln_type` 匹配（允许字符串包含或标签集合相交），算每类型：TP/FP/FN，recall、precision、F1。  
  - 对 `is_negative=1` 的：若 scanner 报出任何 vuln 即计 FP。

- [ ] **D24**：  
  - 输出 `eval/report.md`：表格（类型 | Recall | Precision | F1 | 备注）。  
  - 加一节：负样本 FP 列表与 hold-out 上的汇总。

### 4.2 基于结果的迭代 —— 4 天 × 2h

- [ ] **D25**：  
  - 看哪些类型 recall 低：补规则或改 prompt（加该类型的描述/示例）。  
  - 重跑并刷新 `eval/report.md`。

- [ ] **D26**：  
  - 看哪些类型 precision 低（含负样本 FP）：收严规则或加“确认步骤”的 prompt。  
  - 再跑、再更新 report。

- [ ] **D27**：  
  - 做一次“仅在非 hold-out 上调参，最后在 hold-out 上只跑一次”的正式评估。  
  - 把 hold-out 结果写进 `eval/report.md`，标明“未参与调参”。

- [ ] **D28**：  
  - 若时间允许：加 1–2 个“仓库外”的 sol（同类型）做轻量泛化测试；否则只记录“后续可做”在 README。  
  - 冻结用于 3 月交付的 scanner 版本与 eval 结果。

**阶段 4 完成标准**：有可复现的 `eval/score` 与 `eval/report.md`，hold-out 与负样本结果明确。

---

## 六、阶段 5：文档与交付（第 9 周）

**目标**：使用方可按说明跑 scanner、理解 benchmark、解读输出。

### 5.1 使用说明与示例 —— 2 天 × 2h

- [ ] **D29**：  
  - 写 `token-flow-scanner/README.md`：安装依赖、环境变量（如 API key）、`run` 示例、`--help` 说明。  
  - 在 `examples/` 放 1–2 个 `xxx.sol` 及对应的 `expected_output.json` 或 `.md` 示例。

- [ ] **D30**：  
  - `benchmark/README.md`： taxonomy 摘要、如何跑 PoC、`benchmark_labels.csv` 字段说明、hold-out 与负样本名单。  
  - 确保 `forge test` 对 benchmark 中用到 `_exp.sol` 的都能跑（或在 README 中注明需要哪些 RPC/fork）。

### 5.2 交付清单与 3 月底收尾 —— 1 天 × 2h

- [ ] **D31**：  
  - 起草 `DELIVERABLES.md`：可执行入口、benchmark 目录、`docs/taxonomy.md`、`eval/report.md`、README。  
  - 自测：clone 新目录、按 README 安装并跑 1 个 example + 1 个 benchmark，记录通过。  
  - 若没问题，在计划中标注“3 月交付完成”；若有小缺陷，列到“后续迭代”清单。

**阶段 5 完成标准**：外人可按 README 跑通 scanner 和评估，交付物清单清晰。

---

## 七、每周节奏建议（按 2h/天）

- **工作日**：尽量固定 2h 时段（如晚 8–10 点），完成 1 个 D 的 checkbox；若某天只完成一半，下一日优先补完再开新 D。  
- **单次 2h 拆解**：  
  - 前 10–15 分钟：看 `PLAN.md` 和昨日笔记，进入上下文。  
  - 中间 1.5h：执行当天任务。  
  - 最后 10–15 分钟：更新 checkbox、写 1–3 行“今日结论/卡点”在 `logs/daily_YYYYMMDD.md`（可自建）。  
- **若某 D 超 2h**：不强行收尾；把“未完成子项”记到该 D 下，第二天优先做完。  
- **若提前完成某阶段**：用富余时间做：多 1 个负样本、多 1 个 rule、或补 `docs/` 里想写的小结。

---

## 八、风险与缓冲

| 风险 | 缓解 |
|------|------|
| 某类漏洞在仓库中找不到合适 PoC | 在 taxonomy 中暂时标为“待补”，先保证其它类型覆盖；或从 CVE/审计报告找摘要当“静态标注”延后 PoC。 |
| LLM API 限制或不可用 | 在 D14、D20 确定备用方案（本地模型 / 另一家 API），MVP 先跑通一家。 |
| 评估脚本与标签格式对不齐 | D23 先做 2 个合约的手动对齐示例，再推广到全表。 |
| 2h 经常被压缩 | 阶段 2、3 中部分 D 可拆成 2 天各 1h；阶段 4、5 的 D27–D31 可各放宽到 2.5h，从前面缓冲挪一点。 |

---

## 九、目录结构（建议）

```
token-flow-scanner/
├── PLAN.md                 # 本计划
├── README.md               # 使用说明（阶段 5 完善）
├── DELIVERABLES.md         # 交付清单（阶段 5）
├── docs/
│   ├── taxonomy.md         # 漏洞分类（阶段 1）
│   ├── BENCHMARK_SPEC.md   # benchmark 设计规范（阶段 1）
│   └── annotation_template.md
├── benchmark/
│   ├── README.md
│   ├── benchmark_candidates.csv
│   ├── benchmark_labels.csv
│   └── (若需要可放复制的 sol 或符号链接)
├── scanner/
│   ├── README.md           # 架构说明
│   ├── main.py 或 run.sh   # 入口
│   ├── rules/              # 若做规则层
│   ├── llm/                # prompt、client
│   └── io/
├── eval/
│   ├── score.py
│   └── report.md
├── examples/
│   └── (示例 sol + expected 输出)
└── logs/                   # 可选：每日简要
    └── daily_YYYYMMDD.md
```

---

## 十、检查点（方便你自检进度）

- **第 2 周末**： taxonomy + `BENCHMARK_SPEC` + `benchmark_candidates.csv` 完成。  
- **第 4 周末**： `benchmark_labels.csv` 写满，负样本与 hold-out 定好，PoC 可跑。  
- **第 6 周末**： scanner 对 benchmark 能批量跑并产出结构化结果。  
- **第 8 周末**： `eval/report.md` 就绪，hold-out 与负样本评估完成。  
- **第 9 周末**： README、DELIVERABLES、自测通过，可交付。

---

**计划版本**：v1  
**最后更新**：2026-01  

---

## 如果从今天开始

- **D1**：`docs/taxonomy.md` 已有初稿（约 12 类），你可直接审阅、删并或增补，省下从零起草时间；定稿留到 D2。
- **D3**：创建 `docs/BENCHMARK_SPEC.md`；D4 在 `src/test` 中按 taxonomy 搜 `*_exp.sol`，往 `benchmark/benchmark_candidates.csv` 填空。
- **每日**：在 `logs/daily_YYYYMMDD.md` 记 1–3 行「今日结论/卡点」，方便隔天接上。

目录 `token-flow-scanner/`、`docs/`、`benchmark/`、`logs/` 已建好，`benchmark_labels.csv` 与 `annotation_template.md` 可直接用。
