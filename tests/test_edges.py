"""Real UDP regression tests; no audio hardware needed."""
import socket, struct, subprocess, tempfile, time, unittest, wave, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
BIN = str(ROOT / ('voicelink.exe' if sys.platform == 'win32' else 'voicelink'))

def packet(seq, ts, value=1000, kind=1, ssrc=123):
    return struct.pack('!BBHII', 0x56, kind, seq & 65535, ts, ssrc) + (struct.pack('<320h', *([value]*320)) if kind == 1 else b'')

class Edges(unittest.TestCase):
    def exchange(self, packets, options=(), delay=.003):
        with tempfile.TemporaryDirectory() as d, socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.bind(('127.0.0.1', 0)); port = sock.getsockname()[1]; sock.close()
            output = Path(d)/'out.wav'
            p = subprocess.Popen([BIN,'recv',str(port),str(output),'--timeout','200',*options], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            try:
                time.sleep(.06)
                with socket.socket(socket.AF_INET,socket.SOCK_DGRAM) as tx:
                    for data in packets:
                        tx.sendto(data,('127.0.0.1',port)); time.sleep(delay)
                stdout, stderr = p.communicate(timeout=4)
                self.assertEqual(p.returncode,0,stderr.decode())
                with wave.open(str(output),'rb') as w: pcm=w.readframes(w.getnframes())
                self.assertIn(b'STATS role=recv',stderr)
                return pcm,stderr.decode()
            finally:
                if p.poll() is None: p.kill(); p.communicate()
    def test_partial_frame(self):
        pcm,s=self.exchange([packet(0,0),packet(1,17,kind=2)])
        self.assertEqual(pcm,struct.pack('<17h',*([1000]*17)))
    def test_missing_first(self):
        pcm,s=self.exchange([packet(1,320),packet(2,640,kind=2)])
        self.assertEqual(len(pcm),1280); self.assertEqual(pcm[:640],bytes(640)); self.assertIn('lost=1 ',s)
    def test_zero_plc(self):
        pcm,s=self.exchange([packet(0,0),packet(2,640),packet(3,960,kind=2)],['--plc','zero'])
        self.assertEqual(pcm[640:1280],bytes(640)); self.assertIn('concealed=1 ',s)
    def test_repeat_plc(self):
        pcm,s=self.exchange([packet(0,0),packet(2,640),packet(3,960,kind=2)])
        self.assertEqual(pcm[:640],pcm[640:1280]); self.assertIn('concealed=1 ',s)
    def test_wrap_and_second_bye(self):
        pcm,s=self.exchange([packet(65535,0),packet(0,320),packet(2,640,kind=2)])
        self.assertEqual(len(pcm),1280); self.assertIn('lost=0 ',s)
    def test_timeout_trims_plc(self):
        pcm,s=self.exchange([packet(0,0)])
        self.assertEqual(len(pcm),640); self.assertIn('concealed=0 ',s)
    def test_no_sender(self):
        pcm,s=self.exchange([]); self.assertEqual(pcm,b''); self.assertIn('frames_out=0 ',s)
    def test_delayed_bye_trims_plc(self):
        pcm,s=self.exchange([packet(0,0),packet(1,17,kind=2)],['--timeout','600'],delay=.18)
        self.assertEqual(len(pcm),34); self.assertIn('frames_out=1 ',s)
    def test_empty_bye(self):
        pcm,s=self.exchange([packet(0,0,kind=2)]); self.assertEqual(pcm,b'')
    def test_duplicate_and_garbage(self):
        pcm,s=self.exchange([b'bad',packet(0,0),packet(0,0),packet(1,320,kind=2)])
        self.assertEqual(len(pcm),640); self.assertIn('dup=1 ',s)
    def test_ssrc_reset(self):
        pcm,s=self.exchange([packet(0,0),packet(0,0,value=2000,ssrc=456),packet(1,320,kind=2,ssrc=456)])
        self.assertEqual(pcm,struct.pack('<320h',*([2000]*320)))
    def test_invalid_arguments(self):
        for args in [('recv','0','x'),('recv','5004','x','--buffer','21'),('send','127.0.0.1','5004','missing.wav'),('send','127.0.0.1','5004','x','--codec','bad')]:
            self.assertEqual(subprocess.run([BIN,*args],capture_output=True).returncode,2)
    def test_wav_chunks_and_reject_odd(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'in.wav'
            fmt=b'fmt '+struct.pack('<IHHIIHH',16,1,1,16000,32000,2,16)
            for raw,expected in [(b'\x00\x01',0),(b'\x00',2)]:
                body=b'WAVE'+fmt+b'JUNK'+struct.pack('<I',3)+b'abc\0'+b'data'+struct.pack('<I',len(raw))+raw
                path.write_bytes(b'RIFF'+struct.pack('<I',len(body))+body)
                rc=subprocess.run([BIN,'send','127.0.0.1','59999',str(path)],capture_output=True).returncode
                self.assertEqual(rc,expected)

if __name__=='__main__': unittest.main(verbosity=2)
