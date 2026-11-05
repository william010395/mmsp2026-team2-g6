"""Rebuild the submission PDF from recorded results; requires reportlab."""
from pathlib import Path
import csv,json
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont, defaultUnicodeEncodings
# Traditional Chinese font belongs to Adobe-CNS1 (not GB).
defaultUnicodeEncodings["MSung-Light"] = ("cht", "UniCNS-UCS2-H")
ROOT=Path(__file__).resolve().parents[1]
pdfmetrics.registerFont(UnicodeCIDFont('MSung-Light'))
pages=[
('VoiceLink｜即時 UDP 語音管線',[
'MMSP 2026 · Team 2 / G6 · 2026-11-02',
'16 kHz · PCM16 mono · 20 ms / frame',
'C 實作：mock、jitter buffer、PLC、μ-law、live',
'以課程允許的 step7 範例為起點；來源見 THIRD_PARTY.md',
'現場通話、真人聽感與個人貢獻需組員完成。']),
('管線與固定節奏',[
'WAV / mic → 320 samples → codec → 12-byte header → UDP',
'UDP → 驗證 → decode → jitter buffer → PLC → WAV / speaker',
'每 20 ms 向 buffer 要下一個 seq，缺包照樣前進。',
'預設 60 ms 等待；容量 12 frames；滿了丟最舊。',
'mock 用單調時鐘；live 用音訊 callback，mutex 保護 buffer。']),
('封包、結尾與錯誤處理',[
'Header：magic(1) / type(1) / seq(2) / ts(4) / ssrc(4)',
'Header big-endian；PCM little-endian；seq 65535 → 0。',
'PCM 652 bytes；μ-law 332 bytes；BYE 12 bytes × 3。',
'BYE.ts = 真實 sample 數，截掉最後補零。',
'首包遺失也補 PLC；timeout 與延遲 BYE 去除尾端多補。',
'SSRC 改變重設 session；壞 magic / type / 長度直接丟棄。']),
('自動驗收結果',[
'C → C：官方 1–8 全過；新增 13 個邊界測試全過。',
'Python → C、C → Python：各 8/8 全過。',
'PCM：225,082 bytes 逐 byte 相同，含部分尾框。',
'5% loss：352 frames，lost = concealed = 17。',
'亂序、重複、送端被殺、垃圾封包與 STATS 皆驗證。',
'ADPCM 為選做加分，未實作；測試 9 SKIP。']),
('μ-law：流量減半與失真',[
'課程對數量化格式：與官方 Python 對手端互通。',
'不是標準 G.711 bit-inverted octet mapping。',
'Payload：PCM 256 kb/s → μ-law 128 kb/s。',
'實測 UDP payload：229,540 → 116,900 bytes，比例 0.509。',
'無損包 SQNR = 37.8 dB，大於 30 dB 門檻。',
'解碼後才做 PLC，兩個 codec 共用 buffer 與補償程式。']),
('Buffer 掃描：多等不會救回真正掉包',[]),
('PLC：數字與預期聽感',[
'固定 seed=1 / loss=5%，四種設定皆補 17 frames。',
'PCM SQNR：zero 19.29 dB；repeat 14.64 dB。',
'μ-law SQNR：zero 19.23 dB；repeat 14.62 dB。',
'zero 可能斷續 / click；repeat 短缺口較連續但可能嗡聲。',
'repeat 不保證 SQNR 較高；波形誤差不等於主觀可懂度。',
'四個聽音 WAV 已產生；真人聽感尚待填寫。']),
('展示與繳交前確認',[
'make test / make test-ref / make measure 可重現結果。',
'--burst：352 包中 overflow=340，證明送端 pacing 必要。',
'雲端無可用預設麥克風：call 回傳 1，未宣稱通話通過。',
'現場兩台電腦連熱點、戴耳機，雙向通話至少 30 秒。',
'組員補真實 C commit、分工、聽感及 B0/A4 驗收紀錄。',
'最後登錄 repo URL + 完整 commit SHA；勿將測試代替現場。'])]
c=canvas.Canvas(str(ROOT/'slides.pdf'),pagesize=(960,540))
c.setTitle('VoiceLink — MMSP 2026 Team 2 G6')
for i,(title,lines) in enumerate(pages):
 c.setFillColorRGB(.04,.09,.18);c.rect(0,0,960,540,fill=1,stroke=0)
 c.setFillColorRGB(.3,.85,.8);c.rect(45,465,65,5,fill=1,stroke=0)
 c.setFillColorRGB(1,1,1);c.setFont('MSung-Light',29);c.drawString(45,490,title)
 c.setFont('MSung-Light',20)
 for n,line in enumerate(lines): c.drawString(48,415-48*n,line)
 if i==5:
  c.drawImage(str(ROOT/'docs/results/buffer.png'),45,55,width=480,height=395,preserveAspectRatio=True,anchor='c')
  c.setFont('MSung-Light',17)
  for j,line in enumerate(['2 秒語音，20–200 ms，各 3 次。','loss 5%、jitter 0–30 ms、reorder 5%。','seed=1 固定：七包 lost，所有點 late=0。','此條件 20 ms 已足夠；延遲隨 buffer 增加。','保留預設 60 ms 作一般展示餘裕。','短片段不能推論所有網路。']):
   c.drawString(540,395-j*45,line)
 c.setFillColorRGB(.6,.7,.8);c.setFont('MSung-Light',12)
 c.drawString(45,22,'VoiceLink / G6 · 證據與來源：docs/report.md · THIRD_PARTY.md')
 c.drawRightString(915,22,f'{i+1} / {len(pages)}');c.showPage()
c.save()
