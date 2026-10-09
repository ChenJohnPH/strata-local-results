# Strata 本機部署與雙機實驗成果

2026-10-10 工作區快照：保存 Windows 筆電與 Ubuntu 桌機的配置範例、建置工具、短測結果，以及後續雙機分層的準備原始碼。

## 已驗證成果

硬體：桌機 Ryzen 9 9950X、RTX 4080 SUPER 16GB、32GB RAM；筆電 Ryzen 9 7945HX、RTX 4070 Laptop 8GB、32GB RAM。

| 配置 | 工作負載 | 生成速度 | 測量限制 |
| --- | --- | ---: | --- |
| llama.cpp RPC 原配置 | 數字，96 tokens | 2.747 tok/s | 一次測量 |
| RPC 輸出層留在桌機 GPU | 相同數字，96 tokens | 6.485 tok/s | 一次測量 |
| RPC＋GPU 非專家運算＋3GiB MoE 快取 | 相同數字，96 tokens | 中位數 24.053 tok/s | 三次測量，提示快取與專家快取狀態見 JSON |
| Strata Q2_0，專家由 SSD 映射 | 中文，128 tokens | 18.5 tok/s | 一次短測 |
| Strata Q2_0，GPU 未持有的專家常駐 RAM＋MTP | 相同中文，128 tokens | 56.0 tok/s | 一次短測；生成 2.284 秒，整次 2.72 秒 |
| 後續硬體調整的 Q2 短測 | 中文，128 tokens | 63.6 tok/s | 一次短測；此快照沒有完整保存該輪設定，不能據此判定哪項調整造成提升 |

不同提示、輸出長度、快取狀態的數值不作直接倍率比較。Strata 的 56.0 與 63.6 都是短測結果，不是長時間平均，也不代表 IQ3 模型的速度。`results/` 保留原始 timings、usage 與合成提示的輸出。

## 快照當下的狀態

目前選擇檔顯示 **IQ3_XXS / IQ3_S 雙機版本正在準備**；Q2 已在後續工作中移除。前面的 Q2 成果是歷史驗證結果，並不表示現在仍能直接啟動 Q2。

雙機準備程式碼來自 [NTRYourWaifu/Strata](https://github.com/NTRYourWaifu/Strata)，封存目錄參考 `7add08d`。原始 Strata 為 [Niko1221/Strata](https://github.com/Niko1221/Strata)。此儲存庫保留當下準備好的來源副本與授權，不宣稱此快照的 Ubuntu＋Windows 雙機版本已完成推論驗證。上游指南中的效能數字屬於上游作者的不同硬體。

## 內容

- `scripts/`：啟停、SSH、短測、建置、模型下載與 pack 準備腳本。
- `config-templates/`：歷史 Q2 配置及當下 IQ3 準備狀態，已將電腦名稱、區網 IP 和使用者路徑改成佔位符。
- `results/`：本工作區保存的測量 JSON；帶 `network-transition`、`compile-overlap` 的檔案屬於條件受干擾的紀錄。
- `sources/strata-two-pc/`：準備好的雙機原始碼及第三方依賴来源。授權檔保留在原路徑。
- `docs/`：研究、歷史部署說明與上游雙機指南。
- `PROVENANCE.json`、`SNAPSHOT-SHA256.json`：來源說明與檔案完整性清單。

不包含模型權重、MTP runtime 檔案、編譯好的 GPU 程式、Python 虛擬環境、SSH 私鑰、API key、程序 PID 或私人聊天紀錄。

## 使用前

這是成果快照，`scripts/` 與 `config-templates/` 的 `REMOTE_USER`、`DESKTOP_LAN_IP`、`DESKTOP_HOST_KEY_ALIAS` 等佔位符需要自行替換；來源與建置工具的位置也要符合你的電腦。金鑰需另外建立。模型依其原始授權自行下載，不由此儲存庫分發。

短測工具可使用既有的 OpenAI 相容服務：

```powershell
python scripts/bench-speed.py example --kind prose --tokens 128 --runs 1 --key-file path/to/local-api-key.txt
```

程式預設讀取 `http://127.0.0.1:8080`。測量生成速度使用引擎的 `predicted_per_second`，不把讀題時間算入。
