import asyncio


class Future:
    def __init__(self):
        self.callbacks = []
        self.result = None
        self.exception = None
        self.done = False

    def _set_done(self):
        self.done = True
        for callback in self.callbacks:
            callback(self)

    def set_result(self, result):
        self.result = result
        self._set_done()

    def set_exception(self, exception):
        self.exception = exception
        self._set_done()

    def add_done_callback(self, callback):
        self.callbacks.append(callback)

    def __await__(self):
        yield self


class Task:
    def __init__(self, coro):
        self.gen = coro.__await__()

    def wakeup(self, future=None):
        try:
            if future and future.exception:
                new_future = self.gen.throw(future.exception)
            else:
                new_future = next(self.gen)
            new_future.add_done_callback(self.wakeup)
        except StopIteration:
            pass


async def sleep(t):
    future = Future()
    loop.call_later(t, future.set_result, None)
    await future


async def amain():
    print('start')
    try:
        await sleep(5)
        loop.stop()
    finally:
        print('finish')


loop = asyncio.new_event_loop()
task = Task(amain())
task.wakeup()
loop.run_forever()
