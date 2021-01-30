class UserError(AssertionError):
    def __init__(self, message) -> None:
        self.message = message
        super().__init__(self.message)

    def __str__(self) -> str:
        return f"User Error: {self.message}"


class SpotifyUserError(AssertionError):
    def __init__(self, message) -> None:
        self.message = message
        super().__init__(self.message)

    def __str__(self) -> str:
        return f"User Spotify Error: {self.message}"


class InternalError(AssertionError):
    def __init__(self, message) -> None:
        self.message = message
        super().__init__(self.message)

    def __str__(self) -> str:
        return f"Internal Error: {self.message}"
