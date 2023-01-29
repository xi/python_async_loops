import datetime
import os
import subprocess


class LineReader:
    def __init__(self, file):
        self.file = file
        self.buffer = b''
        self.line = ''

    def read_line(self):
        chunk = os.read(self.file.fileno(), 1024)
        if not chunk:
            raise ValueError
        self.buffer += chunk
        lines = self.buffer.split(b'\n')
        if len(lines) > 1:
            self.line = lines[-2].decode('utf-8')
        self.buffer = lines[-1]


def cleanup():
    proc1.terminate()
    proc2.terminate()
    proc1.wait()
    proc2.wait()


def render():
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(' '.join([now, reader1.line, reader2.line]))


proc1 = subprocess.Popen(['./random.sh'], stdout=subprocess.PIPE)
proc2 = subprocess.Popen(['./random.sh'], stdout=subprocess.PIPE)

reader1 = LineReader(proc1.stdout)
reader2 = LineReader(proc2.stdout)

try:
    while True:
        for reader in [reader1, reader2]:
            reader.read_line()
        render()
finally:
    cleanup()
