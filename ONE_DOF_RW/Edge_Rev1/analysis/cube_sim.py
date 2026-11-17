"""One-axis cube (like the photo): a cube frame standing on one edge, one 2804 motor + wheel inside with its axis parallel to that edge.
theta = lean from the balance point (the cube's diagonal vertical). CoM sits at l = a/sqrt(2) above the pivot edge.
Same model as plate_check.py: J1 th'' = Mgl sin(th) - tau ; w' = tau/Jw - th'' ; closed-form pole placement; torque limit + back-EMF derating.
"""
import math

G = 9.81
W_NL = 272.0
RHO = 1.24e-3 * 0.8                      # g/mm^3, PLA at ~80 % of solid


def cube(a=100.0, strut=5.0, wheel_d=None, bolts=None, battery_g=38.0, elec_g=25.0, motor_g=45.0):
    """a = cube side (mm). Wheel: printed rim+spokes+hub scales from the rev3 D100 wheel (26 g, J 4.45e-5), plus M4x12 bolts (2.3 g) on the rim."""
    d = wheel_d if wheel_d is not None else a - 16.0
    nb = bolts if bolts is not None else max(0, round(10 * d / 100.0))
    m_frame = 12 * a * strut ** 2 * RHO * 1e-3                      # kg
    m_ring = 0.026 * (d / 100.0) ** 2
    jw_ring = 4.45e-5 * (d / 100.0) ** 4
    r_p = (d / 2 - 5.75) * 1e-3
    m_bolts = nb * 2.3e-3
    jw = jw_ring + m_bolts * r_p ** 2 + 4.6e-6                        # spin inertia: ring + bolts + rotor bell
    m_wheel = m_ring + m_bolts
    m_other = motor_g * 1e-3 + (battery_g + elec_g) * 1e-3
    M = m_frame + m_wheel + m_other
    l = a / math.sqrt(2) * 1e-3
    j_frame = 0.389 * m_frame * (a * 1e-3) ** 2 + m_frame * l ** 2     # about the pivot edge
    j1 = j_frame + m_wheel * l ** 2 + m_other * l ** 2 + 2.5e-5        # excludes the wheel's own spin inertia
    return dict(a=a, d=d, nb=nb, M=M, l=l, Mgl=M * G * l, J1=j1, Jw=jw, m_frame=m_frame, m_wheel=m_wheel)


def gains(p, speed=1.0):
    a = p['Mgl'] / p['J1']
    b = 1 / p['J1']
    c = 1 / p['Jw'] + 1 / p['J1']
    s = math.sqrt(a)
    p1, p2, p3 = 1.5 * s * speed, 1.9 * s * speed, 0.6 * s * speed
    e1, e2, e3 = p1 + p2 + p3, p1 * p2 + p1 * p3 + p2 * p3, p1 * p2 * p3
    k3 = e3 * p['Jw'] / a
    k1 = (e2 + a) / b
    k2 = (e1 + c * k3) / b
    return k1, k2, k3


def run(p, th0, tau_max, speed=1.0, T=4.0, dt=0.001, w0=0.0):
    k1, k2, k3 = gains(p, speed)
    th, thd, w = th0, 0.0, w0
    wpk = 0.0
    t = 0.0
    while t < T:
        u = k1 * th + k2 * thd + k3 * w
        tau = max(-tau_max, min(tau_max, u))
        if tau * w > 0:
            tau *= max(0.0, 1 - abs(w) / W_NL)

        def f(x):
            th_, thd_, w_ = x
            add = (p['Mgl'] * math.sin(th_) - tau) / p['J1']
            return (thd_, add, tau / p['Jw'] - add)
        x = (th, thd, w)
        a1 = f(x); a2 = f([x[i] + 0.5 * dt * a1[i] for i in range(3)])
        a3 = f([x[i] + 0.5 * dt * a2[i] for i in range(3)]); a4 = f([x[i] + dt * a3[i] for i in range(3)])
        th, thd, w = [x[i] + dt / 6 * (a1[i] + 2 * a2[i] + 2 * a3[i] + a4[i]) for i in range(3)]
        wpk = max(wpk, abs(w))
        t += dt
        if abs(th) > 0.6:
            return False, wpk
    return (abs(th) < 0.02 and abs(thd) < 0.2), wpk


def max_lean(p, tau_max, speed=1.0):
    if not run(p, 0.002, tau_max, speed)[0]:
        return 0.0, 0.0
    lo, hi = 0.0, 0.6
    for _ in range(14):
        mid = (lo + hi) / 2
        if run(p, mid, tau_max, speed)[0]:
            lo = mid
        else:
            hi = mid
    return math.degrees(lo), run(p, lo, tau_max, speed)[1]


if __name__ == '__main__':
    print(f"{'cube a':>7} {'wheel D':>7} {'bolts':>5} {'M g':>5} {'l mm':>5} {'Mgl':>6} {'tau/Mgl':>7} {'Jw':>8} {'pole 1/s':>8} | max lean deg @0.03   wheel peak rad/s   | @0.045")
    for a in (70, 80, 90, 100, 120, 150):
        p = cube(a)
        r, wp = max_lean(p, 0.030)
        r2, _ = max_lean(p, 0.045)
        print(f"{a:5d}mm {p['d']:5.0f}mm {p['nb']:5d} {p['M']*1e3:5.0f} {p['l']*1e3:5.0f} {p['Mgl']:6.3f} {0.03/p['Mgl']:7.2f} {p['Jw']:8.1e} {math.sqrt(p['Mgl']/p['J1']):8.1f} | {r:8.1f}             {wp:8.0f}          | {r2:5.1f}")
    print('\nlighter build at a = 90: battery 25 g, electronics 20 g')
    p = cube(90, battery_g=25.0, elec_g=20.0)
    print(f"  M {p['M']*1e3:.0f} g, Mgl {p['Mgl']:.3f}, tau/Mgl {0.03/p['Mgl']:.2f}, max lean {max_lean(p, 0.03)[0]:.1f} deg")
    print('\nrule of thumb used in the page: the angle the motor can hold statically is asin(tau/Mgl) =', [round(math.degrees(math.asin(min(1, 0.03 / cube(a)['Mgl']))), 1) for a in (70, 80, 90, 100, 120, 150)])
