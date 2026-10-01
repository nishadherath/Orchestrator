"""Actor-visible serialisation smoke checks."""
import pickle

from packaging.markers import Marker
from packaging.requirements import Requirement


def main() -> None:
    marker = Marker('python_version >= "3.10" and os_name == "posix"')
    assert pickle.loads(pickle.dumps(marker)) == marker
    requirement = Requirement('sample[feature]>=2; python_version >= "3.10"')
    assert pickle.loads(pickle.dumps(requirement)) == requirement


if __name__ == "__main__":
    main()
