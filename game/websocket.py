import asyncio
from asyncio.queues import Queue
import websockets
import threading


class WebSocketServer:
    def start(self):
        raise NotImplementedError

    def stop(self):
        raise NotImplementedError


class AsyncioWebSocketServer(WebSocketServer):
    """ accept_connection: (send_message: String ->, close_connection: ->)
                                -> open: ->, on_message: String ->, on_close: -> """
    def __init__(self, port, accept_connection):
        super().__init__()
        self._thread = _AsyncioWebSocketThread(port, accept_connection)

    def start(self):
        self._thread.start()

    def stop(self):
        # hmmm...
        pass


class _AsyncioWebSocketThread(threading.Thread):
    def __init__(self, port, accept_connection):
        super().__init__()
        self._port = port
        self._accept_connection = accept_connection
        self._loop = None

    def run(self):
        print('[WebSocketThread] Starting...')
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)

        server = websockets.serve(self._handler, '127.0.0.1', self._port, loop=self._loop)

        print('[WebSocketThread] Now listening on ws://127.0.0.1:'+str(self._port)+'/')
        self._loop.run_until_complete(server)
        self._loop.run_forever()

    async def _handler(self, websocket, path):
        print('[WebSocketThread] Incoming connection')
        queue = Queue()

        async def send_message_async(message):
            await queue.put(message)

        def send_message(message):
            asyncio.run_coroutine_threadsafe(send_message_async(message), self._loop)

        def close():
            send_message(None)

        on_open, on_message, on_close = self._accept_connection(send_message, close)

        on_open()
        listener_task = asyncio.ensure_future(websocket.recv())
        producer_task = asyncio.ensure_future(queue.get())
        try:
            while True:
                done, pending = await asyncio.wait(
                    [listener_task, producer_task],
                    return_when=asyncio.FIRST_COMPLETED)

                if listener_task in done:
                    message = listener_task.result()
                    on_message(message)
                    listener_task = asyncio.ensure_future(websocket.recv())

                if producer_task in done:
                    message = producer_task.result()
                    if message is None:
                        break
                    producer_task = asyncio.ensure_future(queue.get())
                    await websocket.send(message)
        finally:
            listener_task.cancel()
            producer_task.cancel()
            on_close()
            print('[WebSocketThread] Connection closed')
