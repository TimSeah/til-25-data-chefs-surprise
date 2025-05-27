class SurpriseManager:
    def __init__(self):
        # This is where you can initialize your model and any static
        # configurations.
        pass

    def surprise(self, slices: list[bytes]) -> list[int]:
        """
        Reconstructs shredded document from vertical slices.

        Args:
            slices: list of byte arrays, each representing a JPEG-encoded vertical slice of the input document

        Returns:
            Predicted permutation of input slices to correctly reassemble the document.
        """

        # Your inference code goes here.

        return list(range(len(slices)))
    