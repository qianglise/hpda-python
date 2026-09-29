import numpy as np
import time

def timming_matrix_inversion(size: int = 4000) -> float:
    """Generates a symmetric matrix and measures the time taken to invert it."""
    # Create a random matrix
    A = np.random.random((size, size))

    # Make it symmetric (Note: A * A.T is element-wise multiplication.
    # If you meant matrix multiplication, use A @ A.T or np.dot(A, A.T))
    A = A * A.T

    # Measure inversion time
    time_start = time.time()
    np.linalg.inv(A)
    time_end = time.time()

    return time_end - time_start


def main() -> None:
    matrix_size = 4000
    duration = timming_matrix_inversion(matrix_size)

    print(f"Time spent for inverting a random matrix with a size of ({matrix_size}x{matrix_size}) is {round(duration, 2)} s")


if __name__ == "__main__":
    main()
