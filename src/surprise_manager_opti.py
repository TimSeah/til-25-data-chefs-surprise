import io
from PIL import Image
import numpy as np # Import NumPy
import sys # For float('inf')

class SurpriseManager:
    def __init__(self):
        pass

    def _get_edges_from_image_bytes(self, image_bytes: bytes) -> tuple[np.ndarray, np.ndarray, int]:
        """
        Decodes image bytes, opens the image, converts to a NumPy array,
        and extracts the leftmost and rightmost column arrays.
        Returns (left_edge_array, right_edge_array, height).
        """
        try:
            img_pil = Image.open(io.BytesIO(image_bytes))
            img_pil = img_pil.convert("RGB")  # Ensure image is in RGB format
            
            # Convert PIL Image to NumPy array
            img_array = np.array(img_pil) # Shape: (height, width, channels)
            
            height = img_array.shape[0]
            
            # Extract left and right edges using NumPy slicing
            # Left edge: all rows, first column of pixels, all color channels
            left_edge_array = img_array[:, 0, :]
            # Right edge: all rows, last column of pixels, all color channels
            right_edge_array = img_array[:, -1, :]
            
            return left_edge_array, right_edge_array, height
        except Exception as e:
            print(f"Error processing image with Pillow/NumPy: {e}")
            raise

    def _calculate_edge_difference_numpy(self, edge1_array: np.ndarray, edge2_array: np.ndarray) -> float:
        """
        Calculates the Sum of Absolute Differences (SAD) between two edge arrays using NumPy.
        Assumes edge1_array and edge2_array are NumPy arrays of shape (height, channels).
        """
        # Ensure arrays are float32 for subtraction to prevent overflow/underflow with uint8
        # and to ensure the result of np.sum can be a float.
        diff = np.sum(np.abs(edge1_array.astype(np.float32) - edge2_array.astype(np.float32)))
        return float(diff)


    def surprise(self, slices_bytes: list[bytes]) -> list[int]:
        """
        Reconstructs shredded document from vertical slices using NumPy for speed.
        """
        num_slices = len(slices_bytes)
        if num_slices == 0:
            return []
        if num_slices == 1:
            return [0]

        slice_edge_data = []
        common_height = None

        for i, image_data_bytes in enumerate(slices_bytes):
            try:
                # Use the new NumPy-based edge extraction
                left_edge, right_edge, height = self._get_edges_from_image_bytes(image_data_bytes)
                
                if common_height is None:
                    common_height = height
                elif common_height != height:
                    print(f"Warning: Slices have inconsistent heights (slice {i} has {height}, expected {common_height}).")
                    return list(range(num_slices)) # Fallback

                slice_edge_data.append({
                    "id": i,
                    "left_edge_arr": left_edge,  # Store NumPy array
                    "right_edge_arr": right_edge, # Store NumPy array
                    # "height" is implicitly common_height or checked
                })
            except Exception as e:
                print(f"Error processing slice {i}: {e}. Returning original order.")
                return list(range(num_slices))
        
        if not common_height or not slice_edge_data:
             print("No valid slice data could be extracted. Returning original order.")
             return list(range(num_slices))

        dissimilarity_matrix = [[float('inf')] * num_slices for _ in range(num_slices)]

        for i in range(num_slices):
            for j in range(num_slices):
                if i == j:
                    continue
                
                data_i = slice_edge_data[i] 
                data_j = slice_edge_data[j]
                
                # Use the new NumPy-based difference calculation
                diff = self._calculate_edge_difference_numpy(data_i["right_edge_arr"], data_j["left_edge_arr"])
                dissimilarity_matrix[data_i["id"]][data_j["id"]] = diff
            
        best_overall_permutation = []
        min_overall_dissimilarity = float('inf')

        for start_slice_original_idx in range(num_slices):
            current_permutation_indices = [start_slice_original_idx]
            current_total_dissimilarity = 0.0 # Ensure float for costs
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
                    if min_connection_diff != float('inf'): # Avoid adding infinity if a path is broken
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
