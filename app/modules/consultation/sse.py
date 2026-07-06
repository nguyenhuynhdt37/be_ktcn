import asyncio
import json
from typing import Any


class SSEManager:
    """
    Quản lý các kết nối Server-Sent Events (SSE) realtime từ các admin.
    """
    def __init__(self):
        self.active_connections: list[asyncio.Queue] = []

    def connect(self) -> asyncio.Queue:
        """Đăng ký một kết nối admin mới."""
        queue = asyncio.Queue()
        self.active_connections.append(queue)
        return queue

    def disconnect(self, queue: asyncio.Queue):
        """Hủy đăng ký kết nối khi admin tắt tab/mất kết nối."""
        if queue in self.active_connections:
            self.active_connections.remove(queue)

    async def pub_event(self, event_type: str, data: Any):
        """Bắn sự kiện realtime cho toàn bộ admin đang online."""
        message = {
            "event": event_type,
            "data": data
        }
        sse_formatted_msg = f"data: {json.dumps(message)}\n\n"
        
        # Tạo danh sách các task gửi đồng thời để tránh chặn
        tasks = []
        for queue in self.active_connections:
            tasks.append(asyncio.create_task(queue.put(sse_formatted_msg)))
            
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)


sse_manager = SSEManager()
