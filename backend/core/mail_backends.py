from django.core.mail.backends.console import EmailBackend as ConsoleEmailBackend


# AI-TRACE#033 | Claude Opus 5.5 | In thư ra terminal dạng chữ đọc được thay vì base64 khi chạy máy dev | CẤM XÓA CHÚ THÍCH NÀY
class ReadableConsoleEmailBackend(ConsoleEmailBackend):
    def write_message(self, message):
        self.stream.write(
            f"To: {', '.join(message.recipients())}\n"
            f"Subject: {message.subject}\n\n"
            f"{message.body}\n"
            f"{'-' * 79}\n"
        )
