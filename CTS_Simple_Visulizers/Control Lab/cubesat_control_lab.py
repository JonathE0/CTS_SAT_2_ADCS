#!/usr/bin/env python3
"""CubeSat Control Lab: executable block diagrams and guided attitude lessons.

Run python cubesat_control_lab.py; Python 3.10+, standard library only.
The browser edits graphs; Python evaluates their actual wires and integrates
their Integrator blocks with RK4 (maximum step 0.01 s). No MATLAB is needed.
Educational ideal model: J=1/600 kg m^2, Jw=1e-5 kg m^2, no external
disturbance or physical wheel speed limit. All internal signals use SI units.
"""
import argparse
import json
import math
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

J = 1 / 600
JW = 1e-5
PORTS = {'Constant': 0, 'Gain': 1, 'Sum': 2, 'Integrator': 1,
         'Saturation': 1, 'Cross Product': 2, 'Normalize': 1, 'Scope': 1,
         'Rotate to Body': 2, 'Quaternion Rate': 2}


def checked(v):
    if isinstance(v, list):
        if len(v) not in (3, 4):
            raise ValueError('Vector shape must be 3 or 4.')
        return [scalar(x) for x in v]
    return scalar(v)


def scalar(v):
    if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) or abs(v) > 1e9:
        raise ValueError('Signals and parameters must be finite numbers within +/-1e9.')
    return float(v)


def add(a, b):
    if isinstance(a, list) != isinstance(b, list) or isinstance(a, list) and len(a) != len(b):
        raise ValueError('Signal shape mismatch: connect matching scalars or vectors.')
    return [x+y for x, y in zip(a, b)] if isinstance(a, list) else a+b


def scale(a, k):
    return [x*k for x in a] if isinstance(a, list) else a*k


def cross(a, b):
    if not isinstance(a, list) or not isinstance(b, list) or len(a) != 3 or len(b) != 3:
        raise ValueError('Cross Product needs two 3-vector inputs (shape 3).')
    return [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]]


def rotation(q):
    if not isinstance(q, list) or len(q) != 4 or math.hypot(*q) < 1e-12:
        raise ValueError('Attitude input must have quaternion shape 4 and nonzero norm.')
    w, x, y, z = scale(q, 1/math.hypot(*q))
    return [[1-2*(y*y+z*z), 2*(x*y-w*z), 2*(x*z+w*y)],
            [2*(x*y+w*z), 1-2*(x*x+z*z), 2*(y*z-w*x)],
            [2*(x*z-w*y), 2*(y*z+w*x), 1-2*(x*x+y*y)]]


class Graph:
    def __init__(self, graph):
        if not isinstance(graph, dict) or not isinstance(graph.get('nodes'), list) or not isinstance(graph.get('edges'), list):
            raise ValueError('Model needs nodes and edges lists.')
        if not 1 <= len(graph['nodes']) <= 100 or len(graph['edges']) > 200:
            raise ValueError('Use 1 to 100 blocks and at most 200 wires.')
        self.nodes = {}
        for n in graph['nodes']:
            if not isinstance(n, dict) or n.get('type') not in PORTS or not isinstance(n.get('id'), str):
                raise ValueError('Invalid block type or identifier.')
            if n['id'] in self.nodes or len(n['id']) > 80:
                raise ValueError('Block identifiers must be unique and short.')
            checked(n.get('value', 0))
            if n['type'] in ('Gain', 'Saturation', 'Sum'):
                scalar(n.get('value', 1))
            self.nodes[n['id']] = n
        self.inputs = {}
        for e in graph['edges']:
            if not isinstance(e, dict) or e.get('source') not in self.nodes or e.get('target') not in self.nodes:
                raise ValueError('Wire refers to a missing block.')
            port = e.get('port')
            if type(port) is not int or not 0 <= port < PORTS[self.nodes[e['target']]['type']]:
                raise ValueError('Invalid input port.')
            key = (e['target'], port)
            if key in self.inputs:
                raise ValueError('Only one wire may feed an input.')
            self.inputs[key] = e['source']
        for k, n in self.nodes.items():
            for p in range(PORTS[n['type']]):
                if (k, p) not in self.inputs:
                    raise ValueError(f"Connect {n.get('label', k)} input {p+1}.")
        self.integrators = [k for k, n in self.nodes.items() if n['type'] == 'Integrator']

    def initial(self, state):
        if not isinstance(state, dict):
            raise ValueError('Integrator state must be an object.')
        result = {}
        for k in self.integrators:
            n = self.nodes[k]
            v = checked(state.get(k, n.get('value', 0)))
            add(v, scale(checked(n.get('value', 0)), 0))
            if n.get('quaternion'):
                rotation(v)
                v = scale(v, 1/math.hypot(*v))
            result[k] = v
        return result

    def evaluate(self, state):
        values, visiting = dict(state), set()

        def evaluate(k):
            if k in values:
                return values[k]
            if k in visiting:
                raise ValueError('Algebraic loop: feedback needs an Integrator block.')
            visiting.add(k)
            n = self.nodes[k]
            t = n['type']
            a = [evaluate(self.inputs[k, p]) for p in range(PORTS[t])]
            v = n.get('value', 1)
            if t == 'Constant':
                out = v
            elif t == 'Gain':
                out = scale(a[0], v)
            elif t == 'Sum':
                out = add(a[0], scale(a[1], v))
            elif t == 'Scope':
                out = a[0]
            elif t == 'Saturation':
                lim = abs(v)
                out = [max(-lim, min(lim, x)) for x in a[0]] if isinstance(a[0], list) else max(-lim, min(lim, a[0]))
            elif t == 'Cross Product':
                out = cross(*a)
            elif t == 'Normalize':
                if not isinstance(a[0], list):
                    raise ValueError('Normalize requires vector shape 3 or 4.')
                norm = math.hypot(*a[0])
                if norm < 1e-12:
                    raise ValueError('Cannot normalize a zero vector; no Sun direction is available.')
                out = scale(a[0], 1/norm)
            elif t == 'Rotate to Body':
                r = rotation(a[0])
                if not isinstance(a[1], list) or len(a[1]) != 3:
                    raise ValueError('Direction must have vector shape 3.')
                out = [sum(r[j][i]*a[1][j] for j in range(3)) for i in range(3)]
            elif t == 'Quaternion Rate':
                rotation(a[0])
                if not isinstance(a[1], list) or len(a[1]) != 3:
                    raise ValueError('Angular velocity must have vector shape 3.')
                w, x, y, z = a[0]
                b, c, d = a[1]
                out = scale([-x*b-y*c-z*d, w*b+y*d-z*c,
                             w*c+z*b-x*d, w*d+x*c-y*b], .5)
            else:
                raise ValueError('Unsupported block.')
            values[k] = checked(out)
            visiting.remove(k)
            return values[k]

        for k in self.nodes:
            evaluate(k)
        derivatives = {k: evaluate(self.inputs[k, 0]) for k in self.integrators}
        for k, v in derivatives.items():
            add(state[k], v)
        return derivatives, values


def simulate(graph, state, dt):
    dt = scalar(dt)
    if not 0 <= dt <= .1:
        raise ValueError('Time step must be between 0 and 0.1 seconds.')
    model = Graph(graph)
    state = model.initial(state)
    count = max(1, math.ceil(dt/.01))
    step = dt/count
    for _ in range(count):
        def shifted(d, factor):
            return {k: add(state[k], scale(d[k], factor)) for k in state}
        k1, _ = model.evaluate(state)
        k2, _ = model.evaluate(shifted(k1, step/2))
        k3, _ = model.evaluate(shifted(k2, step/2))
        k4, _ = model.evaluate(shifted(k3, step))
        state = model.initial({k: add(state[k], scale(add(add(k1[k], scale(k2[k], 2)),
                         add(scale(k3[k], 2), k4[k])), step/6)) for k in state})
    return state, model.evaluate(state)[1]


def simulate_batch(graph, state, dt, steps=1, auto_stop=False, settle_armed=False):
    """Speed up elapsed simulation time without enlarging integration steps."""
    if type(steps) is not int or not 1 <= steps <= 40:
        raise ValueError('Batch size must be an integer from 1 to 40.')
    if type(auto_stop) is not bool or type(settle_armed) is not bool:
        raise ValueError('Auto-stop flags must be boolean.')
    def rates(values):
        rate = values.get('rate')
        if isinstance(rate, list):
            return rate if len(rate) == 3 else []
        return [rate] if isinstance(rate, (int, float)) else []
    if auto_stop:
        state, initial_values = simulate(graph, state, 0)
        settle_armed = settle_armed or any(abs(x) >= 1e-5 for x in rates(initial_values))
    samples = []
    for i in range(steps):
        state, values = simulate(graph, state, dt)
        if dt > 0:
            body_rates = rates(values)
            settle_armed = settle_armed or any(abs(x) >= 1e-5 for x in body_rates)
            settled = auto_stop and settle_armed and bool(body_rates) and all(abs(x) < 1e-5 for x in body_rates)
            samples.append({'offset': (i+1)*dt, 'values': values,
                            'settle_armed': settle_armed, 'settled': settled})
            if settled:
                break
    return state, values, samples


SOURCES = [
    ['University of Michigan: feedback and PID', 'https://eecs.umich.edu/courses/eecs373.w05/lecture/control.html'],
    ['NASA: small spacecraft guidance, navigation and control', 'https://www.nasa.gov/smallsat-institute/sst-soa/guidance-navigation-and-control/'],
    ['NASA: spacecraft attitude simulation equations', 'https://ntrs.nasa.gov/citations/20030032268'],
]


def node(k, t, label, value, x, y, why, unit='', **extra):
    return dict(id=k, type=t, label=label, value=value, x=x, y=y, why=why, unit=unit, **extra)


