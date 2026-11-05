# 現場驗收（尚未執行）

1. A、B 連同一手機熱點，查各自 IPv4，允許 UDP 5004。記錄 OS、IP、日期與操作者。
2. A 執行 `recv 5004 received.wav --timeout 30000`；B 對 A 的 IP 執行 `send`。比較 WAV PCM 與長度，保留 STATS。交換方向再試。這才完成 B0，loopback 不能代替。
3. 兩邊執行 `devices`，戴耳機，以 `call 5004 <對方IP> 5004 --codec mulaw` 通話至少 30 秒，確認雙向可懂、Enter 結束與統計；保留裝置名稱與結果。雲端無硬體不能代替 A4。
4. 聽 `docs/results/loss5-pcm-zero.wav` 與 `loss5-pcm-repeat.wav`，再比較 mulaw 兩個版本。寫出實際聽感及片段位置，勿把報告中的預期現象當成聆聽紀錄。
5. 如需端到端延遲，以同一錄音裝置同時錄到 A 的拍手與 B 的播放聲，從兩峰時間差估算；距離傳播/裝置緩衝也算入誤差。不得直接相減不同電腦時鐘。
6. 全員各自理解、修改、測試 C 並提交 commit；更新 CONTRIBUTIONS、TEAM_LOG、報告與投影片；`make test && make test-ref`；登錄 repository URL 與完整 HEAD SHA。

記錄欄位：日期 / A、B 設備及 OS / 網路 / codec / buffer / 方向 / 30 秒可懂與否 / 延遲方法及值 / 操作者 / 證據檔案。
