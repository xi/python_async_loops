import datetime
import os
import selectors
import subprocess
import time


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


class Loop:
    def __init__(self):
        self.selector = selectors.DefaultSelector()
        self.times = []

    def set_timeout(self, callback, timeout):
        now = time.time()
        self.times.append((callback, now + timeout))

    def set_interval(self, callback, timeout):
        def wrapper():
            callback()
            self.set_timeout(wrapper, timeout)
        self.set_timeout(wrapper, 0)

    def register_file(self, file, callback):
        self.selector.register(file, selectors.EVENT_READ, callback)

    def unregister_file(self, file):
        self.selector.unregister(file)

    def run(self):
        while True:
            now = time.time()
            timeout = min((t - now for _, t in self.times), default=None)

            for key, mask in self.selector.select(timeout):
                key.data()

            keep = []
            now = time.time()
            for callback, t in self.times:
                if t < now:
                    callback()
                else:
                    keep.append((callback, t))
            self.times = keep


def cleanup():
    proc1.terminate()
    proc2.terminate()
    proc1.wait()
    proc2.wait()


def render():
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(' '.join([now, reader1.line, reader2.line]))


def callback1():
    try:
        reader1.read_line()
    except ValueError:
        loop.unregister_file(proc1.stdout)
    render()


def callback2():
    try:
        reader2.read_line()
    except ValueError:
        loop.unregister_file(proc2.stdout)
    render()


proc1 = subprocess.Popen(['./random.sh'], stdout=subprocess.PIPE)
proc2 = subprocess.Popen(['./random.sh'], stdout=subprocess.PIPE)

reader1 = LineReader(proc1.stdout)
reader2 = LineReader(proc2.stdout)

loop = Loop()
loop.register_file(proc1.stdout, callback1)
loop.register_file(proc2.stdout, callback2)
loop.set_interval(render, 10)

try:
    loop.run()
finally:
    cleanup()
