"""Handle the SAX exception-length quirk (REQ-EXTENDED-MODE-RESILIENCE)."""

from __future__ import annotations


class SaxModbusPacketTrace:
    """Preserve device rejection when firmware echoes a write's MBAP length."""

    def __init__(self, device_id: int) -> None:
        self._device_id = device_id
        self._request: bytes | None = None

    def __call__(self, sending: bool, data: bytes) -> bytes:
        """Adapt only a matching FC06 exception; never manufacture an ACK."""
        if sending:
            self._request = (
                data
                if len(data) == 12
                and data[2:6] == b"\x00\x00\x00\x06"
                and data[6] == self._device_id
                and data[7] == 6
                else None
            )
            return data

        request = self._request
        if (
            request is not None
            and len(data) >= 9
            and data[:7] == request[:7]
            and data[7] == 0x86
            and data[8] in (1, 2, 3, 4, 5, 6, 8, 10, 11)
        ):
            # The gateway returns nine bytes but copies length=6 from FC06.
            # Keep the byte count unchanged: pymodbus owns TCP reassembly and
            # consumes the returned frame length from its original buffer.
            return data[:4] + b"\x00\x03" + data[6:]
        return data
