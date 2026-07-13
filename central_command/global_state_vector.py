"""
The Brain's working memory: a consolidated, always-current view of
telemetry and hardware topology. This is the single object the
Decision Engine reads before making a routing call — it owns the
sync between live sensors and the shared AMSV block so every other
subsystem sees the same numbers.
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from infrastructure.amsv import amsv_block
from hardware_drivers.hardware_reader import HardwareReader
from hardware_drivers.topology import HardwareTopology


class GlobalStateVector:
    def __init__(self):
        self.hw_reader = HardwareReader()
        self.topology = HardwareTopology()
        self._last_snapshot = {}

    def sync_from_hardware(self):
        """Pull live telemetry and publish it into the shared AMSV block."""
        cpu_temp = self.hw_reader.get_cpu_temperature()
        ram_usage = self.hw_reader.get_ram_usage()
        cpu_load = self.hw_reader.get_cpu_load()

        amsv_block.cpu_temp = cpu_temp
        amsv_block.ram_usage = ram_usage
        # No dedicated GPU telemetry provider yet (see roadmap: ROCm SMI);
        # gpu_load stays whatever the workload/demo layer last wrote.

        self._last_snapshot = {
            "cpu_temp": cpu_temp,
            "cpu_load": cpu_load,
            "ram_usage": ram_usage,
            "gpu_load": amsv_block.gpu_load,
            "wattage": amsv_block.wattage,
            "battery_percent": self.hw_reader.get_battery_percent(),
        }
        return self._last_snapshot

    def snapshot(self):
        """Return the most recent telemetry snapshot, syncing if none exists yet."""
        if not self._last_snapshot:
            return self.sync_from_hardware()
        return dict(self._last_snapshot)

    def hardware_profile(self):
        """CPU-only / CPU+GPU / CPU+GPU+TPU routing profile for this machine."""
        return self.topology.profile


if __name__ == "__main__":
    gsv = GlobalStateVector()
    print(f"[GlobalStateVector] Hardware profile: {gsv.hardware_profile()}")
    print(f"[GlobalStateVector] Telemetry: {gsv.sync_from_hardware()}")