def lesson_graph(index):
    def wire(s, t, p=0):
        return dict(source=s, target=t, port=p)
    n, e = [], []
    def put(k, t, label, value, x, y, why, unit='', **extra):
        n.append(node(k, t, label, value, x, y, why, unit, **extra))
    def link(s, t, p=0):
        e.append(wire(s, t, p))
    if index < 4:
        if index == 0:
            put('torque', 'Constant', 'Applied torque', .0001, 70, 100, 'Start with a known external torque. This first experiment isolates Newton’s rotational law before adding wheels.', 'N m')
            source = 'torque'
        else:
            put('target', 'Constant', 'Target angle', 0, 50, 70, 'Choose the desired Y-axis angle in radians. Zero points body +Z toward world +Z.', 'rad')
            put('error', 'Sum', 'Angle error', -1, 245, 70, 'Connect target to input 1 and measured angle to input 2. The second-input gain is −1, so error = target − angle.', 'rad')
            put('kp', 'Gain', 'Proportional Kp', .0000375, 440, 70, 'Multiply angle error by Kp to request restoring torque. More gain turns harder; it does not itself dissipate motion.', 'N m')
            link('target', 'error'); link('angle', 'error', 1); link('error', 'kp')
            source = 'kp'
            if index >= 2:
                put('kd', 'Gain', 'Rate damping Kd', .0005, 440, 265, 'Feed measured angular velocity into Kd. Subtract this torque to brake motion; differentiating the target is unnecessary.', 'N m')
                put('command', 'Sum', 'P minus damping', -1, 635, 70, 'Input 1 is Kp × error. Input 2 is Kd × rate. Negative rate feedback adds damping.', 'N m')
                link('rate', 'kd'); link('kp', 'command'); link('kd', 'command', 1)
                source = 'command'
            if index == 3:
                put('motor_sign', 'Gain', 'Wheel torque sign', -1, 830, 70, 'The wheel motor must exert the opposite torque to the requested satellite motor torque.', 'N m')
                put('limit', 'Saturation', 'Motor torque limit', .0001, 1025, 70, 'Clip each motor torque to ±0.0001 N m. A finite motor cannot deliver arbitrary torque.', 'N m')
                put('reaction', 'Gain', 'Reaction on box', -1, 1025, 265, 'Return equal-and-opposite motor torque to the spacecraft: tau_box = −u_wheel.', 'N m')
                put('momentum', 'Integrator', 'Wheel momentum', 0, 830, 465, 'Integrate wheel torque: dh/dt = u. Its state stores momentum even after the box stops.', 'N m s')
                put('wheel_speed', 'Gain', 'Absolute wheel rate', 1/JW, 1025, 465, 'Divide absolute axial momentum by Jw = 1e−5 kg m².', 'rad/s')
                put('relative', 'Sum', 'Relative wheel rate', -1, 1220, 465, 'Subtract body rate to get wheel speed relative to the satellite.', 'rad/s')
                put('rpm', 'Gain', 'Wheel RPM', 60/math.tau, 1415, 465, 'Convert radians per second into revolutions per minute.', 'RPM')
                link(source, 'motor_sign'); link('motor_sign', 'limit'); link('limit', 'reaction')
                link('limit', 'momentum'); link('momentum', 'wheel_speed'); link('wheel_speed', 'relative'); link('rate', 'relative', 1); link('relative', 'rpm')
                source = 'reaction'
        put('inertia', 'Gain', 'Inverse inertia 1/J', 1/J, 70, 465, 'Newton’s law is alpha = torque / J. For our 1 kg, 0.1 m cube, J = mL²/6 = 1/600 kg m².', 'rad/s²')
        put('rate', 'Integrator', 'Body angular rate', 0, 265, 465, 'Acceleration integrates into angular velocity. With zero torque, an existing spin continues.', 'rad/s')
        put('angle', 'Integrator', 'Body angle', 0 if index == 0 else .5, 460, 465, 'Angular velocity integrates into angle. This is a physical state integrator, not integral feedback on error.', 'rad')
        put('scope', 'Scope', 'Angle scope', 0, 655, 650, 'A scope observes its input without changing it. Compare P oscillation with PD settling.', 'rad')
        link(source, 'inertia'); link('inertia', 'rate'); link('rate', 'angle'); link('angle', 'scope')
    elif index == 4:
        put('sun', 'Constant', 'Sun world vector', [0, 0, 1], 50, 60, 'Use a nonzero world-frame Sun direction. Edit the three components to choose a new target.', 'vector')
        put('sun_unit', 'Normalize', 'Unit Sun direction', 0, 250, 60, 'Direction is independent of brightness. Normalize the nonzero direction vector.', 'unit vector')
        put('sun_body', 'Rotate to Body', 'Sun in body axes', 0, 450, 60, 'Input 1 is scalar-first quaternion q; input 2 is the world Sun vector. Output R(q)ᵀs expresses the target in wheel/body coordinates.', 'unit vector')
        put('z', 'Constant', 'Body +Z', [0, 0, 1], 250, 245, 'Body +Z is fixed in body coordinates. Its world direction changes as attitude changes.', 'unit vector')
        put('error', 'Cross Product', 'Pointing cross error', 0, 650, 60, 'Input 1 is +Z; input 2 is body Sun. z × s gives the right-handed turn direction and magnitude sin(theta). It vanishes at 180° too; avoid exact antiparallel starts in this basic controller.', 'dimensionless')
        put('kp', 'Gain', 'Proportional Kp', .0000375, 850, 60, 'Apply proportional torque to the cross-product error. This is a small-error PD design, not a globally guaranteed acquisition law.', 'N m')
        put('kd', 'Gain', 'Rate damping Kd', .0005, 850, 245, 'Damp all three body rates. A Sun vector sets two pointing degrees of freedom, not an absolute roll angle.', 'N m')
        put('command', 'Sum', 'P minus damping', -1, 1050, 60, 'Combine restoring torque with braking torque, in the same body frame.', 'N m')
        put('motor_sign', 'Gain', 'Wheel torque sign', -1, 1250, 60, 'Negate the requested satellite motor torque.', 'N m')
        put('limit', 'Saturation', 'Motor torque limit', .0001, 1450, 60, 'Apply ±0.1 mN m independently to the three motor axes.', 'N m')
        put('reaction', 'Gain', 'Reaction torque', -1, 1450, 245, 'The motor reaction torque on the box is −u.', 'N m')
        put('momentum', 'Integrator', 'Wheel momentum', [0, 0, 0], 1250, 440, 'Integrate the three wheel torques into absolute axial wheel momenta.', 'N m s')
        put('body_h', 'Gain', 'Body momentum Jω', J, 650, 635, 'Multiply body rate omega by spacecraft inertia J. This is J × omega, not wheel inertia.', 'N m s')
        put('total_h', 'Sum', 'Total body-frame H', 1, 850, 635, 'Add J omega and wheel momentum h. Inertial total momentum is conserved; its body coordinates can change.', 'N m s')
        put('gyro', 'Cross Product', 'Gyroscopic transport', 0, 1050, 635, 'Compute omega × (J omega + h). Rotating coordinates require this term in Euler’s equation.', 'N m')
        put('net', 'Sum', 'Torque minus transport', -1, 1450, 635, 'Compute −u − omega × (J omega + h). This drives body angular acceleration after division by J.', 'N m')
        put('inertia', 'Gain', 'Inverse inertia 1/J', 1/J, 1450, 830, 'The cube has equal principal inertias, so a scalar gain applies to all axes.', 'rad/s²')
        put('rate', 'Integrator', 'Body angular rate', [0, 0, 0], 1050, 830, 'Integrate the vector angular acceleration. The result is body-frame omega, not Euler-angle derivatives.', 'rad/s')
        put('qdot', 'Quaternion Rate', 'Quaternion derivative', 0, 450, 830, 'Input 1 is q; input 2 is omega. Compute qdot = 0.5 q ⊗ [0,omega]. This mathematical operator contains no hidden integration.', '1/s')
        put('attitude', 'Integrator', 'Attitude quaternion', [math.cos(.4), 0, math.sin(.4), 0], 50, 635, 'Integrate qdot to orientation. Scalar-first q maps body to world. Unit-norm correction prevents numerical drift; three independent angle integrators are not valid general attitude kinematics.', 'quaternion', quaternion=True)
        put('scope', 'Scope', 'Body-rate scope', 0, 650, 1010, 'Watch all three components approach zero. Pointing error and wheel RPM also appear beside the CubeSat.', 'rad/s')
        for s,t,p in [('sun','sun_unit',0),('attitude','sun_body',0),('sun_unit','sun_body',1),('z','error',0),('sun_body','error',1),('error','kp',0),('rate','kd',0),('kp','command',0),('kd','command',1),('command','motor_sign',0),('motor_sign','limit',0),('limit','reaction',0),('limit','momentum',0),('rate','body_h',0),('body_h','total_h',0),('momentum','total_h',1),('rate','gyro',0),('total_h','gyro',1),('reaction','net',0),('gyro','net',1),('net','inertia',0),('inertia','rate',0),('attitude','qdot',0),('rate','qdot',1),('qdot','attitude',0),('rate','scope',0)]:
            link(s,t,p)
    else:
        raise ValueError('Unknown lesson.')
    return {'nodes': n, 'edges': e}


LESSONS = [
    dict(title='01 / Torque becomes motion', subtitle='Build the plant', text='Start with an empty canvas. Drag each requested primitive from the library into the outlined position, then connect its ports. The graph itself is the simulator: torque → 1/J → ∫ → ∫ → scope. Run for 1 s: expect rate 0.06 rad/s and angle 0.03 rad. Set applied torque to zero and give the rate integrator a nonzero initial value to see free rotation.', source=2, experiment='Try doubling J by changing 1/J from 600 to 300. Why does angular acceleration halve?'),
    dict(title='02 / Close the loop', subtitle='Proportional feedback', text='Build target − measured angle and multiply by Kp. The angle starts at 0.5 rad. Proportional torque always pulls toward the target, but the ideal plant has no friction, so it overshoots and oscillates. Follow the feedback wire from the angle integrator back to the subtracting input.', source=0, experiment='Run for 40 simulated seconds. Increase Kp: oscillations become faster. Neither physical integrator is an integral controller.'),
    dict(title='03 / Add braking', subtitle='PD control', text='Add Kd × measured rate and subtract it from the P command. This brakes motion before the target is crossed. For small errors J theta_ddot + Kd theta_dot + Kp theta = 0. Our illustrative gains use Kp = J(0.15)² and Kd = 2J(0.15), approximately critical damping without clipping.', source=0, experiment='Set Kd to zero to recover lesson 2. Too little damping oscillates; too much slows the response. No persistent disturbance is present, so integral error feedback is not needed here.'),
    dict(title='04 / Exchange momentum', subtitle='Reaction-wheel actuation', text='Keep the PD loop and build the wheel from a sign gain, saturation and an integrator. The motor accelerates the wheel and exerts opposite torque on the box. Momentum h persists when motor torque becomes zero. Wheel RPM is (h/Jw − omega) × 60/(2π). The command limit is not a physical wheel-speed limit.', source=1, experiment='Use Random spin, then run. Check H = J omega + h stays constant. When the box stops, the wheel can still spin. Resetting wheel momentum would change the physical initial condition.'),
    dict(title='05 / Point +Z at the Sun', subtitle='Three-axis attitude and determination', text='Now scalar signals become vectors and orientation becomes a quaternion. Build z × s_body, rate damping, and the rigid-body cross term from separate blocks. Two mathematical operators expose frame rotation and quaternion differentiation; the Integrator still owns attitude state. Ideal opposite Sun-sensor differences give d = [(I+X−I−X)/K, (I+Y−I−Y)/K, (I+Z−I−Z)/K]; normalize d for a measured body Sun direction. This lesson uses exact Rᵀs instead, plus exact gyro rates, to isolate control design. A single Sun vector cannot determine absolute roll; a second independent reference is needed for full attitude determination.', source=1, experiment='Edit the Sun vector or start a random spin. Test a sideways target. Exactly anti-Sun and zero rate is a blind equilibrium of the basic cross-product controller; a robust acquisition controller needs an explicit escape maneuver or axis-angle logic. Gains here are educational, not flight validated.'),
]

