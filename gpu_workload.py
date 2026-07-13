"""
GPU Workload Harness — simple compute kernel for benchmarking.

Detects available GPU (NVIDIA CUDA or AMD ROCm) and provides a repeatable,
measurable workload. If no GPU available, falls back to CPU numpy.

Usage:
    from gpu_workload import GPUWorkload
    wl = GPUWorkload(size=1024)
    for i in range(10):
        result = wl.compute()  # Actual GPU/CPU work
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from hardware_drivers.topology import HardwareTopology

# Try GPU libraries in order of preference
try:
    import cupy as cp
    HAS_CUPY = True
    GPU_TYPE = "NVIDIA (CuPy)"
except ImportError:
    HAS_CUPY = False
    GPU_TYPE = None

try:
    import numba.cuda
    HAS_NUMBA_CUDA = True
    if GPU_TYPE is None:
        GPU_TYPE = "NVIDIA (Numba)"
except ImportError:
    HAS_NUMBA_CUDA = False

import numpy as np


class GPUWorkload:
    """
    Wraps a simple matrix-multiply workload that runs on GPU if available,
    CPU otherwise. Always returns the same type of result so the benchmark
    doesn't have to care which backend ran.
    """

    def __init__(self, size=512):
        self.size = size
        self.topo = HardwareTopology()
        self.gpu_available = False
        self.backend = "CPU (NumPy)"

        # Detect what we can actually use
        if HAS_CUPY and self.topo.gpus:
            self.backend = "GPU (NVIDIA/CuPy)"
            self.gpu_available = True
            self.A_gpu = cp.random.randn(size, size).astype(cp.float32)
            self.B_gpu = cp.random.randn(size, size).astype(cp.float32)
        elif HAS_NUMBA_CUDA and self.topo.gpus:
            self.backend = "GPU (NVIDIA/Numba)"
            self.gpu_available = True
            self.A_cpu = np.random.randn(size, size).astype(np.float32)
            self.B_cpu = np.random.randn(size, size).astype(np.float32)
        else:
            # Fallback to CPU
            self.A_cpu = np.random.randn(size, size).astype(np.float32)
            self.B_cpu = np.random.randn(size, size).astype(np.float32)

    def compute(self):
        """Run one workload iteration. Returns a scalar result."""
        if HAS_CUPY and self.gpu_available:
            # GPU path: matrix multiply on device
            C = cp.matmul(self.A_gpu, self.B_gpu)
            result = float(cp.sum(C))
            return result
        else:
            # CPU path: numpy matrix multiply
            C = np.matmul(self.A_cpu, self.B_cpu)
            result = float(np.sum(C))
            return result

    def info(self):
        """Return a dict describing the workload."""
        return {
            "backend": self.backend,
            "matrix_size": self.size,
            "gpu_available": self.gpu_available,
            "topology": str(self.topo),
        }


if __name__ == "__main__":
    print("GPU Workload Harness Test\n")
    wl = GPUWorkload(size=512)
    print(f"Backend: {wl.backend}")
    print(f"GPU available: {wl.gpu_available}")
    print(f"Topology: {wl.topo}")
    print()

    print("Running 5 iterations...")
    for i in range(5):
        result = wl.compute()
        print(f"  Iteration {i+1}: result={result:.2e}")

    print("\nWorkload harness OK")
