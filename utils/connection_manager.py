from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        self.active_connections = []

    async def connect(self, web_socket: WebSocket):
        await web_socket.accept()
        self.active_connections.append(web_socket)

    def disconnect(self, web_socket: WebSocket):
        self.active_connections.remove(web_socket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)
        
connection = ConnectionManager()
