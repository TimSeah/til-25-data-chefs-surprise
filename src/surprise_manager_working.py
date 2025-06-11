import io
from PIL import Image # Pillow library for image processing
import sys # For float('inf') if needed, though float('inf') is standard

class SurpriseManager:
    def __init__(self):
        # Initialization for your manager
        pass

    def _get_edges_from_image_bytes(self, image_bytes: bytes) -> tuple[list[tuple[int, int, int]], list[tuple[int, int, int]], int]:
        """
        Decodes image bytes, opens the image using Pillow, 
        and extracts the pixel data for its leftmost and rightmost columns.
        Returns (left_edge_pixels, right_edge_pixels, height).
        Corresponds to: Initial image processing and edge data extraction.
        """
        try:
            img = Image.open(io.BytesIO(image_bytes))
            img = img.convert("RGB")  # Ensure image is in RGB format
            width, height = img.size
            
            left_edge_pixels = []
            for y in range(height):
                left_edge_pixels.append(img.getpixel((0, y)))
            
            right_edge_pixels = []
            for y in range(height):
                right_edge_pixels.append(img.getpixel((width - 1, y)))
            
            return left_edge_pixels, right_edge_pixels, height
        except Exception as e:
            print(f"Error processing image with Pillow: {e}")
            raise

    def _calculate_edge_difference(self, edge1_pixels: list[tuple[int, int, int]], edge2_pixels: list[tuple[int, int, int]], height: int) -> int:
        """
        Calculates the Sum of Absolute Differences (SAD) between two edge pixel columns.
        Corresponds to: The cost function (calculate_edge_difference in the standalone script).
        """
        if len(edge1_pixels) != height or len(edge2_pixels) != height:
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
        Reconstructs shredded document from vertical slices using a graph-based greedy approach.

        Args:
            slices_bytes: list of byte arrays, each representing a JPEG-encoded vertical slice.

        Returns:
            Predicted permutation of input slices to correctly reassemble the document.
        """
        num_slices = len(slices_bytes)
        if num_slices == 0:
            return []
        if num_slices == 1:
            return [0]

        # Step 1: Extract edge data for all slices
        slice_edge_data = []
        common_height = None

        for i, image_data_bytes in enumerate(slices_bytes):
            try:
                left_edge, right_edge, height = self._get_edges_from_image_bytes(image_data_bytes)
                
                if common_height is None:
                    common_height = height
                elif common_height != height:
                    print(f"Warning: Slices have inconsistent heights (slice {i} has {height}, expected {common_height}). This instance may fail.")
                    return list(range(num_slices))

                slice_edge_data.append({
                    "id": i,
                    "left_edge": left_edge,
                    "right_edge": right_edge,
                    "height": height
                })
            except Exception as e:
                print(f"Error processing slice {i}: {e}. Returning original order for this instance.")
                return list(range(num_slices))
        
        if not common_height or not slice_edge_data:
             print("No valid slice data could be extracted. Returning original order.")
             return list(range(num_slices))

        # Step 2: Calculate Dissimilarity Matrix (Cost Matrix)
        # Corresponds to: build_cost_matrix from the standalone script.
        dissimilarity_matrix = [[float('inf')] * num_slices for _ in range(num_slices)]

        for i in range(num_slices):
            for j in range(num_slices):
                if i == j:
                    continue
                
                data_i = slice_edge_data[i] 
                data_j = slice_edge_data[j]

                diff = self._calculate_edge_difference(data_i["right_edge"], data_j["left_edge"], common_height)
                dissimilarity_matrix[data_i["id"]][data_j["id"]] = diff # Cost from slice i to slice j
            
        # Step 3: Find the Best Permutation using a Greedy Approach
        # Corresponds to: find_best_permutation_greedy from the standalone script.
        best_overall_permutation = []
        min_overall_dissimilarity = float('inf')

        for start_slice_original_idx in range(num_slices):
            current_permutation_indices = [start_slice_original_idx]
            current_total_dissimilarity = 0
            used_slices_original_indices = {start_slice_original_idx}
            last_slice_in_chain_idx = start_slice_original_idx

            while len(current_permutation_indices) < num_slices:
                best_next_slice_idx = -1
                min_connection_diff = float('inf')

                for k_idx in range(num_slices):
                    if k_idx not in used_slices_original_indices:
                        cost = dissimilarity_matrix[last_slice_in_chain_idx][k_idx]
                        if cost < min_connection_diff:
                            min_connection_diff = cost
                            best_next_slice_idx = k_idx
                
                if best_next_slice_idx != -1:
                    current_permutation_indices.append(best_next_slice_idx)
                    used_slices_original_indices.add(best_next_slice_idx)
                    current_total_dissimilarity += min_connection_diff
                    last_slice_in_chain_idx = best_next_slice_idx
                else:
                    break 
            
            if len(current_permutation_indices) == num_slices:
                if current_total_dissimilarity < min_overall_dissimilarity:
                    min_overall_dissimilarity = current_total_dissimilarity
                    best_overall_permutation = current_permutation_indices
        
        if not best_overall_permutation:
            print("Warning: Could not form a complete permutation. Returning original order.")
            return list(range(num_slices))

        return best_overall_permutation