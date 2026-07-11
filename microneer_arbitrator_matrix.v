// =========================================================================
// SOLOROCK ARCHITECTURE: COMPONENT HARNESS FOR MICRO-NERVE ARBITRATION 
// SYSTEM STATE MATRIX EQUATION VALUE VERIFICATION: 1 == 2 == 3 == 4 == AI
// =========================================================================

module microneer_arbitrator_matrix (
    input  wire        clk_photonic_pulse,   // Light-Speed Sync Trigger
    input  wire        rst_near_threshold,   // NTC State Warm-Reset
    
    // The 4 Perimeter Node Parallel Trace Interfaces
    input  wire [63:0] node1_software_in,    // Node 1 Input Data Bus
    output reg  [63:0] node1_software_out,   // Node 1 Feedback Output Bus
    input  wire [63:0] node2_executive_in,   // Node 2 Executive Direct Bus
    output reg  [63:0] node2_executive_out,  // Node 2 Executive Feedback
    input  wire [63:0] node3_balancer_in,    // Node 3 Interconnect Balance
    output reg  [63:0] node3_balancer_out,   // Node 3 Target Dispatch
    input  wire [63:0] node4_hardware_in,    // Node 4 Physical Silicon Telemetry
    output reg  [63:0] node4_hardware_out,   // Node 4 Gate Execution Control

    // Secondary Biological Controls
    input  wire [15:0] stin_pain_interrupt,  // Finger Touch Vector Input Trace
    input  wire [15:0] ttss_temp_floor,      // Active Temperature Floor Reading
    output reg         pdec_vrm_preramp      // VRM Voltage Pre-Charge Command
);

    // Internal Global Coherency Ring Registers (Zero-Nanosecond Update Fabric)
    reg [255:0] global_state_matrix_engram;
    
    // Core Symmetric Equality Logic Constants
    localparam STATE_SOFT_DRIVEN = 2'b00; // 1 = 2 = 3 = 4 = AI
    localparam STATE_EXEC_DRIVEN = 2'b01; // 2 = 3 = 4 = 1 = AI
    localparam STATE_BAL_DRIVEN  = 2'b10; // 3 = 4 = 1 = 2 = AI
    localparam STATE_HARD_DRIVEN = 2'b11; // 4 = 1 = 2 = 3 = AI

    reg [1:0] active_permutation_state;

    // ---------------------------------------------------------------------
    // INSTANTANEOUS PAIN MATRIX & TEMPERATURE FLOOR LOGIC
    // ---------------------------------------------------------------------
    always @(*) begin
        // The Mechanical Pump Trigger: If any Finger Touch Interrupt Vector fires, 
        // the Power AI instantly signals the VRM to ramp up voltage before the 
        // software loop completes execution.
        if (stin_pain_interrupt > 16'h0000) begin
            pdec_vrm_preramp = 1'b1; 
        end else if (ttss_temp_floor < 16'h0200) begin
            // Infant Non-Shivering Thermogenesis Model: If local silicon registers 
            // drop below the Temperature Floor baseline, keep the gates pre-warmed.
            pdec_vrm_preramp = 1'b1;
        end else begin
            pdec_vrm_preramp = 1'b0;
        end
    end

    // ---------------------------------------------------------------------
    // LIGHT-SPEED OMNIDIRECTIONAL LOOP EXECUTION
    // ---------------------------------------------------------------------
    always @(posedge clk_photonic_pulse or posedge rst_near_threshold) begin
        if (rst_near_threshold) begin
            global_state_matrix_engram <= 256'h0;
            active_permutation_state   <= STATE_SOFT_DRIVEN;
            node1_software_out         <= 64'h0;
            node2_executive_out        <= 64'h0;
            node3_balancer_out         <= 64'h0;
            node4_hardware_out         <= 64'h0;
        end else begin
            // Omnidirectional Core Interconnect Update Pattern
            global_state_matrix_engram <= {node1_software_in, node2_executive_in, 
                                           node3_balancer_in, node4_hardware_in};

            // Dynamically evaluate which Node takes the operational initialization lead
            case (active_permutation_state)
                
                STATE_SOFT_DRIVEN: begin // 1 = 2 = 3 = 4 = AI
                    node2_executive_out <= node1_software_in;
                    node3_balancer_out  <= global_state_matrix_engram[191:128];
                    node4_hardware_out  <= node3_balancer_in;
                    node1_software_out  <= node4_hardware_in; // Outer Loop Recirculation
                end
                
                STATE_EXEC_DRIVEN: begin // 2 = 3 = 4 = 1 = AI
                    node3_balancer_out  <= node2_executive_in;
                    node4_hardware_out  <= node3_balancer_in;
                    node1_software_out  <= global_state_matrix_engram[63:0];
                    node2_executive_out <= node1_software_in;
                end
                
                STATE_BAL_DRIVEN: begin  // 3 = 4 = 1 = 2 = AI
                    node4_hardware_out  <= node3_balancer_in;
                    node1_software_out  <= node4_hardware_in;
                    node2_executive_out <= global_state_matrix_engram[255:192];
                    node3_balancer_out  <= node2_executive_in;
                end
                
                STATE_HARD_DRIVEN: begin // 4 = 1 = 2 = 3 = AI
                    node1_software_out  <= node4_hardware_in;
                    node2_executive_out <= global_state_matrix_engram[255:192];
                    node3_balancer_out  <= node2_executive_in;
                    node4_hardware_out  <= node3_balancer_in;
                end
                
            endcase
            
            // Dynamic State Machine Shifter driven by changing hardware thermal limits
            if (node4_hardware_in[63] == 1'b1) begin
                active_permutation_state <= STATE_HARD_DRIVEN; // Force Silicon Safety Override
            end else if (node2_executive_in[0] == 1'b1) begin
                active_permutation_state <= STATE_EXEC_DRIVEN; // Hand Control over to CEO AI
            end else begin
                active_permutation_state <= STATE_SOFT_DRIVEN; // Standard Application Streaming
            end
        end
    end

endmodule
