# Strata 雙機本地模型：配置、測速與重現資料

2026-10-11 更新：桌機 9950X／4080 SUPER 16GB／32GB RAM，筆電 7945HX／4070 Laptop 8GB／32GB RAM，**兩機均已接交換器、有線 1Gbps**。保留完整 IQ3_XXS、IQ3_S，Strata 0.1.40.3＋NTR 雙機分層。

Measured deployment results, not upstream performance claims. No OS or power-mode changes were made.

## 最新：重新載入後的 512-token 驗證

中文／程式碼各 128-token 暖機後，每項實際生成 512 tokens **一次**；temperature 0、thinking off。這是單次觀測，不能標為三次中位數或保證每次對話都能達到。速度取引擎 `timings.predicted_per_second`，不含讀題。

| 模型 | 繁體中文 tok/s | 英文程式碼 tok/s | 桌機／筆電層數 | CPU 工作池：桌機／筆電 |
|---|---:|---:|---:|---:|
| IQ3_S | **52.6** | **51.7** | 36／12 | 15／15 |
| IQ3_XXS | **57.7** | **61.0** | 38／10 | 8／8 |

## 交錯短測與優化方式

在同一已載入引擎上，以推測解碼門檻 `0 / 0.5 / 0.5 / 0` 交錯比較。每階段每個工作排除 128-token 暖機，測一份 256-token 輸出；同門檻兩筆取中位數。這組和上面的 512-token 單次驗證分開列出。

| 模型 | 門檻 0：中文／程式碼 tok/s | 門檻 0.5：中文／程式碼 tok/s |
|---|---:|---:|
| IQ3_S | 42.8／55.3 | 50.7／57.4 |
| IQ3_XXS | 50.1／70.4 | 60.0／74.2 |

自動配置採用門檻 0.5，減少低信心草稿；最終 token 仍由完整目標模型驗證。IQ3_S 增加 CPU 專家 RAM 快取，RAM 調整階段的桌機實體讀取約 2971→1981 MiB；仍有檔案層讀取，沒有宣稱零 SSD。IQ3_XXS 各 8 個 CPU 工作執行緒加主工作執行緒，IQ3_S 各 15；沒有量測功耗，不能把工作執行緒減少直接當成節電百分比。

配置依當下兩台 RAM／提交容量挑選能承擔的已測候選；相同配置重用常駐模型。上下文上限仍為 IQ3_XXS 16384、IQ3_S 8192，INT8 KV、prefill 512、4-token MTP、GPU cache auto。GPU 快取命中在 GPU 算，未命中專家使用 CPU。GPU 優先／混合模式沒有在本輪勝出。不同日期、輸出長度、提示快取與專家快取的數字不能混合計算單項提升率。

- [完整配置、RAM／磁碟資料、測法與限制](docs/WIRED-OPTIMIZATION-2026-10-11.zh-TW.md)
- [機器可讀摘要](results/2026-10-11-wired-optimization/summary.json)
- [候選原始計時／容量資料](results/2026-10-11-wired-optimization/runtime-optimization.json)
- [512-token 自動配置驗證](results/2026-10-11-wired-optimization/auto-validation.json)
- [門檻交錯測試](results/2026-10-11-wired-optimization/mtp-abba.json)
- [兩模型桌機／筆電推理參數範例](config-templates/)、[通用測速與暖機工具](scripts/)

## 使用項目與公開範圍

核心：[Niko1221/Strata](https://github.com/Niko1221/Strata)。雙機分層：[NTRYourWaifu/Strata two-pc](https://github.com/NTRYourWaifu/Strata/tree/two-pc)，固定 commit `7add08dbd076f7f5fe897c76769064332450fe61`。模型：[ISTA-DASLab/Qwen3.8-Flash-Next-GSQ-RCO-GGUF](https://huggingface.co/ISTA-DASLab/Qwen3.8-Flash-Next-GSQ-RCO-GGUF)，固定 revision `ed59f92082b1e93c0e96d60a8b11aab089b52f09`。原始來源快照與第三方授權保留在 [sources/strata-two-pc](sources/strata-two-pc/)，本次沒有更新它。

模型分層資料走 LAN TCP 直連；SSH 只管理啟停與本機 API 轉接。兩機內部分別使用 CPU＋GPU，按層接力；效能不是把兩張卡跑分直接相加。桌機保存完整模型，筆電保存其可分配層的資料；全部模型專家仍保留。權重與編譯二進位不在本儲存庫。

分享內容僅限合成測試計時、必要硬體與記憶體數據、推理參數及既有通用測試工具。**不包含實際 IP／主機位址、電腦登入帳號、金鑰、私人聊天、存取控制／防火牆設定或本機部署管理腳本。** 參數範例不是一鍵安裝包；建立服務請依上游指南自行設定。

## 歷史結果

- [2026-10-10 較早的 Wi-Fi、512-token 三次中位數](docs/IQ3-TWO-PC-BENCHMARK-2026-10-10.zh-TW.md)：當時層數、記憶體配置與網路條件不同，原始結果保留於 [2026-10-10-iq3-comparison](results/2026-10-10-iq3-comparison/)。
- [更早的 Q2／llama.cpp 歷史快照](docs/HISTORICAL-SNAPSHOT-20261010.md)：不與最新表格直接排名。

上述短測不代表冷啟動、長上下文、多使用者或長期穩定值，也沒有進行品質評分／長時間熱負載測試。
