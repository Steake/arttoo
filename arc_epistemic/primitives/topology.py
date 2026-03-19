from __future__ import annotations

from collections import deque

import numpy as np


def connected_components(mask: np.ndarray, connectivity: int = 4) -> list[np.ndarray]:
    arr = np.asarray(mask, dtype=bool)
    visited = np.zeros_like(arr, dtype=bool)
    components: list[np.ndarray] = []
    if connectivity == 8:
        neighbors = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
    else:
        neighbors = [(-1, 0), (0, -1), (0, 1), (1, 0)]
    for row in range(arr.shape[0]):
        for col in range(arr.shape[1]):
            if not arr[row, col] or visited[row, col]:
                continue
            queue = deque([(row, col)])
            visited[row, col] = True
            component = np.zeros_like(arr, dtype=bool)
            while queue:
                current_row, current_col = queue.popleft()
                component[current_row, current_col] = True
                for d_row, d_col in neighbors:
                    next_row = current_row + d_row
                    next_col = current_col + d_col
                    if 0 <= next_row < arr.shape[0] and 0 <= next_col < arr.shape[1]:
                        if arr[next_row, next_col] and not visited[next_row, next_col]:
                            visited[next_row, next_col] = True
                            queue.append((next_row, next_col))
            components.append(component)
    return components
