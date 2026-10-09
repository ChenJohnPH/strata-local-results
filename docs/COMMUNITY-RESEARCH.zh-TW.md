# Qwen3.8 Flash Next 與跨機 RPC 案例整理

查閱日期：2026-10-09。下列數字是原作者自行報告的測量，沒有在你的機器重現；模型量化、提示、上下文、引擎版本與採樣設定不同，不能直接當作你的預期速度。表中的速度均指生成，不是提示讀取。

## 實際案例

| 硬體與模型 | 做法 | 作者報告生成速度 | 和你的配置有何不同 |
| --- | --- | --- | --- |
| RTX 5070 12GB、Ryzen 7600、64GB RAM；完整 Flash Next Q2_0 | Strata 0.1.36，GPU 專家快取、專用核心與推測解碼 | 94 tok/s；同頁 IQ3_XXS 是 62 tok/s | 單機 Strata，RAM 是桌機的兩倍；並非普通 llama.cpp RPC |
| RTX 5070 12GB、i5-13500 VM、91GiB RAM；Flash Next Q2，自訂 Q8 hyper-connection mixers | llama.cpp 分支，所有層的非專家部分放 GPU、專家在 CPU、6 個實體核心、MTP | 短上下文約 23–24 tok/s，23K 約 21–23；另一個 greedy 比較不開專家快取 26.7，8-slot 快取 25.8 | 模型有額外重新量化，RAM 遠大於 32GB；不是跨機測試。快取或 MTP 不一定都加速 |
| RTX 4090 24GB；Flash Next UD-Q3_K_XL、8K | 實驗性 persistent expert pool，所有專家原先在 CPU | 中性 tg512 測試 11.55→21.21；實際程式生成 12.82→17.14 | 單卡分支，當時只支援第一張 GPU 的快取；不是現有版本可直接複製的參數 |
| 同一台 Windows 的 2×RTX 3090 24GB；Flash Next IQ4_XS | csantiago78 專家快取分支加公開與私有修改、MTP2、CPU 核心綁定 | 約 3500 tokens 時 49.3 tok/s | 同機 48GB 顯存，非 Wi-Fi RPC；完整程式樹未公開，因此不能視為完整可重現配方 |
| RTX 5080 16GB＋RTX 2070 SUPER 8GB，兩台 Windows、1GbE；27B Q4_K | llama.cpp RPC、分層、單 slot、量化 KV，所有層放兩張 GPU | 表格：32K 約 22，96K 約 18，128K 約 15 tok/s | 顯存容量和你接近，但模型只有 27B；你的完整 125B 仍約半數主權重在桌機 CPU |
| M2 Ultra 128GB＋DGX Spark 120GB，10GbE；Qwen2.5 72B Q4_K_M | Metal＋CUDA RPC | 單機 11.1；RPC 5.9 tok/s | 即使實測網路 9.41Gbps，仍可能因軟體與同步成本變慢；硬體與模型都不同，不能用它預測你的速度 |
| RTX 5090 32GB、285K、64GB RAM；Flash Next IQ2_XS | Strata 0.1.29、約 23.44GiB GPU 專家快取、MTP，三次測量取中位數 | 4K 提示 179.4；32K 175.7；128K 165.0 tok/s | 很完整的可重現報告，但顯存、RAM、PCIe 與引擎均不同 |

原始來源：

1. [Strata 官方測量及硬體需求](https://github.com/Niko1221/Strata)
2. [holden093 的模型、CPU affinity、MTP 與快取測量](https://github.com/holden093/llama.cpp-qwen3.8-flash-next)
3. [RTX 4090 persistent expert pool 的原始測量](https://github.com/ggml-org/llama.cpp/discussions/28248)
4. [2×3090 專家快取分支測量與限制](https://github.com/ggml-org/llama.cpp/discussions/24528)
5. [16GB＋8GB 兩台 Windows 的 RPC 安裝與調整](https://github.com/FremaTech/llama-rpc-dual-gpu)
6. [10GbE Metal＋CUDA RPC 的原始資料與指令](https://github.com/kjaiswal/llama-cpp-distributed-benchmarks)
7. [Strata RTX 5090：逐次 JSON、設定與方法](https://github.com/Niko1221/Strata/blob/main/bench/results/2026-09-30-community-rtx-5090/README.md)

第 4 個案例請在討論串搜尋 Volunteer-1 的 2026-09-22 留言；不要假設未公開修改可由一條命令重現。

## 可以套用到你這裡的判斷

1. 跨機先用連續分層，避免把同一層的矩陣拆到網路兩邊。權重主要在載入時送到 worker；生成時仍須按模型依賴傳送中間結果。
2. 一個 token 可由 4080S 跑完它的連續區段後送到 4070，但下一個 token 要等本輪輸出決定。不能先把整段回答的 4080S 工作全部做完才一次傳送。MTP 可以一次推測數個 token、批次驗證，這才是減少逐 token 成本的相關方向。
3. 把輸出 head 留在主機／做 GPU backend sampling，可避免把整份大詞表分數從遠端取回。你的配置已採輸出 head 留在 4080S；這是實測有效的修正。
4. 高速度 MoE 案例通常將 attention、hyper-connection 等非專家工作留在 GPU，只讓 CPU 處理未快取的專家，而不是把整個前半部模型放在 CPU。熱門專家快取與 MTP 是後續值得比較的路線。
5. 網路要同時看頻寬、往返延遲與 RPC 同步等待。桌機 Wi-Fi、SSH 有效串流約 81.6Mbps 是弱點，但不能據此推斷改有線就會到 60 tok/s。
6. 你的兩台 RAM 不會自動變成一台 64GB RAM。目前 CPU 權重在桌機，筆電作為 GPU worker。Strata 官方多 GPU 路徑是同機多卡，沒有在這些資料中提供可直接替換的跨機 RPC 引擎。

[Strata 多卡原理與支援範圍](https://github.com/Niko1221/Strata/blob/main/docs/MULTI_GPU.md)說明連續分層、每張卡各自快取專家，以及末端卡執行輸出 head 和 MTP；它描述的是同一台電腦。

## 你的實測

固定完整 GSQ-RCO Q2_0、16K context、相同 32-token 提示、96-token 輸出、temperature 0、關閉思考。生成速度取伺服器 predicted_per_second，沒有把提示處理算進去。

- 原配置，輸出 head 在筆電：2.747 tok/s，整次請求約 42.69 秒。
- 輸出 head 與 hc_head 移至桌機 CUDA0，16 threads：6.485 tok/s，整次約 20.19 秒。
- 相同 head 配置，8 threads 綁定 CPU 0–7、提示處理 16 threads：6.065 tok/s，整次約 20.06 秒。因此恢復 16 threads。
- 此次比較各一次測量，約 2.36 倍生成速度；不是所有提示均可保證的速度。
- 原始資料：profile-baseline.json、profile-head-local-16.json。硬體負載：桌機 profile-desktop-baseline.json、profile-desktop-head-local-16.json。

目前尚未在你的硬體測量 Strata 或專家快取分支。上表的 60–100 tok/s 不能當作這個普通跨機分層配置的保證。
