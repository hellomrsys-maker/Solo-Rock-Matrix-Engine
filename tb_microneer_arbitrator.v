`timescale 1ns/1ps

module tb_microneer_arbitrator;

    // Inputs
    reg         clk_photonic_pulse;
    reg         rst_near_threshold;
    reg  [63:0] node1_software_in;
    reg  [63:0] node2_executive_in;
    reg  [63:0] node3_balancer_in;
    reg  [63:0] node4_hardware_in;
    reg  [15:0] stin_pain_interrupt;
    reg  [15:0] ttss_temp_floor;

    // Outputs
    wire [63:0] node1_software_out;
    wire [63:0] node2_executive_out;
    wire [63:0] node3_balancer_out;
    wire [63:0] node4_hardware_out;
    wire        pdec_vrm_preramp;

    // Instantiate the Unit Under Test (UUT)
    microneer_arbitrator_matrix uut (
        .clk_photonic_pulse(clk_photonic_pulse),
        .rst_near_threshold(rst_near_threshold),
        .node1_software_in(node1_software_in),
        .node1_software_out(node1_software_out),
        .node2_executive_in(node2_executive_in),
        .node2_executive_out(node2_executive_out),
        .node3_balancer_in(node3_balancer_in),
        .node3_balancer_out(node3_balancer_out),
        .node4_hardware_in(node4_hardware_in),
        .node4_hardware_out(node4_hardware_out),
        .stin_pain_interrupt(stin_pain_interrupt),
        .ttss_temp_floor(ttss_temp_floor),
        .pdec_vrm_preramp(pdec_vrm_preramp)
    );

    // Clock generation: 500MHz (2ns period)
    always #1 clk_photonic_pulse = ~clk_photonic_pulse;

    initial begin
        // Initialize Inputs
        clk_photonic_pulse = 0;
        rst_near_threshold = 1;
        node1_software_in = 64'h0;
        node2_executive_in = 64'h0;
        node3_balancer_in = 64'h0;
        node4_hardware_in = 64'h0;
        stin_pain_interrupt = 16'h0000;
        ttss_temp_floor = 16'h0300; // Normal temperature baseline

        // Wait 10 ns for global reset to propagate
        #10;
        rst_near_threshold = 0;
        
        // ---------------------------------------------------------
        // TEST CASE 1: Standard Application Streaming (STATE_SOFT_DRIVEN)
        // ---------------------------------------------------------
        #5;
        node1_software_in = 64'hA5A5A5A5_A5A5A5A5;
        node3_balancer_in = 64'h5A5A5A5A_5A5A5A5A;
        node4_hardware_in = 64'h11112222_33334444;
        
        #2; // Wait for positive edge
        $display("TC1 - STATE_SOFT_DRIVEN: node2_executive_out = %h (Expected: %h)", 
                 node2_executive_out, node1_software_in);
        $display("TC1 - STATE_SOFT_DRIVEN: node4_hardware_out  = %h (Expected: %h)", 
                 node4_hardware_out, node3_balancer_in);
        $display("TC1 - STATE_SOFT_DRIVEN: node1_software_out  = %h (Expected: %h)", 
                 node1_software_out, node4_hardware_in);

        // ---------------------------------------------------------
        // TEST CASE 2: Pain Matrix Interrupt Trigger (VRM Pre-ramp verification)
        // ---------------------------------------------------------
        #5;
        stin_pain_interrupt = 16'hFFFF; // Touch vector registered
        #1;
        $display("TC2 - PAIN INTERRUPT: pdec_vrm_preramp = %b (Expected: 1)", pdec_vrm_preramp);
        stin_pain_interrupt = 16'h0000;
        #1;
        $display("TC2 - PAIN CLEAR: pdec_vrm_preramp = %b (Expected: 0)", pdec_vrm_preramp);

        // ---------------------------------------------------------
        // TEST CASE 3: Infant Non-Shivering Thermogenesis Model (Low Temp Pre-Heat)
        // ---------------------------------------------------------
        #5;
        ttss_temp_floor = 16'h0100; // Temperature below floor threshold (0x0200)
        #1;
        $display("TC3 - TEMP UNDER FLOOR: pdec_vrm_preramp = %b (Expected: 1)", pdec_vrm_preramp);
        ttss_temp_floor = 16'h0300; // Normal temperature baseline restored
        #1;
        $display("TC3 - TEMP NORMALIZED: pdec_vrm_preramp = %b (Expected: 0)", pdec_vrm_preramp);

        // ---------------------------------------------------------
        // TEST CASE 4: Executive-Driven Transition (STATE_EXEC_DRIVEN)
        // ---------------------------------------------------------
        #5;
        node2_executive_in = 64'h00000000_00000001; // Hand control to CEO AI (node2_executive_in[0] = 1)
        #2; // Clock tick to register state shift
        node2_executive_in = 64'hBCDEBCDE_BCDEBCDE;
        #2; // Clock tick to propagate inputs in the new state
        $display("TC4 - STATE_EXEC_DRIVEN: node3_balancer_out = %h (Expected: %h)", 
                 node3_balancer_out, node2_executive_in);

        // ---------------------------------------------------------
        // TEST CASE 5: Hardware Safety Override (STATE_HARD_DRIVEN)
        // ---------------------------------------------------------
        #5;
        node4_hardware_in = 64'h80000000_00000000; // Force Silicon Safety Override (node4_hardware_in[63] = 1)
        #2;
        $display("TC5 - STATE_HARD_DRIVEN: node1_software_out = %h (Expected: %h)", 
                 node1_software_out, node4_hardware_in);
        
        #10;
        $finish;
    end

endmodule
