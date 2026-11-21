from django.core.mail.backends.console import EmailBackend as ConsoleEmailBackend


class ReadableConsoleEmailBackend(ConsoleEmailBackend):
    def write_message(self, message):
        self.stream.write(
            f"To: {', '.join(message.recipients())}\n"
            f"Subject: {message.subject}\n\n"
            f"{message.body}\n"
            f"{'-' * 79}\n"
        )
