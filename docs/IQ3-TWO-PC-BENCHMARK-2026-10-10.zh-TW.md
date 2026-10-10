# IQ3 雙模型實測：9950X＋4080 SUPER、7945HX＋4070 Laptop

測試日期：2026-10-10（Asia/Taipei）。實際運行的是 Strata v0.1.40.3＋NTR two-pc 擴充。This is a user deployment benchmark, not an upstream performance claim.

## 速度

| 模型 | 工作負載 | 中位數 tok/s | 三次範圍 tok/s | 請求耗時中位數 |
|---|---|---:|---:|---:|
| IQ3_XXS | 繁體中文說明 | **39.4** | 38.6–43.5 | 13.19 秒 |
| IQ3_XXS | 英文程式碼 | **46.0** | 44.0–47.8 | 11.31 秒 |
| IQ3_S | 繁體中文說明 | **37.4** | 36.0–41.4 | 13.89 秒 |
| IQ3_S | 英文程式碼 | **49.6** | 47.3–50.3 | 10.52 秒 |

每次實際輸出 512 tokens；每格三次。速度取 API `timings.predicted_per_second`，是引擎生成速度；請求耗時另含提示處理與 HTTP／轉接開銷。暖機結果不混入中位數。這些是暖機後、重複提示的短測，不能代表冷啟動、長上下文、多使用者、所有文章或長時間平均。

## 硬體與軟體

| 項目 | 桌機 | 筆電 |
|---|---|---|
| CPU | Ryzen 9 9950X，16C/32T | Ryzen 9 7945HX，16C/32T |
| GPU | RTX 4080 SUPER，16GB | RTX 4070 Laptop，8GB |
| RAM | 32GB，頻率／通道配置本報告未額外確認 | 32GB，2×16GB DDR5，ConfiguredClockSpeed 4800 |
| SSD | 2TB＋1TB，實際 SSD 型號未記錄 | 2TB＋1TB，實際 SSD 型號未記錄 |
| OS | Ubuntu 22.04.5 LTS | Windows 11 Home，10.0.26200 |
| 網路 | 有線 1Gbps | Wi-Fi |
| 編譯環境 | CUDA 12.4，Release，sm89 | CUDA 12.6，Release，sm89 |

本次不調整系統、電源模式、CPU governor、驅動或分頁檔。桌機 governor 保持 powersave，筆電維持既有 OEM Performance。背景環境沿用日常配置，沒有為測速清空所有應用程式。硬體 JSON 是測試附近的時間點快照，GPU 利用率／時脈不是整段平均，也不能用其中的低時脈推斷生成時降頻。

## 模型與分層

