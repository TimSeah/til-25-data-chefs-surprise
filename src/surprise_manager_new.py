import io
from PIL import Image
import numpy as np
import sys # For float('inf')

class SurpriseManager:
    def __init__(self):
        self.epsilon = 1e-9 # Small number to prevent division by zero

    def _get_grayscale_edges_from_image_bytes(self, image_bytes: bytes) -> tuple[np.ndarray | None, np.ndarray | None, int]:
        """
        Decodes image bytes, converts to a NumPy array (grayscale),
        and extracts the leftmost and rightmost grayscale column arrays.
        Returns (left_edge_gray_array, right_edge_gray_array, height).
        Returns None for arrays if image processing fails.
        """
        try:
            img_pil = Image.open(io.BytesIO(image_bytes))
            # Convert to grayscale first, then to NumPy array
            img_pil_gray = img_pil.convert("L") # 'L' mode for grayscale
            img_array_gray = np.array(img_pil_gray, dtype=np.float32) # Shape: (height, width)
            
            height = img_array_gray.shape[0]
            
            left_edge_gray = img_array_gray[:, 0]    # Shape: (height,)
            right_edge_gray = img_array_gray[:, -1]  # Shape: (height,)
            
            return left_edge_gray, right_edge_gray, height
        except Exception as e:
            print(f"Error processing image to grayscale edges: {e}")
            # Return None for edges to indicate failure at this stage
            return None, None, 0


    def _calculate_ncc_cost(self, edge1_gray: np.ndarray, edge2_gray: np.ndarray) -> float:
        """
        Calculates cost based on Normalized Cross-Correlation (NCC) between two grayscale edges.
        Cost = 1.0 - NCC. NCC is between -1 and 1. Cost is between 0 (perfect) and 2 (perfect inverse).
        """
        if edge1_gray is None or edge2_gray is None or edge1_gray.size == 0 or edge2_gray.size == 0:
            return 2.0 # Max cost if edges are invalid

        mean1 = np.mean(edge1_gray)
        mean2 = np.mean(edge2_gray)
        
        std1 = np.std(edge1_gray)
        std2 = np.std(edge2_gray)

        # Handle flat edges (std_dev close to zero)
        if std1 < self.epsilon and std2 < self.epsilon: # Both are flat
            return 0.0 if np.abs(mean1 - mean2) < self.epsilon else 1.0 # Cost 0 if same flat color, else 1
        if std1 < self.epsilon or std2 < self.epsilon: # One is flat
            return 1.0 # NCC is effectively 0, so cost is 1.0

        numerator = np.sum((edge1_gray - mean1) * (edge2_gray - mean2))
        denominator = std1 * std2 * edge1_gray.size # Or use (N-1)*std1*std2 if std is sample std_dev

        # Using the direct formula for Pearson correlation coefficient which is equivalent to NCC for 1D signals
        # Pearson r = cov(X, Y) / (std_dev(X) * std_dev(Y))
        # cov(X,Y) = E[(X-EX)(Y-EY)]
        # numerator = np.sum((edge1_gray - mean1) * (edge2_gray - mean2))
        # denominator_sqrt_part1 = np.sqrt(np.sum((edge1_gray - mean1)**2))
        # denominator_sqrt_part2 = np.sqrt(np.sum((edge2_gray - mean2)**2))
        # ncc = numerator / (denominator_sqrt_part1 * denominator_sqrt_part2 + self.epsilon) # Add epsilon to avoid div by zero

        # Simplified calculation of NCC for zero-mean unit-variance signals
        norm_edge1 = (edge1_gray - mean1) / (std1 + self.epsilon)
        norm_edge2 = (edge2_gray - mean2) / (std2 + self.epsilon)
        ncc = np.mean(norm_edge1 * norm_edge2) # This is equivalent to Pearson correlation

        # Ensure NCC is within [-1, 1] due to potential floating point inaccuracies
        ncc = np.clip(ncc, -1.0, 1.0)
        
        return 1.0 - ncc

    def _calculate_total_path_cost(self, permutation: list[int], cost_matrix: list[list[float]], num_strips: int) -> float:
        if not permutation or num_strips <= 1:
            return 0.0
        
        total_cost = 0.0
        for k in range(num_strips - 1):
            idx1 = permutation[k]
            idx2 = permutation[k+1]
            cost = cost_matrix[idx1][idx2]
            if cost == float('inf'): # Should not happen in a valid path from greedy
                return float('inf') 
            total_cost += cost
        return total_cost

    def _apply_2_opt(self, initial_permutation: list[int], cost_matrix: list[list[float]], num_strips: int):
        if num_strips < 4: # 2-Opt needs at least 4 nodes to make a non-trivial swap
            return initial_permutation

        current_permutation = list(initial_permutation)
        
        improved = True
        while improved:
            improved = False
            min_delta = 0.0 # Track if any improvement is made

            for i in range(num_strips - 2): # First edge is (p[i], p[i+1])
                for j in range(i + 2, num_strips -1): # Second edge is (p[j], p[j+1])
                                                      # Segment to reverse is p[i+1]...p[j]
                    
                    # Current cost of the two edges being considered for swap
                    cost_before = cost_matrix[current_permutation[i]][current_permutation[i+1]] + \
                                  cost_matrix[current_permutation[j]][current_permutation[j+1]]
                    
                    # Cost if we swap: p[i]->p[j] and p[i+1]->p[j+1]
                    cost_after = cost_matrix[current_permutation[i]][current_permutation[j]] + \
                                 cost_matrix[current_permutation[i+1]][current_permutation[j+1]]

                    delta = cost_after - cost_before

                    if delta < min_delta and delta < -self.epsilon : # Significant improvement
                        # Perform the 2-opt swap (reverse segment)
                        segment_to_reverse = current_permutation[i+1 : j+1] # Slice is exclusive at end
                        segment_to_reverse.reverse()
                        current_permutation = current_permutation[:i+1] + segment_to_reverse + current_permutation[j+1:]
                        
                        improved = True
                        min_delta = delta # Update for "best improvement" in this pass, or just use first improvement
                        # For "first improvement", we would break here and restart the while improved loop
                        # For "best improvement", we continue inner loops and apply the best swap of the pass
            
            # Using "first improvement" for simplicity and often faster convergence in practice
            if improved: 
                continue # Restart the while loop to re-evaluate from the beginning of the new path

        return current_permutation


    def surprise(self, slices_bytes: list[bytes]) -> list[int]:
        num_slices = len(slices_bytes)
        if num_slices == 0:
            return []
        if num_slices == 1:
            return [0]

        slice_edge_data = []
        # Common height is not strictly needed if edges are 1D arrays, but good for validation
        # common_height = None 

        for i, image_data_bytes in enumerate(slices_bytes):
            try:
                left_edge_gray, right_edge_gray, height = self._get_grayscale_edges_from_image_bytes(image_data_bytes)
                if left_edge_gray is None or right_edge_gray is None or height == 0: # Check for processing failure
                    print(f"Failed to get valid edges for slice {i}. Returning original order.")
                    return list(range(num_slices))

                # if common_height is None:
                #     common_height = height
                # elif common_height != height: # Should be guaranteed by problem spec
                #     print(f"Warning: Slices have inconsistent heights. This instance may fail.")
                #     return list(range(num_slices))

                slice_edge_data.append({
                    "id": i,
                    "left_edge_arr": left_edge_gray,
                    "right_edge_arr": right_edge_gray,
                })
            except Exception as e: # Catch any other unexpected error during loop
                print(f"Error processing slice {i} in main loop: {e}. Returning original order.")
                return list(range(num_slices))
        
        if not slice_edge_data: # Should be caught by num_slices check, but defensive
             print("No valid slice data. Returning original order.")
             return list(range(num_slices))

        # --- Build Dissimilarity (Cost) Matrix using NCC ---
        dissimilarity_matrix = [[float('inf')] * num_slices for _ in range(num_slices)]
        for i in range(num_slices):
            for j in range(num_slices):
                if i == j:
                    continue
                data_i = slice_edge_data[i] 
                data_j = slice_edge_data[j]
                cost = self._calculate_ncc_cost(data_i["right_edge_arr"], data_j["left_edge_arr"])
                dissimilarity_matrix[data_i["id"]][data_j["id"]] = cost
            
        # --- Greedy Algorithm to find initial permutation ---
        initial_permutation = []
        min_overall_greedy_cost = float('inf')

        for start_slice_original_idx in range(num_slices):
            current_permutation_indices = [start_slice_original_idx]
            current_total_cost = 0.0
            used_slices_original_indices = {start_slice_original_idx}
            last_slice_in_chain_idx = start_slice_original_idx

            while len(current_permutation_indices) < num_slices:
                best_next_slice_idx = -1
                min_connection_cost = float('inf')
                for k_idx in range(num_slices):
                    if k_idx not in used_slices_original_indices:
                        cost = dissimilarity_matrix[last_slice_in_chain_idx][k_idx]
                        if cost < min_connection_cost:
                            min_connection_cost = cost
                            best_next_slice_idx = k_idx
                
                if best_next_slice_idx != -1:
                    current_permutation_indices.append(best_next_slice_idx)
                    used_slices_original_indices.add(best_next_slice_idx)
                    if min_connection_cost != float('inf'):
                         current_total_cost += min_connection_cost
                    last_slice_in_chain_idx = best_next_slice_idx
                else:
                    break 
            
            if len(current_permutation_indices) == num_slices:
                if current_total_cost < min_overall_greedy_cost:
                    min_overall_greedy_cost = current_total_cost
                    initial_permutation = current_permutation_indices
        
        if not initial_permutation: # Fallback if greedy fails
            print("Warning: Greedy algorithm could not form a complete permutation. Using original order for 2-Opt.")
            initial_permutation = list(range(num_slices))
        
        # --- Apply 2-Opt Refinement ---
        final_permutation = self._apply_2_opt(initial_permutation, dissimilarity_matrix, num_slices)
        
        return final_permutation
