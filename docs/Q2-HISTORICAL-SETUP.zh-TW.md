# Qwen3.8-Flash-Next：目前使用 Strata 常駐 RAM 配置

2026-10-09 已將預設引擎切換為 Strata 0.1.41，完整 GSQ-RCO Q2_0，保留全部專家。模型由 Ubuntu 桌機的 9950X、4080 SUPER 16GB、32GB RAM 執行；筆電透過 SSH 使用網頁及 API。

## 開關

- 在筆電雙擊 `START-QWEN.cmd`：連接桌機、載入模型、等待就緒並開啟網頁。
- 雙擊 `STOP-QWEN.cmd`：停止模型與本次安裝管理的 SSH 隧道。
- 關閉瀏覽器不會停止模型。兩台須保持開機與可連線。

網頁：http://127.0.0.1:8080/

OpenAI API：http://127.0.0.1:8080/v1

模型別名：`qwen3.8-flash-next-125b-q2_0`

Strata 已啟用 API key。第一次網頁或客戶端要求金鑰時，開啟 `ssh\strata-api-key.txt`，複製裡面的字串。請勿分享金鑰或 SSH 私鑰。

## 配置與短測

- CUDA 12 引擎，以桌機原有 CUDA 12.4 編譯；NVIDIA 驅動 570.211.01。
- 16,384-token context、INT8 KV、單一請求、MTP、15 個專家工作執行緒加主執行緒。
- GPU 專家快取約 9.30GiB、7,224 個專家；GPU 未持有的專家常駐 RAM，約 23.19GiB。
- 中文短測：33-token 提示、128-token 回答、temperature 0、關閉思考，生成 **56.0 tok/s**；生成 2.284 秒，整次 2.72 秒。
- 相同中文短測，Strata mmap 模式為 18.5 tok/s。原 RPC 配置的數字測試為 2.747，輸出層修正後為 6.485，MoE 快取曾達 24.053 tok/s 中位數；不同提示的測量應分開比較。
- 56.0 是一次短測，不能保證每個問題同速；現行配置尚未重新做長上下文測試。
- 目前桌機單機推論比已測跨機配置快，筆電 RPC worker 已停止。

原始結果：`bench-strata-resident-auto-prose.json`、`bench-strata-mmap-auto-prose.json`。

## 網路與檔案

桌機 RTL8126 有線網卡原先沒有驅動。來源已與 OpenWrt 的 SHA256 清單比對，取得同意後安裝 r8126 10.016.00 DKMS，符合目前核心 6.8.0-138。

桌機有線 IP：`DESKTOP_LAN_IP`，連線速度 1Gbps；Wi-Fi IP：`DESKTOP_HOST_KEY_ALIAS`。SSH 使用原來已驗證的主機金鑰，強制檢查。防火牆允許筆電 LAPTOP_WIRED_IP 與 LAPTOP_WIFI_IP 連 SSH。

桌機服務僅監聽 127.0.0.1:8080，筆電以 SSH 轉接取得網頁。DHCP 位址改變時，須調整 Start-Strata.ps1、Start-Qwen.ps1、Stop-Qwen.ps1 的桌機位址。

- 筆電工具：`D:\LLM\llama-rpc`
- 原始模型：桌機 `~/llama-rpc/models/Q2_0`，兩檔共 66.4GB，SHA256 已驗證。
- Strata 程式：桌機 `~/Strata-speed`
- Strata 資料與 MTP：`~/Strata-speed-data`
- 現行配置：桌機 `~/Strata-speed/strata-q2_0.json`；本機 `selected-engine.json`。
- 紀錄：桌機 `~/Strata-speed/managed-server.log`、`~/Strata-speed/strata-q2_0.log`，筆電 `tunnel.err.log`。

原有 llama.cpp b11517、RPC 配置及研究報告均保留。切換引擎前先停止現行模型，避免同時載入兩個大模型。