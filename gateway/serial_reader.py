"""Serial reader abstraction with automatic reconnection."""

from __future__ import annotations

import logging
import time
from typing import Optional

try:  # pragma: no cover - optional hardware dependency
    import serial  # type: ignore
    from serial.serialutil import SerialException  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - fallback for tests
    serial = None

    class SerialException(Exception):
        """Placeholder exception when pyserial is unavailable."""


class SerialReader:
    """Read newline-delimited messages from a serial port."""

    def __init__(
        self,
        port: str,
        baudrate: int,
        reconnect_interval: float = 5.0,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        self.port = port
        self.baudrate = baudrate
        self.reconnect_interval = reconnect_interval
        self._serial: Optional["serial.Serial"] = None  # type: ignore[name-defined]
        self.logger = logger or logging.getLogger(self.__class__.__name__)

    @property
    def is_connected(self) -> bool:
        return bool(self._serial and self._serial.is_open)

    def connect(self) -> None:
        """Attempt to establish the serial connection."""

        if serial is None:
            raise ImportError(
                "pyserial is required to use SerialReader. Install 'pyserial' or run in simulation mode."
            )

        while not self.is_connected:
            try:
                self.logger.info(
                    "Opening serial port %s at %s baud", self.port, self.baudrate
                )
                self._serial = serial.Serial(  # type: ignore[attr-defined]
                    self.port,
                    self.baudrate,
                    timeout=1,
                )
                self.logger.info("Serial connection established")
            except SerialException as exc:
                self.logger.warning(
                    "Unable to open serial port %s: %s. Retrying in %ss",
                    self.port,
                    exc,
                    self.reconnect_interval,
                )
                time.sleep(self.reconnect_interval)

    def close(self) -> None:
        if self._serial and self._serial.is_open:
            self.logger.info("Closing serial connection")
            self._serial.close()

    def read_line(self) -> Optional[str]:
        """Read a line from the serial connection."""

        if not self.is_connected:
            self.connect()

        if not self._serial:
            return None

        try:
            raw = self._serial.readline().decode("utf-8", errors="ignore").strip()
            if raw:
                self.logger.debug("Read from serial: %s", raw)
            return raw or None
        except SerialException as exc:
            self.logger.error("Serial read failed: %s", exc)
            self.close()
            time.sleep(self.reconnect_interval)
            return None
