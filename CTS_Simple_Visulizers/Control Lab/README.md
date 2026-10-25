# CubeSat Control Lab

Download and run from Git Bash:

```bash
git clone https://github.com/JonathE0/CTS_SAT_2_ADCS.git
cd "CTS_SAT_2_ADCS/CTS_Simple_Visulizers/Control Lab"
python cubesat_control_lab.py
```

If you already cloned the repository, update that checkout with `git pull` instead.

Open http://127.0.0.1:8004 if the browser does not open automatically. Use `--port 8080` for another port or `--no-browser` to suppress automatic browser launch. Python 3.10+ is required; no extra packages or MATLAB installation are needed.

## First experiment

1. Stay on **01 / Torque becomes motion**.
2. Drag the highlighted library block to the outlined canvas position. Clicking the library button is an alternative that places it automatically. Only primitive blocks are inserted; no wires are added.
3. Read each block’s explanation in the lesson and inspector. Double-click the block (or focus it and press Enter) to edit its name and parameter directly. Integrators expose their initial condition; blocks without numeric parameters show their explanation. Cancel or Escape closes the editor without saving.
4. After all blocks are placed, follow the connection instructions. Click an output circle, then the numbered destination input. Wires route around blocks using horizontal and vertical segments, favoring shorter paths and fewer bends. When moving a block, connected ports within 10 screen pixels snap into alignment; hold Alt to bypass snapping. Aligned forward connections become one straight segment when their path is clear. A green outline indicates snapping. Dashed wires indicate that blocks obstruct a port and must be separated. One output can feed multiple inputs; each input takes one wire. Click a wire to remove it.
5. Choose **Fit diagram**, **Check wiring**, then **Run**. The first lesson’s torque should give angular rate 0.06 rad/s and angle 0.03 rad after one simulated second.
6. Choose a signal in the scope. Each signal starts with fixed, unit-appropriate Y limits and a 0–60 second time axis. Edit the four axis fields and click **Apply fixed axes**, or double-click a Scope block to edit its limits. The plot never autoscales; out-of-range traces are clipped. Axis changes retain simulation state and history. Up to 600 simulated seconds of history are retained. Pause, reset states, or modify a parameter to repeat the experiment. Parameter changes reset the integrators.

The later lessons introduce proportional feedback, rate damping, reaction-wheel momentum, and three-axis Sun pointing. **Load worked example** supplies a complete reference graph when you want to compare your build. **Save model** exports your diagram and parameters as JSON; **Load model** restores them. Save before switching lessons, which clears the current graph. Simulation history and instantaneous integrator states are not included in model files.

Choosing another lesson opens a preview explaining the new concepts, the blocks added or changed relative to the current lesson, and why they are needed. **Start lesson** confirms the switch; **Cancel** preserves the current model. The simulation pauses while you read the preview.

The three-axis lesson adds explicit quaternion differentiation and coordinate rotation operators. Its integrator still holds the quaternion state, and the wheel/rigid-body equations are assembled from separate blocks. It uses exact state feedback, not a noisy sensor estimator. The tutorial explains ideal Sun-sensor differencing and why a second reference is needed to determine full attitude.

## Navigating the two views

The **Speed** selector offers 1×, 2×, 5×, 10× and 20× simulation time. Faster modes batch the same 0.05-second samples and retain the maximum 0.01-second RK4 integration step. Scope axes remain fixed. The selected multiplier is a target relative to wall time; complex diagrams may run slower if the computer cannot keep up. Hidden browser tabs suspend time accumulation instead of performing a large catch-up when reopened.

The simulation automatically pauses once all components of the lesson's body-rate signal have magnitude below **1e-5 rad/s**, after at least one component has reached or exceeded that threshold. This prevents an immediate stop at an initially stationary state. One-axis lessons apply the same condition to their single rate. The condition is checked every 0.05 simulated seconds, including inside speedup batches; final states and history are retained. This is a spin threshold, not a pointing-error criterion or a guarantee that motion will remain below the threshold if simulation resumes.

The body-rate scope's numeric reading displays **[0, 0, 0]** once all three components are below this threshold (or **0** for a one-axis rate). This is display rounding only: the integrator states, subsequent dynamics, and plotted traces retain their actual values.

In the diagram, scroll the mouse wheel to zoom smoothly around the cursor (20–250%). Hold the middle mouse button and drag to pan. You can also enter a zoom percentage or use **Fit diagram** to frame all blocks. Block placement and alignment snapping follow the transformed coordinates.

In the spacecraft view, left-drag to orbit, scroll to move the camera closer or farther away, and middle-drag to pan. **Reset camera** restores the initial view; **+Z view** and **+X view** look along those world axes. The model uses perspective projection, visible-face culling, solar-cell details, aluminum perimeter rails, corner fasteners, and centered Sun sensors. Camera controls change only the view, never the simulated attitude or angular velocity.

## Verification

```powershell
python -m unittest test_cubesat_control_lab
```

The tutorial links University of Michigan control teaching material and NASA spacecraft references. Its gains, lessons and simplified assumptions are specific educational choices for this application. The model format is JSON, not a Simulink `.slx` file.
