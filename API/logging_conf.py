from logging.config import dictConfig
import logging


def configure_logging(debug: bool = True) -> None:
    dictConfig({
        "version": 1,
        "disable_existing_loggers": False,

        # ── FORMATTERS ─────────────────────────────
        "formatters": {
            "simple": {
                "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            }
        },

        # ── HANDLERS ───────────────────────────────
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": "DEBUG" if debug else "INFO",
                "formatter": "simple",
            },
            "file": {
                "class": "logging.FileHandler",
                "filename": "app.log",
                "level": "DEBUG",
                "formatter": "simple",
            },
        },

        # ── ROOT LOGGER ────────────────────────────
        "root": {
            "handlers": ["console", "file"],
            "level": "DEBUG" if debug else "INFO",
        },

        # ── YOUR APP LOGGER ────────────────────────
        "loggers": {
            "hebrew_vocab_hub": {
                "handlers": ["console", "file"],
                "level": "DEBUG" if debug else "INFO",
                "propagate": False,
            }
        }
    })