# 雙機有線模型優化（2026-10-11 完成）

測試於 2026-10-10 至 2026-10-11 進行；當下可用容量會影響自動選擇，兩次測試日期的環境負載可能不同。

已將有線環境的實測配置存入自動分配。保留完整 IQ3_XXS／IQ3_S 模型、原本上下文與 INT8 KV；只改模型應用程式，沒有更改系統設定、電源模式、網卡、防火牆或分頁檔。測試完成後恢復模型「無」、卸載兩台模型，網頁仍可使用。

## 硬體與引擎

- 桌機：Ubuntu 22.04.5、Ryzen 9 9950X、RTX 4080 SUPER 16GB、32GB RAM。
- 筆電：Windows、Ryzen 9 7945HX、RTX 4070 Laptop 8GB、32GB RAM（2×16GB，配置 4800 MT/s）。
- 兩台接同一交換器，連線為 1Gbps；模型分層資料直接走 LAN TCP。SSH 用於啟停與本機 API 轉接。
- Strata 0.1.40.3，已部署來源為 [NTRYourWaifu/Strata 的雙機分支](https://github.com/NTRYourWaifu/Strata/tree/two-pc)，固定來源提交 `7add08d`；專家核心與模型推論來自 [Niko1221/Strata](https://github.com/Niko1221/Strata)。

## 相同提示與輸出長度的 256-token 短測

中文科普、英文程式碼各先排除 128-token 暖機，再取兩次 256-token 生成的中位數。溫度 0、思考關閉；使用引擎 `timings.predicted_per_second`，不把 prompt tokens 計入輸出速度。提示很短，不是 4K 長提示測試。IQ3_S 最後確認在交錯測試後的熱模型上執行，快取狀態與原配置不同；下表是候選數據的比較，不是嚴格同快取 A/B。門檻的單項效果應看文末交錯測試，重新載入後的實際輸出看 512-token 驗證。

| 模型 | 原配置中文 | 自動採用配置中文 | 原配置程式碼 | 自動採用配置程式碼 | 綜合變化 |
|---|---:|---:|---:|---:|---:|
| IQ3_S | 37.9 | 51.6 | 53.0 | 64.8 | +29.1% |
| IQ3_XXS | 54.0 | 59.2 | 70.3 | 70.1 | +4.5% |

單位均為 tok/s；綜合變化使用兩項速度的幾何平均。每項只有兩次，不能視為長期穩定值；小於 5% 的速度差可能是波動。較少 CPU 工作執行緒代表可用工作數減少，不等於已測得固定功耗下降。

## 自動採用的配置

| 模型 | 桌機／筆電層數 | CPU 專家 RAM 預算 GiB | 桌機／筆電 CPU 工作池 | 顯存預留 MiB | context 上限 |
|---|---:|---:|---:|---:|---:|
| IQ3_S | 36／12 | 23.25／5.75 | 15／15 | 640／640 | 8192 |
| IQ3_XXS | 38／10 | 20.75／5.25 | 8／8 | 800／800 | 16384 |

快取命中的專家由 GPU 計算，未命中的專家使用 CPU（`pcie_frac=0`）；GPU 優先／混合配置沒有在這輪勝出。每台另有主工作執行緒。保留 GPU cache auto、prefill 512、spec 4、suffix draft 0；IQ3_S 試用的 `STRATA_FILE_RELEASE=1` 僅在模型程序中釋放可重新讀取的映射頁面，不減少模型內容，也不更改系統環境變數。

## 磁碟與容量

- IQ3_S：桌機引擎實體儲存讀取 2971 → 1981 MiB；測試最小餘量：桌機 RAM 2.22、筆電 RAM 9.08、筆電提交容量 2.04 GiB。
- IQ3_XXS：桌機引擎實體儲存讀取 157 → 114 MiB；測試最小餘量：桌機 RAM 5.32、筆電 RAM 11.44、筆電提交容量 7.47 GiB。

實體讀取是受管理 Strata 程序群 `/proc/<pid>/io` 的 `read_bytes` 差值，涵蓋兩項 128-token 暖機與四次正式短測；不能等同專家檔案層的邏輯讀取，亦不是整機磁碟總量。IQ3_S 仍會使用檔案層，這次沒有消除全部磁碟讀取。初期 JSON 中未標註 `request_scope` 的 `requests` 含暖機資料，只作診斷，不作四次正式測試的總量。

自動模式每次套用先看當下兩台可用 RAM、筆電提交容量及模型能回收的記憶體，再挑能承擔的已測配置。保留至少約 1.75 GiB 提交容量／桌機 RAM 與 2 GiB 筆電 RAM 的規劃餘量；正式候選另要求短測桌機 RAM 至少 2 GiB。其他程式佔用增加時會回退到較低 RAM 預算或其他安全分層，不強行使用最快那組。不是逐 token 改分層，也不在每次使用時執行完整測速。

## 較長輸出與啟停驗證

自動模式重新載入兩模型，各自先生成中文／程式碼各 128 tokens 暖機，再以各一份 512-token 輸出核對。此處每項只有一次，輸出長度也不同，與上表分開列出，不拿來計算上表提升率。

| 模型 | 中文 512-token 生成 | 程式碼 512-token 生成 |
|---|---:|---:|
| IQ3_S | 52.6 | 51.7 |
| IQ3_XXS | 57.7 | 61.0 |

已核對自動選中的層數、RAM 預算、CPU 工作池、GPU 分派、prefill 與顯存預留實際傳入兩台；相同配置再次啟動會保留原模型程序，不重新載入。模型卸載與按需監控狀態也已核對；本機程序管理實作不在公開範圍。

## 使用

開啟 `http://localhost:8080/`，選 IQ3_XXS 或 IQ3_S，保持「自動平衡」。等載入與 128-token 暖機完成即可對話；要釋放資源選「無」或「卸載模型」。監控維持按需啟用，點「開啟雙機監控」才開始讀取兩台效能／程序。

## 證據與限制

- [runtime-optimization.json](../results/2026-10-11-wired-optimization/runtime-optimization.json)：全部合成短測、容量快照、候選與拒絕紀錄。
- [auto-validation.json](../results/2026-10-11-wired-optimization/auto-validation.json)：自動配置、512-token 輸出計時與原程序重用驗證。
- [公開推理參數範例](../config-templates/)：兩模型的桌機／筆電參數；本機配置備份不公開。
- [功能驗證摘要](../results/2026-10-11-wired-optimization/final-state.json)：自動配置、容量餘量、模型重用與卸載確認；本機管理／安全驗證程式不公開。

保留兩模型完整版。短提示、思考關閉的生成速度不代表長上下文、思考開啟或所有聊天的固定速度；沒有進行品質評分、持續熱負載或大量併發測試。此公開版本不含私人對話、金鑰、實際網路位址或存取安全配置。

## 推測解碼門檻交錯短測

透過 Strata 引擎內建 `strata_tune` 請求參數，以門檻 0／0.5／0.5／0 順序測試；每個階段的兩項工作各排除 128-token 暖機，再生成 256 tokens。兩次相同門檻取中位數；要求綜合提升超過 5%、各項退步不超過 5% 才加入候選。這次測試用已暖機引擎，磁碟數據與剛載入時的 RAM 測試不能直接比較，前述磁碟改善只使用 RAM 調整階段的同類短測。

| 模型 | 門檻 0 中文／程式碼 | 門檻 0.5 中文／程式碼 | 自動配置實際門檻 |
|---|---:|---:|---:|
| IQ3_S | 42.8／55.3 | 50.7／57.4 | 0.5 |
| IQ3_XXS | 50.1／70.4 | 60.0／74.2 | 0.5 |

IQ3_XXS 在 10 日的確認階段因當時容量不足未採用；11 日重新載入確認後，中文／程式碼各兩次 256-token 中位數為 59.2／70.1 tok/s，最小桌機 RAM／筆電 RAM／筆電提交餘量為 5.32／11.44／7.47 GiB，通過容量檢查後加入自動候選。

證據：[mtp-abba.json](../results/2026-10-11-wired-optimization/mtp-abba.json) 及 [runtime-optimization.json](../results/2026-10-11-wired-optimization/runtime-optimization.json) 的 `mtp05-confirm-resumed`。推測解碼門檻只控制草稿鏈長度，不減少模型層數；最終 token 仍由完整目標模型驗證。

## 公開重現方法

先依前述上游雙機指南啟動自己的 Strata 服務，使用 `config-templates/` 的推理參數；自行設定端點與憑證，這個結果儲存庫不提供本機部署腳本。完整專家模型仍保留，兩台以分層接力運行。

固定同一模型、提示、溫度與思考設定，先暖機，再測速；切換模型需由自己的服務完成，不要只修改請求中的模型名稱。以下使用通用、既有的公開測速工具：

```powershell
python scripts/warmup-model.py --url http://localhost:8080 --model qwen3.8-flash-next-iq3_xxs --key-file path/to/local-api-key.txt --tokens 128
python scripts/bench-speed.py warm --kind prose --tokens 128 --runs 1 --model qwen3.8-flash-next-iq3_xxs --key-file path/to/local-api-key.txt --spec-min-p 0.5
python scripts/bench-speed.py measured --kind prose --tokens 256 --runs 2 --model qwen3.8-flash-next-iq3_xxs --key-file path/to/local-api-key.txt --spec-min-p 0.5
python scripts/bench-speed.py validation --kind prose --tokens 512 --runs 1 --model qwen3.8-flash-next-iq3_xxs --key-file path/to/local-api-key.txt --spec-min-p 0.5
```

程式碼使用 `--kind code`；IQ3_S 使用對應的模型名稱。門檻交錯測試依 `0 / 0.5 / 0.5 / 0` 順序執行，每個階段對兩個工作各先排除 128-token 暖機，再測一筆 256-token 輸出。這可在同一已載入引擎內進行；比較 CPU 工作池、層數或 RAM 預算則需要重新載入。

通用工具只寫入自行發起的合成測試輸出，不讀取瀏覽器歷史。若自行公開檔案，也應先檢查是否含私密資訊。機器可讀摘要：[summary.json](../results/2026-10-11-wired-optimization/summary.json)。10 日較早的 Wi-Fi 測試仍保留於[舊報告](IQ3-TWO-PC-BENCHMARK-2026-10-10.zh-TW.md)，條件不同，不用來計算這次單項優化的提升率。
