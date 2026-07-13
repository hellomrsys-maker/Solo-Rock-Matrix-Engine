"""
Autonomic telemetry source: CPU temperature, load, and (where available)
power draw. Tries the richest available provider first and falls back
through progressively simpler ones — the engine stays useful even when
it's partially blind, and never crashes for lack of a sensor.

Provider chain:
    Windows : LibreHardwareMonitor (WMI) -> ACPI thermal zone (WMI) -> psutil -> 0.0
    Linux   : psutil.sensors_temperatures() (hwmon/coretemp) -> 0.0
    Other   : psutil best-effort -> 0.0
"""

import platform
import subprocess
import psutil

_IS_WINDOWS = platform.system() == "Windows"


def _run_powershell(cmd, timeout=3):
    try:
        result = subprocess.run(["powershell", "-Command", cmd],
                                 capture_output=True, text=True, timeout=timeout)
        return result.stdout if result.returncode == 0 else ""
    except Exception:
        return ""


class HardwareReader:
    def __init__(self):
        self.lhm_available = False
        if _IS_WINDOWS:
            self._check_lhm()

    def _check_lhm(self):
        """Check if LibreHardwareMonitor WMI namespace is available (Windows only)."""
        cmd = 'Get-WmiObject -Namespace "root/LibreHardwareMonitor" -Class Sensor -ErrorAction SilentlyContinue | Select-Object -First 1'
        out = _run_powershell(cmd)
        if out.strip():
            self.lhm_available = True
            print("[HardwareReader] LibreHardwareMonitor detected. Deep sensors active.")
        else:
            print("[HardwareReader] LHM not found. Falling back to ACPI/WMI sensors.")

    def get_cpu_temperature(self):
        """Best-effort CPU temperature in Celsius, 0.0 if genuinely unreadable."""
        if _IS_WINDOWS:
            temp = self._get_cpu_temperature_windows()
            if temp is not None:
                return temp
        else:
            temp = self._get_cpu_temperature_psutil()
            if temp is not None:
                return temp
        return 0.0

    def _get_cpu_temperature_windows(self):
        if self.lhm_available:
            cmd = ('Get-WmiObject -Namespace "root/LibreHardwareMonitor" -Class Sensor | '
                   'Where-Object {$_.SensorType -eq "Temperature" -and $_.Name -like "*CPU*"} | '
                   'Select-Object -First 1 Value')
            out = _run_powershell(cmd)
            try:
                lines = [l.strip() for l in out.split('\n') if l.strip()]
                if len(lines) > 2:  # Skip headers
                    return float(lines[-1])
            except (ValueError, IndexError):
                pass

        # ACPI fallback
        cmd = ('Get-WmiObject MSAcpi_ThermalZoneTemperature -Namespace "root/wmi" '
               '-ErrorAction SilentlyContinue | Select-Object CurrentTemperature')
        out = _run_powershell(cmd)
        try:
            lines = [l.strip() for l in out.split('\n') if l.strip()]
            if len(lines) > 2:
                kelvin = float(lines[-1]) / 10.0  # ACPI reports deci-Kelvin
                return kelvin - 273.15
        except (ValueError, IndexError):
            pass

        return self._get_cpu_temperature_psutil()

    def _get_cpu_temperature_psutil(self):
        """Cross-platform fallback via psutil.sensors_temperatures() (Linux hwmon/coretemp)."""
        try:
            sensors = psutil.sensors_temperatures()
        except (AttributeError, NotImplementedError, FileNotFoundError, OSError, PermissionError):
            # Sensors not available on this platform or container environment
            return None
        if not sensors:
            return None

        for key in ("coretemp", "k10temp", "cpu_thermal", "zenpower"):
            if key in sensors and sensors[key]:
                return sensors[key][0].current

        # Anything at all beats nothing.
        for entries in sensors.values():
            if entries:
                return entries[0].current
        return None

    def get_cpu_load(self):
        """CPU utilization percentage, cross-platform."""
        return psutil.cpu_percent(interval=0.1)

    def get_ram_usage(self):
        """RAM utilization percentage, cross-platform."""
        return psutil.virtual_memory().percent

    def get_battery_percent(self):
        """Battery charge percentage, or None if no battery is present."""
        try:
            battery = psutil.sensors_battery()
        except (AttributeError, NotImplementedError, FileNotFoundError, OSError):
            # Battery not available on this platform or container environment
            return None
        return battery.percent if battery else None


if __name__ == "__main__":
    reader = HardwareReader()
    print(f"Current CPU Temp:  {reader.get_cpu_temperature():.1f} C")
    print(f"Current CPU Load:  {reader.get_cpu_load():.1f} %")
    print(f"Current RAM Usage: {reader.get_ram_usage():.1f} %")
    battery = reader.get_battery_percent()
    print(f"Battery:           {'N/A' if battery is None else f'{battery:.1f} %'}")
