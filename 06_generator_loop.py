import datetime
import os
import selectors
import subprocess
import time

selector = selectors.DefaultSelector()
data = ['', '', '']


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


class Task:
    def __init__(self, gen):
        self.gen = gen
        self.files = set()
        self.times = {0}
        self.init = False
        self.done = False
        self.result = None

    def select(self):
        now = time.time()
        timeout = min((t - now for t in self.times), default=None)
        return {key.fileobj for key, mask in selector.select(timeout)}

    def step(self, files, now):
        try:
            if self.done:
                return
            elif not self.init:
                self.files, self.times = next(self.gen)
                self.init = True
            elif any(t < now for t in self.times) or files & self.files:
                self.files, self.times = self.gen.send((files, now))
        except StopIteration as e:
            self.done = True
            self.result = e.value

    def close(self):
        self.gen.close()


def sleep(t):
    yield set(), {time.time() + t}


def gather(*generators):
    subtasks = [Task(gen) for gen in generators]
    try:
        while True:
            wait_files = set().union(
                *[t.files for t in subtasks if not t.done]
            )
            wait_times = set().union(
                *[t.times for t in subtasks if not t.done]
            )
            files, now = yield wait_files, wait_times
            for task in subtasks:
                task.step(files, now)
            if all(task.done for task in subtasks):
                return [task.result for task in subtasks]
    finally:
        for task in subtasks:
            task.close()


def run(gen):
    task = Task(gen)
    try:
        while not task.done:
            files = task.select()
            task.step(files, time.time())
        return task.result
    finally:
        task.close()


def render():
    data[0] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(' '.join(data))


def clock():
    while True:
        yield from sleep(10)
        render()


def popen(cmd, i):
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    reader = LineReader(proc.stdout)
    selector.register(proc.stdout, selectors.EVENT_READ)
    try:
        while True:
            yield {proc.stdout}, set()
            try:
                reader.read_line()
                data[i] = reader.line
                render()
            except ValueError:
                break
    finally:
        selector.unregister(proc.stdout)
        proc.terminate()
        proc.wait()


def amain():
    yield from gather(
        popen(['./random.sh'], 1),
        popen(['./random.sh'], 2),
        clock(),
    )


run(amain())
