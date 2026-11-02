# 來源與修改

課程來源：https://github.com/cychiang-ntpu/mmsp2026

本次固定來源 commit：`3ea33dd8635d3f556341ee093fbc2081b81cea3d`。
課程 `team_projects/team2_voicelink/README.md` 明確允許以 tutorial 第 7 步為起點；此處沿用於課程作業。上游未提供整個課程的統一 LICENSE，不自行宣稱其為 MIT 或重新授權。

| 本地 | 上游 |
|---|---|
| src/voicelink.c | tutorial/step7_live.c（修改） |
| include/{audio,clock,udp,wav}.h、src/audio.c | baseline/wrapper/（wav.h 有修改） |
| vendor/miniaudio.h | baseline/wrapper/miniaudio.h（原樣，授權文字在檔案內） |
| baseline/udp_impair.py | baseline/udp_impair.py（原樣） |
| python_ref/voicelink.py | python_ref/voicelink.py（原樣） |
| tests/run_mock_tests.py | tests/run_mock_tests.py（原樣，保留測試判定） |
| tests/data/aeueo-16kHz.wav | lectures/wk07_1019_audio-pcm/data/aeueo-16kHz.wav |

本地新增/修正：C11 atomic 結束旗標、首包遺失補償、seq/ts 一致性檢查、新 SSRC 時 codec/輸出/時鐘完整重設、延遲 BYE 去除尾端 PLC、等候第一包遵守 timeout、BYE 納入傳輸 bytes、拒絕奇數長度 PCM、IPv4 參數驗證、Makefile、邊界測試、量測工具、文件及簡報。

miniaudio 原檔保留 public domain / MIT No Attribution 選項與原始聲明。新增文件中對沿用演算法的說明不代表組員原創貢獻。
