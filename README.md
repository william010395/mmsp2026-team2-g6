# VoiceLink — MMSP 2026 Team 2 / G6

C 語言即時 UDP 語音管線：16 kHz、16-bit 單聲道、20 ms framing、bounded jitter buffer、zero/repeat PLC、PCM / μ-law，以及 miniaudio 雙向通話。

## 建置與執行

需要 GCC/Clang（C11）、Make；測試需要 Python 3 標準函式庫。miniaudio 已隨附，mock 不需要音訊裝置或額外套件。

```sh
make -j2
# 終端機 A：先啟動接收端
./voicelink recv 5004 out.wav --buffer 60 --plc repeat --timeout 2000
# 終端機 B：接收端啟動後 2 秒內執行
./voicelink send 127.0.0.1 5004 tests/data/aeueo-16kHz.wav
# 壓縮版本
./voicelink send 127.0.0.1 5004 tests/data/aeueo-16kHz.wav --codec mulaw
```

接收端由封包自動選 codec。`--buffer` 支援 20–320 ms，必須為 20 的倍數；`--timeout` 包含等候第一包的時間。手動測試可設 `--timeout 10000`。結束碼 0 正常、1 網路/裝置、2 參數/檔案錯誤。

Linux 已驗證；macOS 與 Windows（MSYS2 MinGW GCC，`mingw32-make` / `voicelink.exe`）保留平台分支，但尚未實機驗證。Windows 測試可指定 `PYTHON=python`，測試程式會尋找 `.exe`。

產生圖表與重建投影片的選用依賴：`python3 -m pip install -r tools/requirements.txt`。

## 自動驗收

```sh
make test       # 邊界回歸測試 + 官方測試 1–8
make test-ref   # 官方 Python send → C recv，以及 C send → Python recv
make measure    # 需 matplotlib；buffer 20–200 ms 各 3 次、PLC WAV、CSV、SVG
make slides     # 重建 slides.pdf（另需 reportlab）
```

官方測試的 ADPCM 是選做加分，本版未實作；測試 9 明確 SKIP。測試及量測會開本機 UDP socket；若執行平台限制 socket，需允許本機網路操作。原始結果在 `docs/results/`，說明在 [報告](docs/report.md)。

## 搗蛋中繼與跨機通話

```sh
# 三個終端依序開 recv、中繼、send
./voicelink recv 5004 out.wav --timeout 10000
python3 baseline/udp_impair.py 5005 127.0.0.1 5004 --loss .05 --jitter 30 --reorder .05 --seed 1
./voicelink send 127.0.0.1 5005 tests/data/aeueo-16kHz.wav
# A/B 兩台都接同一熱點、允許 UDP 5004，換成實際 IPv4
./voicelink devices
./voicelink call 5004 192.168.1.20 5004 --buffer 60 --plc repeat --codec mulaw
```

B 同時執行 `call`，對方 IP 改成 A。戴耳機，按 Enter 結束。無音訊裝置的雲端不能驗證實際通話或聽感；[現場驗收表](docs/manual-test.md) 列出步驟。

## 專案結構與繳交

- `src/voicelink.c`：CLI、封包、codec、buffer、mock/live 主程式。
- `src/audio.c`、`include/`、`vendor/`：跨平台音訊、WAV、UDP、時鐘。
- `tests/`、`python_ref/`、`baseline/`：官方驗收、對手端、搗蛋中繼及新增回歸測試。
- `docs/interface.md`、`docs/report.md`、`slides.pdf`：介面、報告與簡報。
- `TEAM_LOG.md`、`CONTRIBUTIONS.md`、`AI_USAGE.md`、`THIRD_PARTY.md`：工作紀錄與來源。

依課程允許，以官方 step7 為基礎修改，並非全部從零撰寫；來源與修正見 `THIRD_PARTY.md`。μ-law 使用老師 C/Python 範例的對數量化 wire format，與標準 G.711 bit-inverted octet 編碼不同，請以課程對手端互通為準。

繳交前：組員實際閱讀與修改 C、完成各自 commit、補真實貢獻與現場測試結果，再登錄 repo URL 與 `git rev-parse HEAD` 的完整 SHA。截止以課程公告 2026-11-22 18:00 為準。
