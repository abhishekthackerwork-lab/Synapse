class SecretBuffer:
    """
    Best-effort in-memory secret container.
    Uses mutable bytearray to allow explicit zeroization.
    """

    def __init__(self, secret: str):
        # Encode immediately; avoid keeping str around
        self._buf = bytearray(secret.encode("utf-8"))

    def get(self) -> bytes:
        return bytes(self._buf)

    def wipe(self):
        if self._buf is not None:
            for i in range(len(self._buf)):
                self._buf[i] = 0
            self._buf = None
