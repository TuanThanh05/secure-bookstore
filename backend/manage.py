import os
import sys

def main():
    # DJANGO_SETTINGS_MODULE=bookstore.settings.prod
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bookstore.settings.dev")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Please active .venv first. If you have not created a virtual environment, please run 'python -m venv .venv' to create one."
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()