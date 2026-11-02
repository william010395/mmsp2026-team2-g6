# VoiceLink 介面與設計

## CLI

```
voicelink send <ip> <port> <in.wav> [--burst] [--codec pcm|mulaw] [--seq0 N]
voicelink recv <port> <out.wav> [--bind IP] [--buffer MS] [--plc zero|repeat] [--timeout MS]
voicelink call <my_port> <peer_ip> <peer_port> [--buffer MS] [--plc zero|repeat] [--codec pcm|mulaw]
voicelink devices
```

預設 buffer=60、plc=repeat、timeout=2000、codec=pcm、bind=0.0.0.0。IPv4 port 為 1–65535。`--seq0` 是測試繞回用擴充。ADPCM 未實作。輸入 WAV 必須 PCM16 / mono / 16000 Hz；依 chunk 解析、跳過未知 chunk 與奇數 padding。

## Wire format

| Offset | Bytes | 欄位 |
|---|---:|---|
| 0 | 1 | magic=0x56 |
| 1 | 1 | type=1 PCM、2 BYE、4 μ-law |
| 2 | 2 | seq，network byte order，mod 65536 |
| 4 | 4 | ts，network byte order，音訊第一個 sample 的位置 |
| 8 | 4 | ssrc，network byte order，單次串流固定 |
| 12 | 640 / 320 / 0 | PCM little-endian / 課程 μ-law / BYE |

PCM 每包 652 bytes、μ-law 每包 332 bytes、BYE 12 bytes。最後不足 320 samples 補零；3 個 BYE 的 ts 都是原始 sample 數，seq 各 +1。recv 按 ts 截去尾端 padding。send 的 bytes 包含成功送出的 AUDIO 與 BYE UDP payload，不含 IP/UDP 標頭。

μ-law 與官方 Python 相同：`q=clamp(round(sign(x)*log(1+255*abs(x))/log(256)*128),-128,127)`，byte=q+128。解碼反變換；PCM 與 μ-law 解碼後共用 PLC。這是課程公式的 256 階量化，非標準 G.711 octet mapping。

## 模組與資料流

`wav_read → 320-sample frame → codec → pack_header → udp_send`

`udp_recv → parse_header → codec decode → jb_put → jb_tick → WAV / speaker`

- `pack_header / parse_header`：逐 byte 存取，驗 magic/type/確切長度。
- `jb_put`：以 seq % 64 定位；16-bit modular 差判先後；seen bitset 辨重複；到達時間用單調時鐘。
- `jb_tick`：固定 20 ms，沒有預期 seq 就 PLC，expected 必定前進。
- `jb.cap`：4 × buffer_frames，上限 64，overflow 丟最舊的。
- 首包 ts / 320 推算序號起點，因此開頭掉包仍輸出 PLC；後續 seq 與 ts 不符視為壞包。固定 framing 的播放時刻是起點 + ts/16 ms。
- `recv`：select 等待下次 tick 或 timeout。第一包到達後等待 buffer_ms。BYE 可超車，收到後繼續按節奏排空。
- 逾時及遲到的 BYE：去掉結尾之後等待期間補出的 frame，保持 WAV 與 STATS 一致。
- 新 ssrc：mock 重新錄製，捨棄先前 session 的輸出與統計，重設 codec、時鐘及 PLC 歷史。輸出代表最後一個 session。
- `call`：主執行緒等 Enter、網路執行緒接收、音訊 callback 切框收發。mutex 保護 jitter buffer，C11 atomic stop flag 負責終止。callback 不進行檔案 I/O；UDP send 仍在 callback 內，極端系統負載可能影響實時性。

## STATS

stderr 的接收行固定為：

```
STATS role=recv buffer_ms=60 plc=repeat codec=pcm frames_out=... received=... lost=... late=... dup=... reordered=... overflow=... concealed=... avg_delay_ms=... max_delay_ms=...
```

`received` 包含重複及遲到；`lost` 為輸出區間 frame 數減去唯一到達 frame 數（不小於零）；`concealed` 為播放時缺包數。正常結束時 `frames_out = received - late - dup - overflow + concealed`。delay 只計真正播出封包的「到達到播放」，不是跨機器端到端延遲。壞包另以 stdout 計數，避免改動評測 STATS 欄位。

記憶體：jitter queue 固定大小，mock WAV 輸入與輸出保留在記憶體中，隨錄音長度增加；不是無限長錄音服務。模數 seq 比較要求有效亂序距離小於 32768 frames。相隔超過半個序號空間的突發流量不在支援範圍。
