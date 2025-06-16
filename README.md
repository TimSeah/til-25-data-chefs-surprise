# TIL-25 Data Chefs - Surprise Challenge

**Hackathon:** TIL-25 Hackathon
**Team:** Data Chefs
**Author:** lolkabash

## 📖 Description

This repository contains a solution to the TIL-25 Hackathon "surprise challenge": reconstructing a vertically shredded document from its image slices. Given a list of JPEG-encoded vertical slices, the system must predict the correct permutation to reassemble the original document. This project outlines our approach and implementation to tackle it.

![document reconstruc](https://github.com/user-attachments/assets/1a2f5e8f-ffbe-4363-8ab4-3f32c60095aa)

## 💻 Technologies Used

*   **Python:** Core programming language for scripting and logic.
*   **Shell Scripts:** For automation, setup, or execution tasks.
*   **Dockerfile:** Used for containerizing the application/solution, ensuring portability and consistent environments.
*   **Pillow:** Python Imaging Library (PIL) fork, used for image processing and pixel extraction.
*   **Uvicorn:** ASGI server for running FastAPI applications in a performant way.
*   **Base64 (Python standard library):** For encoding/decoding image data as required by the challenge.

## ⚙️ Working Process & Solution

This section outlines the approach taken to understand and solve the surprise challenge.

### 1. Understanding the Challenge
*   **Problem Deconstruction:**  
    The challenge was separated into major tasks: (a) reading and decoding image slices, (b) extracting distinguishing features from each slice, (c) designing a method to measure similarity between slices, and (d) efficiently determining their original left-to-right order.
*   **Initial Brainstorming & Ideas:**  
    Several ideas were considered, including using feature matching, template matching, or deep learning. However, since the shreds are vertical and the edges are directly adjacent in the original, a pixel-based edge approach was deemed more direct and robust.
*   **Constraints & Requirements:**  
    - All slices are vertical and of uniform height.  
    - Input slices are provided as base64-encoded JPEG images.
    - The solution must return a permutation of the input indices in the correct order.
    - The solution must be efficient and robust, suitable for an API server.

### 2. Approach & Strategy
*   **Chosen Solution Path:**  
    A greedy edge-matching algorithm was selected: compare the right edge of one slice to the left edge of another to build a dissimilarity matrix, then reconstruct the permutation by chaining the best-matching edges.
*   **Rationale:**  
    This approach is computationally efficient (quadratic in the number of slices) and leverages the problem structure—adjacent shreds must have visually similar boundaries.
*   **Key Components:**  
    - Edge extraction using Pillow.
    - Dissimilarity (sum of absolute differences) computation for all pairs.
    - Greedy chaining strategy to build the permutation.
    - REST API server using FastAPI to handle requests.

### 3. Implementation Details
*   **Core Logic:**  
      - Each slice is decoded and the leftmost/rightmost columns are extracted as RGB tuples.
      - For every pair of slices, the sum of absolute differences between their adjacent edges is computed.
      - The permutation is constructed by starting with the best-matching pair and iteratively adding the next best-matching unused slice to either end.
*   **Dockerization:**  
      - The Dockerfile sets up a Python environment with all dependencies (FastAPI, Pillow, Uvicorn, etc).
      - It uses an official Python base image and specifies commands to install requirements and launch the API server.
*   **Data Handling:**  
      - All image data is processed in-memory. Slices are received as base64-encoded JPEGs, decoded on-the-fly, and never written to disk.
      - No persistent storage is required; all computation is stateless and request-driven.
*   **Workflow:**  
      1. API receives a batch of shredded document instances.
      2. For each instance, image slices are decoded and edge features extracted.
      3. Dissimilarity matrix is computed for all slice pairs.
      4. The best permutation is constructed using the greedy chaining strategy.
      5. The API responds with the predicted permutations for all instances.

### 4. Outcome & Results
*   **Solution Output:**  
      The solution returns, for each document instance, an ordered list of indices representing the predicted left-to-right reassembly of the slices.
*   **Effectiveness/Performance:**  
      - The greedy algorithm is both fast and robust for typical challenge sizes.
      - Empirically, the method reconstructs most documents correctly, especially when the edge information is distinctive.
      - The quadratic time complexity ensures rapid inference even for larger numbers of slices.
*   **Challenges Faced:**  
      - Handling images with inconsistent formats or corruption required careful error-checking.
      - Ensuring efficiency for batch requests led to vectorized operations and in-memory processing.
      - Fine-tuning the edge comparison metric for robustness (e.g., handling noisy/compressed images).

## 🚀 Setup and Usage

### Prerequisites

*   **Python 3.8+** (tested on Python 3.12)
*   **Docker** (for containerized deployment, optional)
*   **Git** (for cloning and version control)
*   **pip** (Python package manager)
*   **Pillow** (Python Imaging Library fork, for image processing)
*   **FastAPI** (for the web server API)
*   **Uvicorn** (ASGI server for FastAPI)
*   **NumPy** (for optimized image processing in some algorithm variants)
*   (Other dependencies listed in `requirements.txt`)

### Installation & Setup
1.  Clone the repository:
    ```bash
    git clone https://github.com/lolkabash/til-25-data-chefs-surprise.git
    cd til-25-data-chefs-surprise
    ```
2.  **(Python dependencies - if not fully handled by Docker)**
    ```bash
    pip install -r requirements.txt
    ```
3.  **(Docker Setup - if applicable)**
    Build the Docker image:
    ```bash
    docker build -t surprise-challenge-solution .
    ```

### Running the Solution
*   **(If Dockerized):**
    ```bash
    docker run surprise-challenge-solution [any_arguments_needed]
    ```
*   **(If running with Python scripts directly):**
    ```bash
    python main_script.py [any_arguments_needed]
    ```
*   **(If using Shell scripts):**
    ```bash
    ./run_solution.sh
    ```

## 📁 File Structure (Optional - Example)

```
til-25-data-chefs-surprise/
├── src/                        
│   ├── surprise_server.py           # FastAPI server for challenge API
│   ├── surprise_manager.py          # Core algorithm (v1, SAD/greedy)
│   ├── surprise_manager_opti.py     # Optimized algorithm using NumPy
│   ├── surprise_manager_new.py      # Variant with normalized cross-correlation
│   ├── surprise_manager_working.py  # Alternative/working version
│   ├── surprise_manager-template.py # Template/stub for starting new approaches
│   └── ...                         # (Other Python source files may exist)
├── scripts/                    # Shell scripts for automation/setup (if present)
├── data/                       # Input/output data for the challenge (if applicable)
├── Dockerfile                  # Docker configuration
├── .dockerignore               # Files to ignore during Docker build
├── requirements.txt            # Python dependencies
├── .gitignore
└── README.md
```

# TIL-AI 2025 Surprise Challenge

**Contents**
- [TIL-AI 2025 Surprise Challenge](#til-ai-2025-surprise-challenge)
  - [Overview](#overview)
  - [Submission procedure](#submission-procedure)
  - [Challenge specifications](#challenge-specifications)
    - [Input format](#input-format)
    - [Output format](#output-format)
    - [Scoring](#scoring)
      - [In short](#in-short)
      - [In detail](#in-detail)


## Overview

Your task is to develop a system for reassembly of shredded documents. Given slices of a document cut along the vertical axis, your system is to output the permutation of input slices that correctly reassembles the document.

All strips will be of the same width and height. You are guaranteed that all strips are the right way up.


## Submission procedure

You've done the other challenges, so you should know the drill:

```bash
# Build your container
docker build -t TEAM_ID-surprise:TAG .

# Run your container
docker run -p 5005:5005 --gpus all -d TEAM_ID-surprise:TAG

# Test your container
pip install -r requirements-dev.txt
python3 test.py

# Submit
./submit-surprise.sh TEAM_ID-surprise:TAG
```


## Challenge specifications

### Input format

The input is sent via a POST request to the `/surprise` route on port 5005. It is a JSON document structured as such:

```json
{
  "instances": [
    {
      "key": 0,
      "slices": ["base64_encoded_slice", ...]
    },
    ...
  ]
}
```

Each object in the `instances` list corresponds to a single shredded document. Each string in the `slices` list contains the base64-encoded bytes of a single slice of that document represented as a JPEG image.

The length of the `instances` list is variable.


### Output format

Your route handler function must return a `dict` with this structure:

```json
{
    "predictions": [
        [p11, p12, ..., p1s],
        [p21, p22, ..., p2s],
        ...
    ]
}
```

where:

- $s$ is the number of slices in each document, and 
- $[p_{i1}, p_{i2}, \dots, p_{is}]$ is the predicted permutation of input slices that correctly reassembles the $i$-th document, leftmost slice first.

For instance, if you're given a single document in three slices, and you think that:

- the first slice should go in the middle
- the second slice should go on the left
- the third slice should go on the right

then you would return:

```json
{
    "predictions": [
        [1, 0, 2]
    ]
}
```

The $k$-th element of `predictions` must be the prediction corresponding to the $k$-th element of `instances` for all $1 \le k \le n$, where $n$ is the number of input instances. The length of `predictions` must equal that of `instances`.


### Scoring

#### In short

- Predictions that contain long runs of correctly assembled slices will score better.
- Predictions that contain several short runs will score worse. 
- If your prediction is not a permutation of $[0, 1, \dots, s-1]$, your score will be zero.

#### In detail

First we check that your prediction is a permutation of $[0, 1, \dots, s-1]$. If it is, we convert it into a list of run-lengths of correctly assembled sub-segments. For instance, if the ground-truth is $[1, 3, 0, 2]$ but you predicted $[3, 0, 1, 2]$, then your list of run-lengths is $[2, 1, 1]$.

Let $\\{r_i\\}_{i=1}^k$ be the list of run-lengths, and let $p_i = r_i/s$ for $1 \le i \le k$. Interpreting $\{p_i\}$ as a probability distribution, we calculate its base-*s* entropy by:

$$
H = -\sum_{i=1}^n{p_i \log_s p_i}
$$

Your score is then given by $1 - H$.

The highest-scoring run-length list is $[s]$, which scores 1. This corresponds to a perfectly reassembled document.

The lowest-scoring run-length list is $[1, 1, \dots, 1]$ ($s$ 1's), which scores 0. This corresponds to an attempt where no pair of strips was correctly reassembled.

