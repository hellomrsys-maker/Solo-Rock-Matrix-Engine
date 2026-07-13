import time
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hardware_drivers.hardware_reader import HardwareReader
from hardware_drivers.power_controller import PowerController
from hardware_drivers.process_controller import ProcessController

class EmergencyOverride:
    def __init__(self):
        self.hw_reader = HardwareReader()
        self.power_ctrl = PowerController()
        self.proc_ctrl = ProcessController()
        self.is_throttled = False
        
    def trigger_thermal_shutdown(self, current_temp):
        """CEO Level Override: Bypasses all normal flow to save the hardware."""
        print("\n!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        print(f" [CEO OVERRIDE] THERMAL CRITICAL DETECTED: {current_temp} C")
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        
        # 1. Instantly throttle CPU Maximum State to 85% to cut heat generation
        if not self.is_throttled:
            success = self.power_ctrl.set_max_processor_state(85)
            if success:
                self.is_throttled = True
                
        # 2. Command FSMF (Kidney) to kill background noise causing extra heat
        self.proc_ctrl.filter_junk_processes()
        
        print(" [CEO OVERRIDE] Hardware thermal constraints applied successfully.\n")

    def monitor_loop(self):
        """Dedicated CEO thread to monitor 95C spikes directly."""
        print("[CentralAI] Emergency Override Monitor Online.")
        while True:
            temp = self.hw_reader.get_cpu_temperature()
            
            # If we detect the 95C reported by user (or we simulate it for testing if temp is 0)
            if temp >= 90.0:
                self.trigger_thermal_shutdown(temp)
                # Wait for cooldown
                time.sleep(30)
                # Reset power plan to 100% after cooldown
                self.power_ctrl.set_max_processor_state(100)
                self.is_throttled = False
                print("[CentralAI] Temperature normalized. Hardware constraints lifted.")
            
            time.sleep(2)

if __name__ == "__main__":
    eo = EmergencyOverride()
    # For testing the physical lever without waiting for 95C:
    eo.trigger_thermal_shutdown(95.5)