HTML = r'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>CubeSat / Control Lab</title>
<style>
:root{color-scheme:dark;--bg:#081320;--panel:#101f30;--line:#29465d;--ink:#e8f5ff;--muted:#9db5c9;--blue:#8edbff;--green:#9af2c5}*{box-sizing:border-box}body{margin:0;background:radial-gradient(ellipse at 75% 0,#244963,transparent 60%),var(--bg);color:var(--ink);font:14px system-ui,sans-serif}header{padding:22px 28px;border-bottom:1px solid var(--line);display:flex;justify-content:space-between;align-items:center}h1{font-size:23px;margin:2px 0;letter-spacing:-.5px}.eyebrow{font:11px monospace;letter-spacing:2px;color:var(--blue)}button,select,input{font:inherit;color:var(--ink);background:#152a3d;border:1px solid #426780;border-radius:5px;padding:7px 10px}button{cursor:pointer}button:hover{background:#254963}button:focus-visible,a:focus-visible,input:focus-visible,select:focus-visible{outline:2px solid var(--blue);outline-offset:3px}.primary{background:#a0def9;color:#082236;border-color:#a0def9}button:disabled{opacity:.45;cursor:default}a{color:var(--blue)}p{line-height:1.6;color:var(--muted)}main{display:grid;grid-template-columns:285px minmax(480px,1fr) 350px;gap:16px;padding:18px}aside,.viewer{background:#0c1927cc;border:1px solid var(--line);border-radius:8px;padding:16px}h2{font-size:15px;margin:0 0 12px}h3{font-size:13px}.toolbar{display:flex;gap:7px;flex-wrap:wrap;margin-bottom:10px}.small{font-size:12px;color:var(--muted);line-height:1.5}.library{display:grid;grid-template-columns:1fr 1fr;gap:6px}.library button{font-size:12px;padding:10px 5px}.library .recommended{border:2px solid var(--green)}.editor{min-width:0}#viewport{position:relative;height:650px;overflow:hidden;touch-action:none;border:1px solid var(--line);border-radius:8px;background:#0c1825}#workspace{position:absolute;transform-origin:0 0;will-change:transform;width:1700px;height:1250px;background-image:radial-gradient(#31465a 1px,transparent 1px);background-size:20px 20px}#wires{position:absolute;width:100%;height:100%;overflow:visible;pointer-events:none}.wire{fill:none;stroke:#80cfff;stroke-width:2;pointer-events:stroke;cursor:pointer}.wire:hover{stroke:#fff;stroke-width:5}.block{position:absolute;width:160px;min-height:100px;border:1px solid #7299b2;background:#142b3f;border-radius:5px;box-shadow:0 7px 16px #0004;touch-action:none}.block.selected{border:2px solid var(--blue)}.block header{padding:8px 10px;font-size:11px;display:block;cursor:grab;background:#203d53;border-bottom:1px solid #54758a;letter-spacing:1px}.block strong{display:block;font-size:12px;padding:9px 13px 2px}.block .value{font:11px monospace;color:var(--blue);padding:4px 13px 10px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.port{position:absolute;width:22px;height:22px;padding:0;border-radius:50%;font:10px monospace;background:#bceaff;color:#0a2436;border:2px solid #203d53}.port.input{left:-12px}.port.output{right:-12px;top:42px}.port.active{background:var(--green)}#ghost{position:absolute;width:160px;min-height:100px;border:2px dashed var(--green);border-radius:5px;color:var(--green);padding:14px;font-size:12px;background:#153d3933;pointer-events:none}.step{padding:12px;background:#142b3e;border-left:3px solid var(--green);margin:12px 0;line-height:1.6}#inspector{border-top:1px solid var(--line);margin-top:18px;padding-top:14px}#parameter{width:100%;font:12px monospace;margin:8px 0}#lessonText{max-height:290px;overflow:auto}#scene{width:100%;height:350px;cursor:grab;touch-action:none;background:radial-gradient(ellipse,#1b4059,transparent 70%);border-bottom:1px solid var(--line)}#plot{width:100%;height:190px}.stats{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin:16px 0}.stats b{display:block;font:18px monospace;margin-top:5px}.status{padding:9px 12px;background:#142b3e;border-left:3px solid var(--blue);min-height:39px;line-height:1.5;margin:10px 0}#lesson{width:100%;margin-bottom:12px}.unit{font:11px monospace;color:var(--muted)}#wireHint{color:var(--green);min-height:36px}details{margin-top:14px}summary{cursor:pointer;color:var(--blue)}.viewer{align-self:start}#scopeSelect{max-width:100%;margin:8px 0}label{font-size:12px}#speed{width:75px}#stepCount{color:var(--green)}@media(max-width:1250px){main{grid-template-columns:250px minmax(450px,1fr)}.viewer{grid-column:1/-1;display:grid;grid-template-columns:1fr 1fr;gap:20px}}@media(max-width:760px){main{display:block;padding:10px}aside,.editor,.viewer{margin-bottom:15px}.viewer{display:block}header{padding:15px}#viewport{height:500px}}

dialog{width:min(480px,92vw);background:#102638;color:var(--ink);border:1px solid #72b3d8;border-radius:10px;padding:24px;box-shadow:0 20px 80px #0009}dialog::backdrop{background:#020b14b3}dialog input{width:100%;margin:6px 0 14px}[hidden]{display:none!important}dialog .toolbar{justify-content:flex-end;margin-top:18px}.axis-fields{display:grid;grid-template-columns:1fr 1fr;gap:8px}.axis-fields input{width:100%;min-width:0;margin:4px 0}.axis-fields label{display:block}.axis-fields button{grid-column:1/-1}.block:focus-visible{outline:2px solid var(--green)}
</style></head><body><header><div><div class="eyebrow">CTS / LEARN BY BUILDING</div><h1>CubeSat Control Lab</h1></div><span class="small">1U · basic blocks · real signal flow</span></header>
<main><aside><label for="lesson">Guided lesson</label><select id="lesson"></select><h2 id="subtitle"></h2><div id="lessonText"></div><div class="small" id="stepCount"></div><div class="step" id="step"></div><button id="locate">Show next location</button><h3>Block library</h3><p class="small">Drag a block onto the grid, or click its name to place it at the highlighted location.</p><div class="library" id="library"></div><div id="inspector"><h3>Selected block</h3><div id="selection" class="small">Double-click a block to edit it in place.</div><label for="parameter">Value / initial condition (JSON)</label><input id="parameter" aria-label="Block parameter" placeholder="0.5 or [0,0,1]"><button id="apply">Apply value</button> <button id="remove">Delete block</button><p id="why" class="small"></p></div></aside>
<section class="editor"><div class="toolbar"><button id="run" class="primary">Run</button><button id="reset">Reset states</button><button id="spin">Random spin</button><button id="validate">Check wiring</button><label>Zoom <input id="zoom" type="number" min="20" max="250" step="5" value="100" aria-label="Diagram zoom percent" style="width:72px"> %</label><button id="fit">Fit diagram</button><label>Speed <select id="speed"><option value="1">1×</option><option value="2">2×</option><option value="5">5×</option><option value="10">10×</option><option value="20">20×</option></select></label></div><div class="toolbar"><button id="example">Load worked example</button><button id="clear">Clear canvas</button><button id="save">Save model</button><button id="load">Load model</button><input id="file" type="file" accept=".json" hidden></div><div id="status" class="status" role="status" aria-live="polite">Build your first signal chain.</div><div class="small" id="wireHint">Wheel: zoom around cursor · Middle drag: pan the diagram. Connect an output circle to an input circle. Wires avoid blocks with 90° turns. Connected ports snap within 10 screen pixels while dragging; hold Alt for free movement. Dashed wires mean overlapping blocks prevent routing. Double-click a block to edit. Escape cancels a connection.</div><div id="viewport"><div id="workspace"><svg id="wires"></svg><div id="ghost"></div><div id="nodes"></div></div></div><details><summary>Experiment and equations</summary><p id="experiment"></p><p class="small">SI units throughout. Gain: y = kx. Sum: y = input 1 + k × input 2. Integrator: dx/dt = input, output = x. Saturation: y = clip(x, −|limit|, +|limit|). Cross Product: y = input 1 × input 2. RK4 uses steps ≤0.01 s. Scopes are passive observations. Feedback must pass through an integrator; direct algebraic loops are rejected.</p><p class="small">The last lesson adds two explicit mathematical operators: Rotate to Body computes R(q)ᵀs; Quaternion Rate computes ½q⊗[0,ω]. They contain no controller or hidden state. Matching operations can later be implemented with Simulink math blocks. This app does not export .slx files.</p></details></section>
<section class="viewer"><div><div class="eyebrow">LIVE SPACECRAFT</div><canvas id="scene" tabindex="0" aria-label="CubeSat 3D view. Drag to orbit, scroll to zoom, middle drag to pan."></canvas><div class="toolbar"><button id="resetCamera">Reset camera</button><button id="frontCamera">+Z view</button><button id="sideCamera">+X view</button></div><p class="small">Drag: orbit · Wheel: zoom · Middle drag: pan</p><div class="stats"><span class="small">Pointing error<b id="angleRead">—</b></span><span class="small">Body rate<b id="rateRead">—</b></span><span class="small">Wheel RPM<b id="rpmRead">—</b></span><span class="small">Elapsed / simulated<b id="timeRead">0.00 s</b></span></div><p class="small">Cyan: body +Z. Gold: desired Sun direction. One-axis lessons rotate about body Y. The three-axis lesson uses the attitude integrator. Auto-stop: all modeled body rates below 10⁻⁵ rad/s after motion begins. This checks spin, not Sun-pointing accuracy. Values update only when your diagram runs.</p></div><div><h2>Signal scope</h2><label for="scopeSelect">Signal to plot</label><select id="scopeSelect"></select><canvas id="plot"></canvas><div class="axis-fields"><label>Time min (s)<input id="xMin" type="number" step="any" value="0"></label><label>Time max (s)<input id="xMax" type="number" step="any" value="60"></label><label>Y min<input id="yMin" type="number" step="any" value="-1"></label><label>Y max<input id="yMax" type="number" step="any" value="1"></label><button id="applyAxes">Apply fixed axes</button></div><p id="scopeValue" class="unit">No signal yet</p><p class="small">Body-rate readings display as zero when all components are below 10⁻⁵ rad/s. The simulation and plotted traces retain their actual values.</p><p class="small">Vector traces: X cyan · Y green · Z violet · W white when present. Fixed axes: traces outside the chosen limits are clipped, never rescaled. Each signal keeps its own limits. Up to 600 simulated seconds of history are retained; axis labels use the selected block’s units.</p><details open><summary>References and assumptions</summary><div id="sources"></div><p class="small">Lesson explanations and gains are educational derivations for this model. Exact state and Sun direction, no disturbances, ideal centered wheels. A real design needs state estimation and wheel capacity limits. Library connections are checked for signal dimensions, but physical units remain your responsibility.</p></details></div></section></main>
<dialog id="blockDialog" aria-labelledby="editTitle"><form id="blockForm"><h2 id="editTitle">Edit block</h2><label>Block name<input id="editName" required maxlength="100"></label><div id="valueEditor"><label id="editValueLabel" for="editValue">Value</label><input id="editValue" autocomplete="off"></div><div id="scopeEditor" class="axis-fields" hidden><label>Time min (s)<input id="editXMin" type="number" step="any" value="0"></label><label>Time max (s)<input id="editXMax" type="number" step="any" value="60"></label><label>Y min<input id="editYMin" type="number" step="any" value="-1"></label><label>Y max<input id="editYMax" type="number" step="any" value="1"></label></div><p id="editWhy" class="small"></p><p id="editError" role="alert"></p><div class="toolbar"><button type="button" id="cancelEdit">Cancel</button><button type="submit" class="primary">Save changes</button></div></form></dialog>
<dialog id="lessonDialog" aria-labelledby="lessonPreviewTitle"><h2 id="lessonPreviewTitle"></h2><p id="lessonPreviewWhy"></p><h3>What changes in the diagram</h3><div id="lessonPreviewBlocks" style="max-height:38vh;overflow:auto"></div><p id="lessonPreviewExperiment" class="small"></p><p class="small">Starting this lesson clears the current diagram and simulation. Cancel and use Save model first if you want to keep your work.</p><div class="toolbar"><button id="cancelLesson">Cancel</button><button id="beginLesson" class="primary">Start lesson</button></div></dialog>
<script>
const DATA=__DATA__;
const $=id=>document.getElementById(id), clone=x=>structuredClone(x);
let lesson=0, graph={nodes:[],edges:[]}, state={}, values={}, selected=null, pending=null, running=false, busy=false, epoch=0, time=0, history=[], serial=0;
const symbols={'Constant':'Constant','Gain':'Gain ×k','Sum':'Sum + / −','Integrator':'Integrator ∫','Saturation':'Saturation','Cross Product':'Cross Product','Normalize':'Normalize','Scope':'Scope','Rotate to Body':'Rotate to Body','Quaternion Rate':'Quaternion Rate'};
function msg(t){$('status').textContent=t;}
let lastTick=performance.now(),timeCredit=0,settleArmed=false;
function stop(){running=false;timeCredit=0;lastTick=performance.now();$('run').textContent='Run';}
function invalidate(){stop();settleArmed=false;epoch++;state={};values={};time=0;history=[];updateView();}
function recipe(){return DATA.graphs[lesson];}
function nextNode(){return recipe().nodes.find(n=>!graph.nodes.some(g=>g.id===n.id));}
function nextWire(){return recipe().edges.find(e=>!graph.edges.some(g=>g.source===e.source&&g.target===e.target&&g.port===e.port));}
function fmt(v){return Array.isArray(v)?'['+v.map(x=>Number(x).toPrecision(3)).join(', ')+']':Number(v).toPrecision(4);}
function label(id){return graph.nodes.find(n=>n.id===id)?.label||recipe().nodes.find(n=>n.id===id)?.label||id;}
function lessonUI(){const l=DATA.lessons[lesson];$('subtitle').textContent=l.subtitle;$('lessonText').replaceChildren();const p=document.createElement('p');p.className='small';p.textContent=l.text;$('lessonText').append(p);const a=document.createElement('a');a.href=DATA.sources[l.source][1];a.textContent=DATA.sources[l.source][0];a.target='_blank';a.rel='noopener';$('lessonText').append(a);$('experiment').textContent=l.experiment;}
function progress(){const n=nextNode(),w=nextWire();$('ghost').hidden=!n;if(n){$('ghost').style.left=n.x+'px';$('ghost').style.top=n.y+'px';$('ghost').textContent='Place '+n.type+' here: '+n.label;$('step').textContent='Add '+n.type+' → '+n.label+'. '+n.why;}else if(w){$('step').textContent='Connect '+label(w.source)+' output → '+label(w.target)+' input '+(w.port+1)+'. '+recipe().nodes.find(n=>n.id===w.target).why;}else{$('step').textContent='Lesson wiring complete. Check wiring, run, then try the experiment. Edit gains in the inspector to test your prediction.';}$('stepCount').textContent=graph.nodes.filter(n=>recipe().nodes.some(r=>r.id===n.id)).length+'/'+recipe().nodes.length+' lesson blocks · '+recipe().edges.filter(e=>graph.edges.some(g=>g.source===e.source&&g.target===e.target&&g.port===e.port)).length+'/'+recipe().edges.length+' lesson wires';document.querySelectorAll('#library button').forEach(b=>b.classList.toggle('recommended',b.dataset.type===n?.type));drawWires();}
function select(id){selected=id;const n=graph.nodes.find(n=>n.id===id);$('selection').textContent=n?n.label+' · '+n.type+' · '+(n.unit||'units user-defined'):'Select a block.';$('parameter').value=n?JSON.stringify(n.value):'';$('why').textContent=n?.why||'';document.querySelectorAll('.block').forEach(b=>b.classList.toggle('selected',b.dataset.id===id));}
const parameterTypes=new Set(['Constant','Gain','Sum','Integrator','Saturation']);
function parseParameter(n,text){const v=JSON.parse(text);if(!(typeof v==='number'&&Number.isFinite(v)||Array.isArray(v)&&[3,4].includes(v.length)&&v.every(x=>typeof x==='number'&&Number.isFinite(x))))throw Error('Use a finite number or a 3/4-component numeric JSON array.');if(['Gain','Sum','Saturation'].includes(n.type)&&Array.isArray(v))throw Error('This block parameter must be scalar.');return v;}
function validAxes(a){if(!a||!['xMin','xMax','yMin','yMax'].every(k=>typeof a[k]==='number'&&Number.isFinite(a[k]))||a.xMin<0||a.xMax<=a.xMin||a.yMax<=a.yMin)throw Error('Axis limits must be finite, with max greater than min and time min ≥ 0.');return a;}
function defaultAxes(n){const ranges={'rad':1,'rad/s':.2,'rad/s²':.1,'N m':.0001,'N m s':.0005,'RPM':100,'quaternion':1,'unit vector':1,'dimensionless':1};const span=ranges[n?.unit]||1;return {xMin:0,xMax:60,yMin:-span,yMax:span};}
function axesFor(n){return n?.scopeAxes||defaultAxes(n);}
function syncAxes(){const n=graph.nodes.find(n=>n.id===$('scopeSelect').value),a=axesFor(n);for(const k of ['xMin','xMax','yMin','yMax'])$(k).value=a[k];}
let editingId=null;
function openEditor(id){const n=graph.nodes.find(n=>n.id===id);if(!n)return;select(id);editingId=id;$('editTitle').textContent='Edit '+n.type;$('editName').value=n.label;$('valueEditor').hidden=!parameterTypes.has(n.type);$('editValueLabel').textContent=n.type==='Integrator'?'Initial condition (scalar or vector)':n.type==='Sum'?'Second-input gain (+1 adds, −1 subtracts)':n.type==='Saturation'?'Symmetric torque / signal limit':n.type==='Gain'?'Gain':'Constant value (scalar or vector)';$('editValue').value=JSON.stringify(n.value);$('scopeEditor').hidden=n.type!=='Scope';const a=axesFor(n);for(const k of ['xMin','xMax','yMin','yMax'])$('edit'+k[0].toUpperCase()+k.slice(1)).value=a[k];$('editWhy').textContent=n.why||'This mathematical block has no numeric parameter; its inputs determine the result.';$('editError').textContent='';$('blockDialog').showModal();(parameterTypes.has(n.type)?$('editValue'):$('editName')).focus();}
$('cancelEdit').onclick=()=>$('blockDialog').close();
$('blockForm').onsubmit=e=>{e.preventDefault();try{const n=graph.nodes.find(n=>n.id===editingId);if(!n)throw Error('Block no longer exists.');const name=$('editName').value.trim();if(!name)throw Error('Enter a block name.');const v=parameterTypes.has(n.type)?parseParameter(n,$('editValue').value):n.value;let a;if(n.type==='Scope'){a={};for(const k of ['xMin','xMax','yMin','yMax']){const input=$('edit'+k[0].toUpperCase()+k.slice(1));a[k]=input.value.trim()===''?NaN:Number(input.value);}validAxes(a);}const changed=JSON.stringify(v)!==JSON.stringify(n.value);if(changed)invalidate();n.value=v;n.label=name;if(a)n.scopeAxes=a;render();if(n.type==='Scope'){$('scopeSelect').value=n.id;syncAxes();drawPlot();}$('blockDialog').close();msg(changed?'Block updated. Integrator states reset for a repeatable run.':'Block updated; simulation state retained.');}catch(error){$('editError').textContent=error.message;}};
$('applyAxes').onclick=()=>{try{const n=graph.nodes.find(n=>n.id===$('scopeSelect').value);if(!n)throw Error('Select a signal first.');const a={};for(const k of ['xMin','xMax','yMin','yMax'])a[k]=$(k).value.trim()===''?NaN:Number($(k).value);n.scopeAxes=validAxes(a);drawPlot();msg('Fixed scope limits applied; simulation state retained.');}catch(e){msg(e.message);}};
function render(){const root=$('nodes');root.replaceChildren();for(const n of graph.nodes){const b=document.createElement('div');b.className='block';b.dataset.id=n.id;b.style.left=n.x+'px';b.style.top=n.y+'px';const h=document.createElement('header');h.textContent=symbols[n.type];b.append(h);const title=document.createElement('strong');title.textContent=n.label;b.append(title);const val=document.createElement('div');val.className='value';val.textContent=(n.type==='Integrator'?'initial: ':'')+fmt(n.value);b.append(val);for(let p=0;p<DATA.ports[n.type];p++){const port=document.createElement('button');port.className='port input';port.style.top=(DATA.ports[n.type]===2?24+p*34:42)+'px';port.textContent=p+1;port.setAttribute('aria-label',n.label+' input '+(p+1));port.onclick=e=>{e.stopPropagation();connect(n.id,p);};b.append(port);}const out=document.createElement('button');out.className='port output'+(pending===n.id?' active':'');out.textContent='›';out.setAttribute('aria-label',n.label+' output');out.onclick=e=>{e.stopPropagation();pending=n.id;$('wireHint').textContent='From '+n.label+': click the destination input (1 is top, 2 is bottom).';render();};b.append(out);b.onclick=()=>select(n.id);b.tabIndex=0;b.setAttribute('aria-label',n.label+' block. Double-click or press Enter to edit.');b.ondblclick=e=>{if(e.target.closest('.port'))return;e.preventDefault();openEditor(n.id);};b.onkeydown=e=>{if(e.key==='Enter'&&!e.target.closest('.port')){e.preventDefault();openEditor(n.id);}};h.onpointerdown=e=>{if(e.button!==0)return;cancelViewAnimation();select(n.id);h.setPointerCapture(e.pointerId);const start={x:e.clientX,y:e.clientY,nx:n.x,ny:n.y};h.onpointermove=v=>{const zoom=modelView.scale;const proposedX=Math.max(20,Math.min(1520,start.nx+(v.clientX-start.x)/zoom)),proposedY=Math.max(20,Math.min(1120,start.ny+(v.clientY-start.y)/zoom)),snap=snapBlock(n,proposedX,proposedY,zoom,v.altKey);n.x=snap.x;n.y=snap.y;b.style.outline=snap.snapped?'2px solid var(--green)':'';b.style.left=n.x+'px';b.style.top=n.y+'px';drawWires();};h.onpointerup=()=>{b.style.outline='';h.onpointermove=null;h.onpointerup=null;};};root.append(b);}select(selected);const current=$('scopeSelect').value;$('scopeSelect').replaceChildren();for(const n of graph.nodes){const o=document.createElement('option');o.value=n.id;o.textContent=n.label+' ('+(n.unit||'signal')+')';$('scopeSelect').append(o);}if(graph.nodes.some(n=>n.id===current))$('scopeSelect').value=current;else $('scopeSelect').value=graph.nodes.some(n=>n.id==='scope')?'scope':graph.nodes[0]?.id||'';syncAxes();progress();}
function portY(n,p){return DATA.ports[n.type]===2?35+p*34:53;}
function blockRect(n){return {left:n.x-10,right:n.x+170,top:n.y-10,bottom:n.y+118};}
function clearSegment(a,b,rects){
 if(a[0]!==b[0]&&a[1]!==b[1])return false;
 return !rects.some(r=>a[1]===b[1]?a[1]>r.top&&a[1]<r.bottom&&Math.max(a[0],b[0])>r.left&&Math.min(a[0],b[0])<r.right:a[0]>r.left&&a[0]<r.right&&Math.max(a[1],b[1])>r.top&&Math.min(a[1],b[1])<r.bottom);
}
function simplifyPath(points){const out=[];for(const p of points){if(out.length&&p[0]===out.at(-1)[0]&&p[1]===out.at(-1)[1])continue;while(out.length>1){const a=out.at(-2),b=out.at(-1);if((a[0]===b[0]&&b[0]===p[0]&&(b[1]-a[1])*(p[1]-b[1])>=0)||(a[1]===b[1]&&b[1]===p[1]&&(b[0]-a[0])*(p[0]-b[0])>=0))out.pop();else break;}out.push(p);}return out;}
function pathCost(points){return points.slice(1).reduce((sum,p,i)=>sum+Math.abs(p[0]-points[i][0])+Math.abs(p[1]-points[i][1]),0)+24*Math.max(0,points.length-2);}
function routeWire(a,b,port){
 const from=[a.x+160,a.y+53],to=[b.x,b.y+portY(b,port)],others=graph.nodes.filter(n=>n.id!==a.id&&n.id!==b.id).map(blockRect);
 if(to[0]>from[0]&&to[1]===from[1]&&clearSegment(from,to,others))return [from,to];
 const start=[from[0]+12,from[1]],end=[to[0]-12,to[1]],rects=graph.nodes.map(blockRect);
 if(!clearSegment(from,start,graph.nodes.filter(n=>n.id!==a.id).map(blockRect))||!clearSegment(end,to,graph.nodes.filter(n=>n.id!==b.id).map(blockRect)))return null;
 const xs=[...new Set([start[0],end[0],(start[0]+end[0])/2,...rects.flatMap(r=>[r.left,r.right])])].sort((a,b)=>a-b);
 const ys=[...new Set([start[1],end[1],...rects.flatMap(r=>[r.top,r.bottom])])].sort((a,b)=>a-b);
 let best=null,cost=Infinity;
 function consider(middle){for(let i=1;i<middle.length;i++)if(!clearSegment(middle[i-1],middle[i],rects))return;const path=simplifyPath([from,...middle,to]),c=pathCost(path);if(c<cost){cost=c;best=path;}}
 for(const x of xs)consider([start,[x,start[1]],[x,end[1]],end]);
 for(const y of ys)consider([start,[start[0],y],[end[0],y],end]);
 // Simple visibility channels handle most diagrams. A* handles staggered obstacles.
 if(best)return best;
 const ny=ys.length,sx=xs.indexOf(start[0]),sy=ys.indexOf(start[1]),ex=xs.indexOf(end[0]),ey=ys.indexOf(end[1]);
 const heap=[],dist=new Map(),parent=new Map(),edgeCache=new Map();
 function push(v){heap.push(v);let i=heap.length-1;while(i){const p=(i-1)>>1;if(heap[p].f<=v.f)break;heap[i]=heap[p];i=p;}heap[i]=v;}
 function pop(){const root=heap[0],v=heap.pop();if(heap.length){let i=0;while(i*2+1<heap.length){let j=i*2+1;if(j+1<heap.length&&heap[j+1].f<heap[j].f)j++;if(heap[j].f>=v.f)break;heap[i]=heap[j];i=j;}heap[i]=v;}return root;}
 const key=(x,y,d)=>(x*ny+y)*3+d;
 const first=key(sx,sy,1);dist.set(first,0);push({x:sx,y:sy,d:1,k:first,g:0,f:0});
 while(heap.length){
  const v=pop();if(v.g!==dist.get(v.k))continue;
  if(v.x===ex&&v.y===ey){let k=v.k,points=[];while(k!==undefined){const cell=Math.floor(k/3);points.push([xs[Math.floor(cell/ny)],ys[cell%ny]]);k=parent.get(k);}return simplifyPath([from,...points.reverse(),to]);}
  for(const [dx,dy,d] of [[-1,0,1],[1,0,1],[0,-1,2],[0,1,2]]){const x=v.x+dx,y=v.y+dy;if(x<0||x>=xs.length||y<0||y>=ys.length)continue;
   const cell=v.x*ny+v.y,next=x*ny+y,ek=Math.min(cell,next)+':'+Math.max(cell,next);
   let free=edgeCache.get(ek);if(free===undefined){free=clearSegment([xs[v.x],ys[v.y]],[xs[x],ys[y]],rects);edgeCache.set(ek,free);}if(!free)continue;
   const k=key(x,y,d),g=v.g+Math.abs(xs[x]-xs[v.x])+Math.abs(ys[y]-ys[v.y])+(d===v.d?0:24);
   if(g>=(dist.get(k)??Infinity))continue;dist.set(k,g);parent.set(k,v.k);push({x,y,d,k,g,f:g+Math.abs(xs[x]-end[0])+Math.abs(ys[y]-end[1])});
  }
 }
 return null;
}
function svgPath(points){return points.map((p,i)=>i?(p[1]===points[i-1][1]?'H'+p[0]:'V'+p[1]):'M'+p[0]+','+p[1]).join(' ');}
function orthogonalPath(a,b,port){const path=routeWire(a,b,port);if(path)return svgPath(path);return svgPath([[a.x+160,a.y+53],[b.x-12,a.y+53],[b.x-12,b.y+portY(b,port)],[b.x,b.y+portY(b,port)]]);}
function snapBlock(n,x,y,zoom,bypass){
 if(bypass)return {x,y,snapped:false};
 let delta=10/zoom,target=y;
 for(const e of graph.edges){
  const a=graph.nodes.find(b=>b.id===e.source),b=graph.nodes.find(b=>b.id===e.target);if(!a||!b||a.id===b.id)continue;
  let desired;
  if(e.target===n.id&&x>=a.x+176)desired=a.y+53-portY(n,e.port);
  else if(e.source===n.id&&b.x>=x+176)desired=b.y+portY(b,e.port)-53;
  else continue;
  if(desired<20||desired>1120)continue;
  const diff=Math.abs(desired-y);
  if(diff<delta){delta=diff;target=desired;}
 }
 return {x,y:target,snapped:target!==y};
}
function drawWires(){const svg=$('wires');svg.replaceChildren();graph.edges.forEach((e,i)=>{const a=graph.nodes.find(n=>n.id===e.source),b=graph.nodes.find(n=>n.id===e.target);if(!a||!b)return;const path=document.createElementNS('http://www.w3.org/2000/svg','path');const route=routeWire(a,b,e.port);path.setAttribute('d',route?svgPath(route):orthogonalPath(a,b,e.port));if(!route){path.setAttribute('stroke-dasharray','5 5');path.dataset.blocked='true';}path.classList.add('wire');path.onclick=()=>{invalidate();graph.edges.splice(i,1);render();msg('Wire removed. Reconnect before running.');};const title=document.createElementNS('http://www.w3.org/2000/svg','title');title.textContent=label(e.source)+' → '+label(e.target)+' input '+(e.port+1)+ (route?' (click to remove)':' — routing blocked: separate overlapping blocks (click to remove)');path.append(title);svg.append(path);});}
function connect(target,port){if(!pending){msg('Choose an output circle first.');return;}invalidate();graph.edges=graph.edges.filter(e=>!(e.target===target&&e.port===port));graph.edges.push({source:pending,target,port});pending=null;$('wireHint').textContent='Wire connected. Click another output to branch its signal, or click a wire to remove it.';render();}
function addBlock(type,x,y){invalidate();if(graph.nodes.length>=100){msg('Maximum 100 blocks.');return;}const expected=nextNode();let n;if(expected&&expected.type===type)n=clone(expected);else n={id:'custom_'+(++serial)+'_'+Date.now(),type,label:type,value:type==='Gain'?1:type==='Sum'?-1:type==='Saturation'?.0001:0,x:100,y:100,why:'Custom primitive. Set its parameter and connect its inputs. Vector parameters use JSON arrays.',unit:''};if(x!==undefined){n.x=Math.max(20,Math.min(1520,x));n.y=Math.max(20,Math.min(1120,y));}graph.nodes.push(n);selected=n.id;render();if(n.type==='Scope'){$('scopeSelect').value=n.id;syncAxes();}msg('Added '+n.label+'. Select it to edit parameters.');}
const modelView={x:0,y:0,scale:1};
let viewAnimation=0,viewTarget=null,modelPan=null;
function paintModelView(){const v=modelView;$('workspace').style.transform=`translate(${v.x}px,${v.y}px) scale(${v.scale})`;$('zoom').value=Math.round(v.scale*100);}
function cancelViewAnimation(){cancelAnimationFrame(viewAnimation);viewAnimation=0;viewTarget=null;}
function animateView(target){cancelViewAnimation();viewTarget=target;let last=performance.now();function frame(now){const f=1-Math.exp(-Math.min(64,now-last)/45);last=now;for(const k of ['x','y','scale'])modelView[k]+=(target[k]-modelView[k])*f;paintModelView();if(Math.abs(modelView.x-target.x)+Math.abs(modelView.y-target.y)+Math.abs(modelView.scale-target.scale)*100<.05){Object.assign(modelView,target);paintModelView();viewAnimation=0;viewTarget=null;}else viewAnimation=requestAnimationFrame(frame);}viewAnimation=requestAnimationFrame(frame);}
function zoomModel(scale,px,py){const v=modelView,z=Math.max(.2,Math.min(2.5,scale));animateView({scale:z,x:px-(px-v.x)/v.scale*z,y:py-(py-v.y)/v.scale*z});}
function fitModel(){const ns=graph.nodes.length?graph.nodes:[{x:30,y:30}];const left=Math.min(...ns.map(n=>n.x))-35,top=Math.min(...ns.map(n=>n.y))-35,right=Math.max(...ns.map(n=>n.x+160))+35,bottom=Math.max(...ns.map(n=>n.y+110))+35;const vp=$('viewport'),z=Math.max(.2,Math.min(1.5,vp.clientWidth/(right-left),vp.clientHeight/(bottom-top)));animateView({scale:z,x:(vp.clientWidth-(right-left)*z)/2-left*z,y:(vp.clientHeight-(bottom-top)*z)/2-top*z});}
function locate(){const n=nextNode()||graph.nodes.find(n=>n.id===nextWire()?.target);if(n)animateView({scale:modelView.scale,x:$('viewport').clientWidth/2-(n.x+80)*modelView.scale,y:$('viewport').clientHeight/2-(n.y+50)*modelView.scale});}
$('viewport').addEventListener('wheel',e=>{e.preventDefault();const r=$('viewport').getBoundingClientRect(),delta=e.deltaY*(e.deltaMode===1?16:e.deltaMode===2?400:1);zoomModel((viewTarget?.scale||modelView.scale)*Math.exp(-delta*.0015),e.clientX-r.left,e.clientY-r.top);},{passive:false});
$('viewport').addEventListener('pointerdown',e=>{if(e.button!==1)return;e.preventDefault();e.stopPropagation();cancelViewAnimation();modelPan={id:e.pointerId,x:e.clientX,y:e.clientY,tx:modelView.x,ty:modelView.y};$('viewport').setPointerCapture(e.pointerId);$('viewport').style.cursor='grabbing';},true);
$('viewport').addEventListener('pointermove',e=>{if(!modelPan||e.pointerId!==modelPan.id)return;e.preventDefault();modelView.x=modelPan.tx+e.clientX-modelPan.x;modelView.y=modelPan.ty+e.clientY-modelPan.y;paintModelView();});
function endModelPan(e){if(!modelPan||e.pointerId!==modelPan.id)return;modelPan=null;$('viewport').style.cursor='';}
$('viewport').addEventListener('pointerup',endModelPan);$('viewport').addEventListener('pointercancel',endModelPan);$('viewport').addEventListener('lostpointercapture',endModelPan);$('viewport').addEventListener('auxclick',e=>{if(e.button===1)e.preventDefault();});

async function request(dt,steps=1){const version=epoch;const response=await fetch('/api/step',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({graph,state,dt,steps,auto_stop:true,settle_armed:settleArmed}),signal:AbortSignal.timeout(8000)});const result=await response.json();if(version!==epoch)return false;if(!response.ok)throw Error(result.error||'Simulation failed');state=result.state;values=result.values;if(dt>0){for(const sample of result.samples)history.push({t:time+sample.offset,v:sample.values});history=history.slice(-12000);}const last=result.samples.at(-1);time+=last?.offset||0;if(last)settleArmed=last.settle_armed;updateView();if(last?.settled){stop();msg("Automatically stopped: all body rates are below 1e-5 rad/s in magnitude.");}return true;}
async function check(){if(busy)return;busy=true;try{if(await request(0))msg('Valid executable graph. All inputs and signal shapes checked. '+(nextWire()||nextNode()?'Your graph differs from the lesson; it will run as wired.':'Ready to run.'));}catch(e){msg(e.message);}finally{busy=false;}}
async function tick(){const now=performance.now(),elapsed=Math.min(.25,(now-lastTick)/1000);lastTick=now;if(running&&!document.hidden)timeCredit=Math.min(2,timeCredit+elapsed*Number($('speed').value));else timeCredit=0;if(running&&!busy&&timeCredit>=.05){busy=true;const steps=Math.min(40,Math.floor((timeCredit+1e-9)/.05));timeCredit-=steps*.05;try{await request(.05,steps);}catch(e){stop();msg(e.message);}finally{busy=false;}}setTimeout(tick,16);}
$('speed').onchange=()=>{timeCredit=0;lastTick=performance.now();msg('Simulation speed: '+$('speed').value+'×. Physics step size and scope sampling stay unchanged.');};
document.addEventListener('visibilitychange',()=>{timeCredit=0;lastTick=performance.now();});

$('run').onclick=async()=>{if(running){stop();msg('Paused. The diagram and integrator states are retained.');return;}if(busy)return;busy=true;try{if(await request(0)){running=true;settleArmed=false;lastTick=performance.now();timeCredit=0;$('run').textContent='Pause';msg('Running your block diagram.');}}catch(e){msg(e.message);}finally{busy=false;}};
$('reset').onclick=()=>{invalidate();msg('Integrator states reset to their initial conditions.');};
$('spin').onclick=()=>{invalidate();const n=graph.nodes.find(n=>n.id==='rate'&&n.type==='Integrator');if(!n){msg('Add the lesson’s Body angular rate integrator first.');return;}if(Array.isArray(n.value)){let v=Array.from({length:3},()=>Math.random()*2-1),r=(3+Math.random()*5)*Math.PI/180;state.rate=v.map(x=>x/Math.hypot(...v)*r);}else state.rate=(Math.random()<.5?-1:1)*(3+Math.random()*5)*Math.PI/180;msg('New initial body spin of 3–8 deg/s; wheel momentum reset. Run to test recovery.');};
$('validate').onclick=check;$('locate').onclick=locate;
$('zoom').onchange=()=>{const z=Number($('zoom').value)/100;if(!Number.isFinite(z)||z<=0){paintModelView();return;}zoomModel(z,$('viewport').clientWidth/2,$('viewport').clientHeight/2);};
$('fit').onclick=fitModel;
$('apply').onclick=()=>{const n=graph.nodes.find(n=>n.id===selected);if(!n)return;try{const v=JSON.parse($('parameter').value);if(!(typeof v==='number'&&Number.isFinite(v)||Array.isArray(v)&&[3,4].includes(v.length)&&v.every(x=>typeof x==='number'&&Number.isFinite(x))))throw Error('Use a finite number or a 3/4-component numeric JSON array.');if(['Gain','Sum','Saturation'].includes(n.type)&&Array.isArray(v))throw Error('This block parameter must be scalar.');invalidate();n.value=v;render();msg('Value applied; states reset for a repeatable experiment.');}catch(e){msg(e.message);}};
$('remove').onclick=()=>{if(!selected)return;invalidate();graph.nodes=graph.nodes.filter(n=>n.id!==selected);graph.edges=graph.edges.filter(e=>e.source!==selected&&e.target!==selected);selected=null;pending=null;render();};
function chooseLesson(index){invalidate();lesson=index;graph={nodes:[],edges:[]};selected=null;pending=null;$('lesson').value=index;lessonUI();render();msg('Start by placing the highlighted block.');locate();}
const lessonTransitions=[
 'We return to the basic physical model: a known torque, inverse inertia, and two integrators. This isolates how torque produces rate and angle before feedback is introduced.',
 'We add a target angle, a subtraction block, and proportional gain Kp. Feeding the measured angle back lets the controller react to pointing error. Watch why restoring torque alone causes overshoot and oscillation.',
 'We retain the proportional loop and add rate feedback through Kd, then subtract that damping torque. The extra path brakes the satellite as it approaches the target, so the oscillation decays.',
 'We replace direct applied torque with an explicit reaction wheel. Sign gains create equal-and-opposite torques, saturation represents the motor limit, and a momentum integrator accounts for stored wheel momentum. Additional gains convert momentum to relative wheel RPM.',
 'We move from one rotation axis to three. Rate and wheel momentum become three-component vectors; an attitude quaternion replaces the single angle. Sun normalization, coordinate rotation, and a cross product create the pointing error. Quaternion differentiation and the gyroscopic cross term provide valid three-axis dynamics.'
];
let pendingLesson=null;
function previewLesson(index){
 if(index===lesson)return;
 stop();pendingLesson=index;$('lessonPreviewTitle').textContent=DATA.lessons[index].title;
 $('lessonPreviewWhy').textContent=lessonTransitions[index];
 const previous=DATA.graphs[lesson],next=DATA.graphs[index],container=$('lessonPreviewBlocks');container.replaceChildren();
 for(const n of next.nodes){const before=previous.nodes.find(p=>p.id===n.id);const changed=before&&(before.type!==n.type||before.unit!==n.unit||Array.isArray(before.value)!==Array.isArray(n.value));if(before&&!changed)continue;const item=document.createElement('p');item.className='small';const strong=document.createElement('strong');strong.textContent=(before?'Change: ':'Add: ')+n.type+' → '+n.label;item.append(strong,document.createElement('br'),document.createTextNode(n.why));container.append(item);}
 const removed=previous.nodes.filter(n=>!next.nodes.some(p=>p.id===n.id));if(removed.length){const p=document.createElement('p');p.className='small';p.textContent='Replaced or removed: '+removed.map(n=>n.label).join(', ')+'.';container.append(p);}
 if(!container.children.length){const p=document.createElement('p');p.textContent='Rebuild the same primitive structure and explore the lesson’s parameter choices.';container.append(p);}
 $('lessonPreviewExperiment').textContent='Try next: '+DATA.lessons[index].experiment;$('lessonDialog').showModal();
}
$('lesson').onchange=()=>{const target=Number($('lesson').value);$('lesson').value=lesson;previewLesson(target);};
$('cancelLesson').onclick=()=>$('lessonDialog').close();
$('lessonDialog').addEventListener('close',()=>{pendingLesson=null;});
$('beginLesson').onclick=()=>{if(pendingLesson===null)return;const target=pendingLesson;pendingLesson=null;$('lessonDialog').close();chooseLesson(target);};

$('example').onclick=()=>{if(graph.nodes.length&&!confirm('Replace this diagram with the worked example?'))return;invalidate();graph=clone(recipe());pending=null;selected=null;render();msg('Worked example loaded. Inspect each block, then run.');};
$('clear').onclick=()=>{if(graph.nodes.length&&!confirm('Clear this diagram?'))return;chooseLesson(lesson);};
$('save').onclick=()=>{const blob=new Blob([JSON.stringify({version:1,lesson,graph},null,2)],{type:'application/json'}),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download='cubesat-control-model.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);};
$('load').onclick=()=>$('file').click();$('file').onchange=async e=>{try{const f=e.target.files[0];if(!f)return;if(f.size>500000)throw Error('Model file is too large.');const m=JSON.parse(await f.text());if(m.version!==1||!Number.isInteger(m.lesson)||m.lesson<0||m.lesson>4||!Array.isArray(m.graph?.nodes)||!Array.isArray(m.graph?.edges)||m.graph.nodes.length>100)throw Error('Unsupported model file.');const ids=new Set;for(const n of m.graph.nodes){if(!Object.hasOwn(DATA.ports,n.type)||typeof n.id!=='string'||ids.has(n.id)||!Number.isFinite(n.x)||!Number.isFinite(n.y)||n.x<0||n.x>1540||n.y<0||n.y>1140)throw Error('Invalid block in model file.');if(typeof n.label!=='string'||!(typeof n.value==='number'&&Number.isFinite(n.value)||Array.isArray(n.value)&&[3,4].includes(n.value.length)&&n.value.every(x=>typeof x==='number'&&Number.isFinite(x))))throw Error('Invalid block label or parameter.');if(n.scopeAxes)validAxes(n.scopeAxes);ids.add(n.id);}for(const w of m.graph.edges)if(!ids.has(w.source)||!ids.has(w.target)||!Number.isInteger(w.port)||w.port<0||w.port>=DATA.ports[m.graph.nodes.find(n=>n.id===w.target).type])throw Error('Invalid wire.');invalidate();lesson=m.lesson;graph=m.graph;selected=null;pending=null;$('lesson').value=lesson;lessonUI();render();msg('Model loaded. Check wiring before running.');}catch(error){msg(error.message);}finally{e.target.value='';}};
document.onkeydown=e=>{if(e.key==='Escape'){pending=null;render();$('wireHint').textContent='Connection cancelled.';}};
$('workspace').ondragover=e=>e.preventDefault();$('workspace').ondrop=e=>{e.preventDefault();const type=e.dataTransfer.getData('text/plain');if(!Object.hasOwn(DATA.ports,type))return;const r=$('workspace').getBoundingClientRect();const zoom=modelView.scale;addBlock(type,(e.clientX-r.left)/zoom-80,(e.clientY-r.top)/zoom-25);};
for(const type of Object.keys(DATA.ports)){const b=document.createElement('button');b.textContent=symbols[type];b.draggable=true;b.dataset.type=type;b.ondragstart=e=>e.dataTransfer.setData('text/plain',type);b.onclick=()=>addBlock(type);$('library').append(b);}
DATA.lessons.forEach((l,i)=>{const o=document.createElement('option');o.value=i;o.textContent=l.title;$('lesson').append(o);});
DATA.sources.forEach(([title,url])=>{const p=document.createElement('p'),a=document.createElement('a');p.className='small';a.href=url;a.textContent=title;a.target='_blank';a.rel='noopener';p.append(a);$('sources').append(p);});
function canvas(id){const c=$(id),r=c.getBoundingClientRect(),d=devicePixelRatio||1;if(c.width!==Math.round(r.width*d)||c.height!==Math.round(r.height*d)){c.width=Math.round(r.width*d);c.height=Math.round(r.height*d);}const ctx=c.getContext('2d');ctx.setTransform(d,0,0,d,0,0);ctx.clearRect(0,0,r.width,r.height);return [ctx,r.width,r.height];}
function rot(q,v){let [w,x,y,z]=q,n=Math.hypot(...q)||1;w/=n;x/=n;y/=n;z/=n;return [(1-2*(y*y+z*z))*v[0]+2*(x*y-w*z)*v[1]+2*(x*z+w*y)*v[2],2*(x*y+w*z)*v[0]+(1-2*(x*x+z*z))*v[1]+2*(y*z-w*x)*v[2],2*(x*z-w*y)*v[0]+2*(y*z+w*x)*v[1]+(1-2*(x*x+y*y))*v[2]];}
const sceneCamera={az:.8,el:.5,distance:3.6,panX:0,panY:0};
let cameraDrag=null,cameraFrame=0;
function scheduleScene(){if(!cameraFrame)cameraFrame=requestAnimationFrame(()=>{cameraFrame=0;drawScene();});}
function resetSceneCamera(){Object.assign(sceneCamera,{az:.8,el:.5,distance:3.6,panX:0,panY:0});scheduleScene();}
$('resetCamera').onclick=resetSceneCamera;
$('frontCamera').onclick=()=>{Object.assign(sceneCamera,{az:0,el:Math.PI/2-.001,panX:0,panY:0});scheduleScene();};
$('sideCamera').onclick=()=>{Object.assign(sceneCamera,{az:0,el:0,panX:0,panY:0});scheduleScene();};
$('scene').onpointerdown=e=>{if(e.button!==0&&e.button!==1)return;e.preventDefault();cameraDrag={id:e.pointerId,x:e.clientX,y:e.clientY,pan:e.button===1};$('scene').setPointerCapture(e.pointerId);$('scene').style.cursor='grabbing';};
$('scene').onpointermove=e=>{if(!cameraDrag||cameraDrag.id!==e.pointerId)return;const dx=e.clientX-cameraDrag.x,dy=e.clientY-cameraDrag.y;cameraDrag.x=e.clientX;cameraDrag.y=e.clientY;if(cameraDrag.pan){sceneCamera.panX+=dx;sceneCamera.panY+=dy;}else{sceneCamera.az-=dx*.008;sceneCamera.el=Math.max(-Math.PI/2+.001,Math.min(Math.PI/2-.001,sceneCamera.el+dy*.008));}scheduleScene();};
function endCamera(e){if(cameraDrag?.id!==e.pointerId)return;cameraDrag=null;$('scene').style.cursor='grab';}
$('scene').onpointerup=endCamera;$('scene').onpointercancel=endCamera;$('scene').onlostpointercapture=endCamera;
$('scene').addEventListener('wheel',e=>{e.preventDefault();const delta=e.deltaY*(e.deltaMode===1?16:e.deltaMode===2?400:1);sceneCamera.distance=Math.max(2.2,Math.min(8,sceneCamera.distance*Math.exp(delta*.001)));scheduleScene();},{passive:false});
$('scene').addEventListener('auxclick',e=>{if(e.button===1)e.preventDefault();});
function drawScene(){
 const [c,w,h]=canvas('scene'),angle=typeof values.angle==='number'?values.angle:0,q=values.attitude||[Math.cos(angle/2),0,Math.sin(angle/2),0],sun=values.sun_unit||[Math.sin(values.target||0),0,Math.cos(values.target||0)];
 const cam=sceneCamera,eye=[Math.cos(cam.el)*Math.cos(cam.az),Math.cos(cam.el)*Math.sin(cam.az),Math.sin(cam.el)],right=[-Math.sin(cam.az),Math.cos(cam.az),0],up=[-Math.sin(cam.el)*Math.cos(cam.az),-Math.sin(cam.el)*Math.sin(cam.az),Math.cos(cam.el)];
 const dot=(a,b)=>a.reduce((s,x,i)=>s+x*b[i],0),focal=Math.min(w,h)*1.45;
 const project=v=>{const depth=cam.distance-dot(v,eye);return [w/2+cam.panX+dot(v,right)*focal/depth,h/2+cam.panY-dot(v,up)*focal/depth];};
 for(let i=0;i<90;i++){c.fillStyle='#9bd7ff35';c.fillRect((i*79.3)%w,(i*43.7)%h,1,1);}
 function polygon(points,fill,stroke){c.beginPath();points.forEach((p,i)=>i?c.lineTo(...project(p)):c.moveTo(...project(p)));c.closePath();c.fillStyle=fill;c.fill();if(stroke){c.strokeStyle=stroke;c.lineWidth=.8;c.stroke();}}
 function line(a,b,color,width=1){c.beginPath();c.moveTo(...project(a));c.lineTo(...project(b));c.strokeStyle=color;c.lineWidth=width;c.stroke();}
 const faces=[];
 for(let axis=0;axis<3;axis++)for(const sign of [-1,1]){const normal=[0,0,0];normal[axis]=sign;const nw=rot(q,normal),center=nw.map(x=>x*.6);if(dot(nw,eye)*cam.distance<=.6)continue;faces.push({axis,sign,nw,center});}
 faces.sort((a,b)=>dot(a.center,eye)-dot(b.center,eye));
 for(const f of faces){
  const uv=[0,1,2].filter(i=>i!==f.axis),light=Math.max(0,dot(f.nw,sun)),metal=Math.round(115+105*light);
  function point(u,v,offset=.6){const p=[0,0,0];p[f.axis]=f.sign*offset;p[uv[0]]=u;p[uv[1]]=v;return rot(q,p);}
  function plate(x0,y0,x1,y1,fill,stroke,depth=.6){polygon([point(x0,y0,depth),point(x1,y0,depth),point(x1,y1,depth),point(x0,y1,depth)],fill,stroke);}
  plate(-.6,-.6,.6,.6,'#182733','#8198a7');
  plate(-.515,-.515,.515,.515,'#06111f','#657586');
  for(let col=0;col<2;col++)for(let row=0;row<4;row++){
   const x=-.465+col*.495,y=-.46+row*.24,x1=x+.435,y1=y+.20,cut=.03;
   polygon([point(x+cut,y),point(x1-cut,y),point(x1,y+cut),point(x1,y1-cut),point(x1-cut,y1),point(x+cut,y1),point(x,y1-cut),point(x,y+cut)],`rgb(${15+Math.round(light*12)},${27+Math.round(light*18)},${53+Math.round(light*36)})`,'#6582a1');
   for(let j=1;j<9;j++)line(point(x+j*.435/9,y+.025),point(x+j*.435/9,y1-.025),'#819db74d',.5);
   for(const t of [.3,.7])line(point(x+.018,y+.20*t),point(x1-.018,y+.20*t),'#a4c3d480',.8);
  }
  const alloy=`rgb(${metal-12},${metal+4},${Math.min(255,metal+15)})`;
  for(const [x0,y0,x1,y1] of [[-.6,-.6,-.515,.6],[.515,-.6,.6,.6],[-.515,-.6,.515,-.515],[-.515,.515,.515,.6]])plate(x0,y0,x1,y1,alloy,'#c7e3ef');
  for(const t of [-.505,.505]){line(point(t,-.505),point(t,.505),'#06101b',1);line(point(-.505,t),point(.505,t),'#06101b',1);}
  for(const x of [-.557,.557])for(const y of [-.557,.557]){const ring=Array.from({length:12},(_,j)=>point(x+.021*Math.cos(j*Math.PI/6),y+.021*Math.sin(j*Math.PI/6)));polygon(ring,'#1b2a33','#def0f8');line(point(x-.01,y),point(x+.01,y),'#a2c9de',.7);}
  // Centered coarse Sun sensor with PCB, pins, package and optical aperture.
  plate(-.108,-.108,.108,.108,'#245547','#a0b8ab',.603);
  for(const x of [-.097,.075])for(const y of [-.06,0,.06])plate(x,y-.012,x+.024,y+.012,'#bbdbe8',null,.605);
  plate(-.066,-.066,.066,.066,'#a8c8d8','#e0f4ff',.608);
  plate(-.045,-.045,.045,.045,light>.1?'#375e76':'#061420','#172532',.61);
  line(point(-.035,-.03,.612),point(.033,-.03,.612),'#8dcfed',1);
  const origin=project(point(-.39,.555)),u=project(point(-.17,.555)),v=project(point(-.39,.52));
  c.save();c.transform((u[0]-origin[0])/44,(u[1]-origin[1])/44,(v[0]-origin[0])/8,(v[1]-origin[1])/8,...origin);c.fillStyle='#142c3c';c.font='bold 8px monospace';c.fillText('1U '+(f.sign>0?'+':'−')+'XYZ'[f.axis],0,0);c.restore();
 }
 // Direction arrows are overlays so they remain readable through the model.
 function arrow(v,color,text){const a=project([0,0,0]),b=project(v),theta=Math.atan2(b[1]-a[1],b[0]-a[0]);c.strokeStyle=color;c.lineWidth=2;c.beginPath();c.moveTo(...a);c.lineTo(...b);c.stroke();c.fillStyle=color;c.beginPath();c.moveTo(...b);c.lineTo(b[0]-8*Math.cos(theta-.4),b[1]-8*Math.sin(theta-.4));c.lineTo(b[0]-8*Math.cos(theta+.4),b[1]-8*Math.sin(theta+.4));c.closePath();c.fill();c.font='12px monospace';c.fillText(text,b[0]+6,b[1]-7);}
 arrow(rot(q,[0,0,1.02]),'#8edbff','+Z');arrow(sun.map(x=>x*1.2),'#ffe29a','Sun');
 c.font='10px monospace';c.fillStyle='#a5c1d1';c.fillText('Perspective · 1U / 10 cm',12,h-12);
}

function updateView(){const rate=values.rate,r=Array.isArray(rate)?Math.hypot(...rate):Math.abs(rate||0);let error;if(Array.isArray(values.sun_body))error=Math.acos(Math.max(-1,Math.min(1,values.sun_body[2])));else if(typeof values.angle==='number')error=Math.acos(Math.cos(values.angle-(values.target||0)));$('angleRead').textContent=error===undefined?'—':(error*180/Math.PI).toFixed(2)+'°';$('rateRead').textContent=rate===undefined?'—':(r*180/Math.PI).toFixed(2)+'°/s';let rpm=values.rpm;if(rpm===undefined&&Array.isArray(values.momentum)&&Array.isArray(rate))rpm=values.momentum.map((x,i)=>(x/1e-5-rate[i])*60/(2*Math.PI));$('rpmRead').textContent=rpm===undefined?'—':Array.isArray(rpm)?Math.max(...rpm.map(Math.abs)).toFixed(1)+' max':rpm.toFixed(1);$('timeRead').textContent=time.toFixed(2)+' s';drawScene();drawPlot();}
function bodyRateDisplay(id,value){
 let node=graph.nodes.find(n=>n.id===id);const visited=new Set();
 while(node?.type==='Scope'&&!visited.has(node.id)){visited.add(node.id);const source=graph.edges.find(e=>e.target===node.id&&e.port===0)?.source;node=graph.nodes.find(n=>n.id===source);}
 if(node?.id==='rate'){
  const components=Array.isArray(value)?value:[value];
  if(components.length&&components.every(x=>typeof x==='number'&&Math.abs(x)<1e-5))return Array.isArray(value)?'['+components.map(()=>0).join(', ')+']':'0';
 }
 return fmt(value);
}
function drawPlot(){
 const [c,w,h]=canvas('plot'),id=$('scopeSelect').value,n=graph.nodes.find(n=>n.id===id),a=axesFor(n),colors=['#8edbff','#9af2c5','#b7b0ff','#ffffff'];
 const left=60,top=15,pw=Math.max(1,w-72),ph=h-45,span=a.yMax-a.yMin;
 c.strokeStyle='#35516a';c.strokeRect(left,top,pw,ph);c.font='10px monospace';c.fillStyle='#a7c7da';
 c.fillText(a.yMax.toPrecision(3),0,top+5);c.fillText(a.yMin.toPrecision(3),0,top+ph);c.fillText(a.xMin+' s',left,h-5);c.fillText(a.xMax+' s',w-52,h-5);
 if(a.yMin<0&&a.yMax>0){const zy=top+a.yMax/span*ph;c.beginPath();c.moveTo(left,zy);c.lineTo(left+pw,zy);c.stroke();}
 const rows=history.filter(r=>r.v[id]!==undefined);
 if(!rows.length){$('scopeValue').textContent='No signal history yet';c.fillText('Run to collect signal history',left+5,45);return;}
 c.save();c.beginPath();c.rect(left,top,pw,ph);c.clip();
 const count=Array.isArray(rows[0].v[id])?rows[0].v[id].length:1;
 for(let k=0;k<count;k++){c.strokeStyle=colors[k];c.beginPath();rows.forEach((r,i)=>{const v=Array.isArray(r.v[id])?r.v[id][k]:r.v[id],x=left+(r.t-a.xMin)/(a.xMax-a.xMin)*pw,y=top+(a.yMax-v)/span*ph;i?c.lineTo(x,y):c.moveTo(x,y);});c.stroke();}
 c.restore();$('scopeValue').textContent=label(id)+' = '+bodyRateDisplay(id,values[id])+' '+(n?.unit||'');
}
$('scopeSelect').onchange=()=>{syncAxes();drawPlot();};window.addEventListener('resize',updateView);chooseLesson(0);tick();
</script></body></html>'''


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def send(self, status, body, content_type='application/json'):
        data = body.encode('utf-8') if isinstance(body, str) else json.dumps(body, allow_nan=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', content_type+'; charset=utf-8')
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path not in ('/', '/index.html'):
            self.send(404, {'error': 'Not found'})
            return
        data = dict(lessons=LESSONS, graphs=[lesson_graph(i) for i in range(5)], ports=PORTS, sources=SOURCES)
        self.send(200, HTML.replace('__DATA__', json.dumps(data)), 'text/html')

    def do_POST(self):
        if self.path != '/api/step':
            self.send(404, {'error': 'Not found'})
            return
        # Only same-origin browser requests; no cross-origin application access.
        origin = self.headers.get('Origin')
        if origin and origin != 'http://'+self.headers.get('Host', ''):
            self.send(403, {'error': 'Cross-origin request rejected.'})
            return
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if not 0 < length <= 500000:
                raise ValueError('Invalid request size.')
            args = json.loads(self.rfile.read(length))
            if not isinstance(args, dict) or not {'graph', 'state', 'dt'} <= set(args) or set(args) - {'graph', 'state', 'dt', 'steps', 'auto_stop', 'settle_armed'}:
                raise ValueError('Request needs graph, state and dt.')
            state, values, samples = simulate_batch(args['graph'], args['state'], args['dt'], args.get('steps', 1), args.get('auto_stop', False), args.get('settle_armed', False))
            self.send(200, dict(state=state, values=values, samples=samples))
        except (ValueError, TypeError, KeyError, OverflowError, RecursionError) as exc:
            self.send(400, {'error': str(exc)})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8004)
    parser.add_argument('--no-browser', action='store_true')
    args = parser.parse_args()
    try:
        server = ThreadingHTTPServer(('127.0.0.1', args.port), Handler)
    except OSError as exc:
        parser.exit(1, f'{exc}\nTry --port 8080.\n')
    url = f'http://127.0.0.1:{server.server_port}'
    print(f'CubeSat Control Lab: {url}\nCtrl+C to stop.', flush=True)
    if not args.no_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
