from aiohttp import web

class WSChat:
    def __init__(self, host='0.0.0.0', port=8080):
        """
        Инициализация объекта WSChat.

        :param host: Хост для запуска сервера.
        :param port: Порт для запуска сервера.
        """
        self.host = host
        self.port = port
        self.connections = {}

    async def main_page(self, request):
        """
        Обработчик запроса главной страницы.
        Возвращает файловый ответ с содержимым файла index.html.

        :param request: Запрос.
        """
        return web.FileResponse('./index.html')

    async def handle_init_message(self, data, ws):
        """
        Обработка сообщения типа "INIT".

        :param data: Данные сообщения.
        :param ws: WebSocket соединение.
        """
        self.connections[data["id"]] = ws
        init_message = {'mtype': 'USER_ENTER', 'id': data["id"]}
        for client in self.connections.values():
            await client.send_json(init_message)

    async def handle_text_message(self, data, ws):
        """
        Обработка сообщения типа "TEXT".

        :param data: Данные сообщения.
        :param ws: WebSocket соединение.
        """
        message = data["text"]
        if data["to"]:
            direct_message = {'mtype': 'DM', 'id': data["id"], 'text': message}
            await self.connections[data["to"]].send_json(direct_message)
        else:
            broadcast_message = {'mtype': 'MSG', 'id': data["id"], 'text': message}
            for client in self.connections.values():
                if ws == client:
                    continue
                await client.send_json(broadcast_message)

    async def ws_handler(self, request):
        """
        Обработчик WebSocket соединения.
        """
        ws = web.WebSocketResponse()
        ws._autoclose = False
        await ws.prepare(request)

        async for msg in ws:
            try:
                data = msg.json()
            except:
                await ws.pong(b"pong")
                continue

            if data["mtype"] == "INIT":
                await self.handle_init_message(data, ws)
            elif data["mtype"] == "TEXT":
                await self.handle_text_message(data, ws)

        disconnected_client = self.find_disconnected(ws)
        del self.connections[disconnected_client]
        for client in self.connections.values():
            await client.send_json({'mtype': 'USER_LEAVE', 'id': disconnected_client})
        await ws.close()

    def find_disconnected(self, ws):
        """
        Поиск отключившегося клиента.

        :param ws: WebSocket соединение.
        :return: Идентификатор отключившегося клиента.
        """
        for client_id, connection in self.connections.items():
            if connection == ws:
                return client_id

    def run(self):
        """
        Запуск приложения.
        """
        app = web.Application()
        app.router.add_get('/', self.main_page)
        app.router.add_get('/chat', self.ws_handler)
        web.run_app(app, host=self.host, port=self.port)

if __name__ == '__main__':
    WSChat().run()