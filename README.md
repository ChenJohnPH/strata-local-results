# Strata 雙機本地模型：配置、測速與重現資料

2026-10-10 更新：兩機 CPU＋GPU 分層已完成推理驗證，保留 IQ3_XXS、IQ3_S。桌機 Ryzen 9 9950X／RTX 4080 SUPER 16GB／32GB RAM；筆電 Ryzen 9 7945HX／RTX 4070 Laptop 8GB／32GB RAM。

Measured on Ubuntu + Windows with Strata v0.1.40.3 and the NTR two-PC extension. These are warmed, repeated-prompt benchmarks of deployed configurations, not upstream performance claims.

## 最新測速

每個負載三次、每次實際生成 512 tokens；temperature 0、thinking off。速度取引擎 `predicted_per_second`，不含讀題。暖機與快取狀態、分層／上下文差異已在報告明列。

| 模型 | 工作負載 | 中位數 tok/s | 三次範圍 tok/s | 請求耗時中位數 |
|---|---|---:|---:|---:|
| IQ3_XXS | 繁體中文說明 | **39.4** | 38.6–43.5 | 13.19 秒 |
| IQ3_XXS | 英文程式碼 | **46.0** | 44.0–47.8 | 11.31 秒 |
| IQ3_S | 繁體中文說明 | **37.4** | 36.0–41.4 | 13.89 秒 |
| IQ3_S | 英文程式碼 | **49.6** | 47.3–50.3 | 10.52 秒 |

- [完整配置、原理、測試方法與限制](docs/IQ3-TWO-PC-BENCHMARK-2026-10-10.zh-TW.md)
- [每次原始 timings、usage、合成輸出與硬體快照](results/2026-10-10-iq3-comparison/)
- [結構化測速摘要](results/2026-10-10-iq3-comparison/summary.json)
- [推理參數範例](config-templates/)、[合成測速與暖機工具](scripts/)
- [原始來源快照與授權](sources/strata-two-pc/)

## 使用項目

核心：[Niko1221/Strata](https://github.com/Niko1221/Strata)。雙機分層：[NTRYourWaifu/Strata two-pc](https://github.com/NTRYourWaifu/Strata/tree/two-pc)，固定 commit `7add08dbd076f7f5fe897c76769064332450fe61`。模型來源：[ISTA-DASLab/Qwen3.8-Flash-Next-GSQ-RCO-GGUF](https://huggingface.co/ISTA-DASLab/Qwen3.8-Flash-Next-GSQ-RCO-GGUF)。第三方授權保留在來源快照。

模型分層資料走 LAN TCP 直連，桌機有線、筆電 Wi-Fi；SSH 只負責管理與 API 本機轉接。桌機／筆電 IQ3_XXS 為 42／6 層、16K 上下文；IQ3_S 為 36／12 層、8K 上下文。兩機各 16 個參與執行緒，INT8 KV、4-token MTP 驗證，自適應 GPU 專家快取與 CPU 專家運算。

本次保留日常環境與原電源／系統設定。桌機仍有記憶體壓力及 swap，詳見快照；不宣稱完全零換頁、固定 60 tok/s 或長時間穩定性。桌機保存完整 GGUF，筆電稀疏檔只包含其可分配的層；所有模型專家仍完整保留。

此次分享只保留測速、硬體資料、推理參數與通用測試工具；電腦安全配置、部署管理腳本、實際 IP、帳號、金鑰與私人聊天均不納入。原始上游來源快照保留作來源參考。以前的 Q2／llama.cpp 測量保留為[歷史快照](docs/HISTORICAL-SNAPSHOT-20261010.md)，不能與本表不同條件直接比較。
