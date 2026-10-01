"""Actor-visible retry and wait-composition smoke checks."""
from tenacity import Retrying, RetryCallState, stop_after_attempt, wait_combine, wait_fixed


def main() -> None:
    attempts = []

    def flaky():
        attempts.append(1)
        if len(attempts) == 1:
            raise ValueError("try again")
        return "ok"

    assert Retrying(wait=None, stop=stop_after_attempt(2))(flaky) == "ok"
    assert len(attempts) == 2
    state = RetryCallState(Retrying(), None, (), {})
    assert wait_combine(wait_fixed(1), lambda attempt: 2)(state) == 3


if __name__ == "__main__":
    main()
