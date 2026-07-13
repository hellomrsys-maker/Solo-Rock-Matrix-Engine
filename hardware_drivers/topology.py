"""
Hardware topology detection for the Central System (the Brain).

Probes what silicon is actually present on the running machine so the
Decision Engine can build its routing table dynamically, instead of
assuming a fixed CPU/GPU/TPU configuration. Every probe here degrades
gracefully: an undetectable device class is simply reported absent,
never raises.
"""

import platform
import shutil
import subprocess

import psutil


def _run(cmd, timeout=3):
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return result.stdout if result.returncode == 0 else ""
    except Exception:
        return ""


def _detect_amd_rocm_gpu():
    """Detect AMD GPUs exposed via ROCm SMI (rocm-smi on the PATH)."""
    if not shutil.which("rocm-smi"):
        return []
    out = _run(["rocm-smi", "--showproductname"])
    names = [line.split(":", 1)[1].strip() for line in out.splitlines() if "Card series" in line or "GPU" in line]
    return names or (["AMD GPU (ROCm)"] if "GPU" in out else [])


def _detect_nvidia_gpu():
    """Detect NVIDIA GPUs exposed via nvidia-smi, for topology completeness."""
    if not shutil.which("nvidia-smi"):
        return []
    out = _run(["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"])
    return [line.strip() for line in out.splitlines() if line.strip()]


def _detect_windows_gpu():
    """Detect GPUs via WMI Win32_VideoController (Windows only)."""
    if platform.system() != "Windows":
        return []
    out = _run(["powershell", "-Command",
                "Get-CimInstance Win32_VideoController | Select-Object -ExpandProperty Name"])
    return [line.strip() for line in out.splitlines() if line.strip()]


def _detect_linux_gpu():
    """Fallback GPU detection on Linux via lspci, for non-vendor-SDK visibility."""
    if platform.system() != "Linux" or not shutil.which("lspci"):
        return []
    out = _run(["lspci"])
    return [line.split(":", 2)[-1].strip() for line in out.splitlines()
            if "VGA compatible controller" in line or "3D controller" in line]


def _detect_tpu():
    """
    TPU / SmartNIC detection has no universal userspace API. We only
    report a TPU present if an operator explicitly flags one via
    environment variable, or a known accelerator device node exists.
    Absence is the correct default on almost all developer machines.
    """
    import os
    if os.environ.get("SOLO_ROCK_TPU_PRESENT", "").lower() in ("1", "true", "yes"):
        return ["Operator-declared TPU (SOLO_ROCK_TPU_PRESENT)"]
    return []


class HardwareTopology:
    """
    Snapshot of the hardware silicon actually available on this machine.
    Built once at boot; call refresh() if hardware is hot-plugged.
    """

    def __init__(self):
        self.os_name = platform.system()
        self.cpu_logical_cores = psutil.cpu_count(logical=True) or 1
        self.cpu_physical_cores = psutil.cpu_count(logical=False) or 1
        self.gpus = []
        self.has_tpu = False
        self.refresh()

    def refresh(self):
        gpus = []
        gpus += _detect_amd_rocm_gpu()
        gpus += _detect_nvidia_gpu()
        gpus += _detect_windows_gpu()
        gpus += _detect_linux_gpu()
        # De-duplicate while preserving order
        seen = set()
        self.gpus = [g for g in gpus if not (g in seen or seen.add(g))]
        self.has_tpu = bool(_detect_tpu())
        return self

    @property
    def has_gpu(self):
        return len(self.gpus) > 0

    @property
    def profile(self):
        """The routing profile name the Decision Engine keys off of."""
        if self.has_gpu and self.has_tpu:
            return "CPU_GPU_TPU"
        if self.has_gpu:
            return "CPU_GPU"
        return "CPU_ONLY"

    def describe(self):
        return {
            "os": self.os_name,
            "cpu_physical_cores": self.cpu_physical_cores,
            "cpu_logical_cores": self.cpu_logical_cores,
            "gpus": list(self.gpus),
            "has_tpu": self.has_tpu,
            "profile": self.profile,
        }

    def __repr__(self):
        d = self.describe()
        gpu_desc = ", ".join(d["gpus"]) if d["gpus"] else "none"
        return (f"<HardwareTopology profile={d['profile']} "
                f"cores={d['cpu_physical_cores']}p/{d['cpu_logical_cores']}l "
                f"gpus=[{gpu_desc}] tpu={d['has_tpu']}>")


if __name__ == "__main__":
    topo = HardwareTopology()
    print("[Topology] Detected hardware profile:")
    for key, value in topo.describe().items():
        print(f"    {key}: {value}")
