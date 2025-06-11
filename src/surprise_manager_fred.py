import io
from PIL import Image # Pillow library for image processing

class SurpriseManager:
    def __init__(self):
        # This is where you can initialize your model and any static
        # configurations. For this specific problem, no complex
        # model loading is needed, but Pillow will be used.
        pass

    def _get_edges_from_image_bytes(self, image_bytes: bytes) -> tuple[list[tuple[int, int, int]], list[tuple[int, int, int]], int]:
        """
        Decodes image bytes, opens the image using Pillow, 
        and extracts the pixel data for its leftmost and rightmost columns.
        Returns (left_edge_pixels, right_edge_pixels, height).
        """
        try:
            img = Image.open(io.BytesIO(image_bytes))
            img = img.convert("RGB")  # Ensure image is in RGB format
            width, height = img.size
            
            left_edge_pixels = []
            for y in range(height):
                left_edge_pixels.append(img.getpixel((0, y)))  # (R, G, B) tuple
            
            right_edge_pixels = []
            for y in range(height):
                right_edge_pixels.append(img.getpixel((width - 1, y)))  # (R, G, B) tuple
            
            return left_edge_pixels, right_edge_pixels, height
        except Exception as e:
            # Log or handle specific image processing errors if necessary
            print(f"Error processing image with Pillow: {e}")
            raise  # Re-raise to be handled by the caller (surprise method)

    def _calculate_edge_difference(self, edge1_pixels: list[tuple[int, int, int]], edge2_pixels: list[tuple[int, int, int]], height: int) -> int:
        """
        Calculates the Sum of Absolute Differences (SAD) between two edge pixel columns.
        Assumes edge1_pixels and edge2_pixels are lists of (R, G, B) tuples.
        """
        if len(edge1_pixels) != height or len(edge2_pixels) != height:
            # This should not happen if all slices have the same height as guaranteed
            # and _get_edges_from_image_bytes works correctly.
            raise ValueError("Edge pixel lists have different heights than expected or processing failed.")

        total_difference = 0
        for i in range(height):
            p1 = edge1_pixels[i]
            p2 = edge2_pixels[i]
            total_difference += abs(p1[0] - p2[0]) + \
                                abs(p1[1] - p2[1]) + \
                                abs(p1[2] - p2[2])
        return total_difference

    def surprise(self, slices_bytes: list[bytes]) -> list[int]:
        """
        Reconstructs shredded document from vertical slices.

        Args:
            slices_bytes: list of byte arrays, each representing a JPEG-encoded vertical slice.

        Returns:
            Predicted permutation of input slices to correctly reassemble the document.
        """
        num_slices = len(slices_bytes)
        if num_slices == 0:
            return []
        if num_slices == 1:
            return [0]  # A single slice is already "assembled"

        # 1. Extract edge data for all slices
        slice_edge_data = []  # Store dicts: {"id": original_index, "left_edge": ..., "right_edge": ..., "height": ...}
        common_height = None

        for i, image_data_bytes in enumerate(slices_bytes):
            try:
                left_edge, right_edge, height = self._get_edges_from_image_bytes(image_data_bytes)
                
                if common_height is None:
                    common_height = height
                elif common_height != height:
                    # This contradicts the problem statement's guarantee.
                    print(f"Warning: Slices have inconsistent heights (slice {i} has {height}, expected {common_height}). This instance may fail.")
                    # Fallback for this instance if heights are inconsistent
                    return list(range(num_slices))

                slice_edge_data.append({
                    "id": i,  # Original index of the slice
                    "left_edge": left_edge,
                    "right_edge": right_edge,
                    "height": height # Stored for consistency, should be common_height
                })
            except Exception as e:
                print(f"Error processing slice {i}: {e}. Returning original order for this instance.")
                # If a slice is corrupt or unprocessable, fallback for this document instance.
                return list(range(num_slices))
        
        if not common_height or not slice_edge_data: # If no valid slices were processed
             print("No valid slice data could be extracted. Returning original order.")
             return list(range(num_slices))

        # 2. Calculate Dissimilarity Matrix: D[i][j]
        # D[original_idx_i][original_idx_j] = difference between RIGHT edge of slice i 
        #                                       and LEFT edge of slice j.
        dissimilarity_matrix = [[float('inf')] * num_slices for _ in range(num_slices)]

        for i in range(num_slices):
            for j in range(num_slices):
                if i == j:  # A slice cannot connect to itself
                    continue
                
                # slice_edge_data is indexed 0 to num_slices-1, and 'id' also corresponds to this
                data_i = slice_edge_data[i] 
                data_j = slice_edge_data[j]

                # All slices should have common_height
                diff = self._calculate_edge_difference(data_i["right_edge"], data_j["left_edge"], common_height)
                dissimilarity_matrix[data_i["id"]][data_j["id"]] = diff
            
        # 3. Find the Best Permutation using a Greedy Approach
        # Try each slice as a potential starting slice
        best_overall_permutation = []
        min_overall_dissimilarity = float('inf')

        for start_slice_original_idx in range(num_slices):
            current_permutation_indices = [start_slice_original_idx] # List of original indices
            current_total_dissimilarity = 0
            used_slices_original_indices = {start_slice_original_idx}
            
            last_slice_in_chain_idx = start_slice_original_idx

            while len(current_permutation_indices) < num_slices:
                best_next_slice_idx = -1
                min_connection_diff = float('inf')

                # Find the unused slice 'k_idx' whose LEFT edge best matches
                # the RIGHT edge of 'last_slice_in_chain_idx'.
                for k_idx in range(num_slices): # k_idx is an original index
                    if k_idx not in used_slices_original_indices:
                        # Cost to connect right of 'last_slice_in_chain_idx' to left of 'k_idx'
                        cost = dissimilarity_matrix[last_slice_in_chain_idx][k_idx]
                        if cost < min_connection_diff:
                            min_connection_diff = cost
                            best_next_slice_idx = k_idx
                
                if best_next_slice_idx != -1: # Found a slice to connect
                    current_permutation_indices.append(best_next_slice_idx)
                    used_slices_original_indices.add(best_next_slice_idx)
                    current_total_dissimilarity += min_connection_diff
                    last_slice_in_chain_idx = best_next_slice_idx
                else:
                    # Could not find a next slice to connect; this chain is broken.
                    # This implies the set of slices might not form a single contiguous document,
                    # or the dissimilarity scores are misleading.
                    break 
            
            if len(current_permutation_indices) == num_slices:  # A full permutation was found
                if current_total_dissimilarity < min_overall_dissimilarity:
                    min_overall_dissimilarity = current_total_dissimilarity
                    best_overall_permutation = current_permutation_indices
        
        if not best_overall_permutation: # Fallback if no complete permutation was found
            print("Warning: Could not form a complete permutation. Returning original order.")
            return list(range(num_slices))

        return best_overall_permutation