兩模型均為 Qwen3.8-Flash-Next GSQ-RCO 的完整專家模型；IQ3_XXS、IQ3_S 是不同量化。模型來源：[ISTA-DASLab/Qwen3.8-Flash-Next-GSQ-RCO-GGUF](https://huggingface.co/ISTA-DASLab/Qwen3.8-Flash-Next-GSQ-RCO-GGUF)，下載固定 revision `ed59f92082b1e93c0e96d60a8b11aab089b52f09`。

| 設定 | IQ3_XXS | IQ3_S |
|---|---|---|
| 桌機／筆電層數 | 42／6，筆電含輸出頭 | 36／12，筆電含輸出頭 |
| 上下文上限 | 16384 | 8192 |
| 桌機 CPU 專家 RAM 預算 | 24 GiB | 24.5 GiB |
| 筆電 CPU 專家 RAM 預算 | 7.25 GiB | 8.25 GiB |

共同配置：兩機各 15 workers＋1 host；桌機 host-core first、筆電 last；GPU 專家快取 auto；VRAM 分配預留 800 MiB；CPU allocator headroom 1.25 GiB；INT8 KV、prefill 512、spec 4、spec-min-p 0.5、pcie-frac 0、suffix-draft 0；檔案 tier 使用 OS 緩衝。預留參數不是載入後剩餘 RAM／VRAM 的保證。

分層與上下文沿用各模型的部署配置，因此表格比較的是兩套可用配置，不是只改量化、其他完全相同的隔離實驗。

## 做法與資料路徑

推理核心來自 [Niko1221/Strata](https://github.com/Niko1221/Strata)，跨機分層來自 [NTRYourWaifu/Strata two-pc](https://github.com/NTRYourWaifu/Strata/tree/two-pc)，固定 commit `7add08dbd076f7f5fe897c76769064332450fe61`。

桌機計算前面 K 層，筆電計算剩餘層與輸出頭，每個驗證視窗在分界傳中間結果，並返回 token／MTP 所需資料。兩機內部分別用 GPU 專家快取與 CPU 專家運算；兩機依層接力，效能不直接相加。

模型分層資料走 LAN TCP 直連，SSH 只負責啟停管理和本機 API 轉接，網頁透過本機 gateway 使用模型。此次分享不公開實際端點、帳號、金鑰、防火牆規則、存取控制配置或部署管理腳本。

已驗證 Windows／Linux CUDA Release 的雙機連線與推理。原始來源快照保留在 `sources/strata-two-pc`；本機安全相关修改與部署配置不在本次分享範圍。不宣稱 HIP／SYCL 也經過測試。

桌機保留並驗證完整 GGUF。筆電權重檔保留完整結構、非專家資料與第 32–47 層的專家，傳輸範圍逐段 SHA256 校驗；較早專家是稀疏留空，故啟動限制 K≥32。這是工作節點儲存安排，模型的全部專家仍保留在桌機，沒有刪除模型專家。PLE 共用資料表以硬連結避免重複占用，按需讀取；不宣稱整個 GGUF 都載入 RAM。

## 測速方法

1. 確認模型 loaded、沒有其他請求正在生成。
2. 啟動器會先用中文／程式碼各 64 tokens 暖機；每種負載再額外生成 128 tokens，這筆不計成績。
3. 使用以下固定提示，temperature 0、thinking off、`enable_thinking=false`、stream false、max_tokens 512，逐次測三次。
4. 記錄完整 timings、usage、合成輸出；取生成速度中位數，並保留每次值與耗時。
5. 同一提示重複後有提示快取：中文通常重用 26 tokens、程式碼 33；實際 cache_n 以各 JSON 為準。自適應專家快取亦會隨執行變化。

中文提示：
```text
請用繁體中文寫一篇至少一千字的科普文章，解釋颱風如何形成，直接開始正文。
```

程式碼提示：
```text
Write a complete Python implementation of an LRU cache with TTL expiration, thread safety, and example usage. Explain the design after the code.
```

已啟動服務後的測速範例（key 檔案必須是自己的本機檔案）：
```powershell
python scripts/bench-speed.py warm --kind prose --tokens 128 --runs 1 --model qwen3.8-flash-next-iq3_xxs --key-file path/to/local-api-key.txt
python scripts/bench-speed.py measured --kind prose --tokens 512 --runs 3 --model qwen3.8-flash-next-iq3_xxs --key-file path/to/local-api-key.txt
```
程式碼用 `--kind code`；IQ3_S 用 `--model qwen3.8-flash-next-iq3_s`。需先完成模型切換，不能只修改请求的模型名字。

## 記憶體與限制

桌機 32GB RAM 的部署仍有記憶體壓力，快照記錄 available RAM、swap 與 Strata VmSwap；這些資料如實公開，沒有把此結果宣稱為完全無換頁的理想配置。CPU 專家 RAM 預算只計專家，資料表、上下文和系統另占空間。暖機不能替代 RAM 容量，也不保證任意長題零 SSD 讀取。

測試附近的快照（不是整段平均）：

| 模型 | 桌機 available RAM | 桌機 Strata VmSwap | 筆電 available RAM | 筆電剩餘 commit |
|---|---:|---:|---:|---:|
| IQ3_XXS | 0.99 GiB | 300 MiB | 11.21 GiB | 8.14 GiB |
| IQ3_S | 0.54 GiB | 86 MiB | 5.99 GiB | 0.96 GiB |

兩個快照的桌機 2 GiB swap 均幾乎用滿；swap 已占用不等於整段一直在換頁，生成速度的影響需配合實際 I/O 觀察。

兩台並非都走有線，因此不能把上游作者不同模型、英文 800-token、不同分層的結果直接當作本機應達成的固定速度。只驗證本表測試的內容與長度；沒有做 32K 長題、多人併發或長時間壓力測試。

## 開關與介面

`START-QWEN.cmd` 預設 IQ3_S，`START-IQ3_XXS.cmd` 切至 IQ3_XXS，`STOP-QWEN.cmd` 停止本次管理的兩機程序。網頁 `http://localhost:8080/` 可選兩個模型，切換後自動暖機；一次常駐一個模型，重按相同配置沿用常駐模型。

網頁包含對話紀錄、搜尋、推算小視窗與下方獨立回答卡片。私人聊天只存在使用者瀏覽器，不包含在此報告。

`scripts/` 僅分享通用合成測速與 API 暖機工具，`config-templates/` 僅保存推理參數，沒有本機端點、登入帳號、金鑰或安全配置；不是一鍵部署包。建立服務請參照前述上游項目。

## 原始證據

數據與硬體快照：`results/2026-10-10-iq3-comparison/`，其中 `summary.json` 可機器讀取。只公開合成測試輸出與必要硬體資料；不包含實際 LAN IP、登入帳號、API key、SSH 私鑰、程序 PID、模型權重、編譯二進位或私人聊天。
