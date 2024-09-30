import abc


class CollectionObject(abc.ABC):
    """Any object that can appear on a collection."""

    def __init__(self):
        pass

    @property
    @abc.abstractmethod
    def labels(self) -> set[str]:
        """Returns all labels found in this object."""
        pass

    def clean_labels(self, labels: set[str]) -> set[str]:
        return {l.strip() for l in labels if len(l.strip()) > 0}
