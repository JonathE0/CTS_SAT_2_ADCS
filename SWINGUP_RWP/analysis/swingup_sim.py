"""Sizing study 2: swing-up by energy pumping + LQR catch, with the 2804 motor's torque limit and back-EMF derating.

a  = arm angle from UP (a = 0 upright, a = pi hanging)      w = wheel speed relative to the arm
J1 * a'' = M g l sin(a) - tau                               (J1 = Jt - Jw, wheel spin inertia excluded)
w'       = tau/Jw - a''                                      tau = torque the motor applies TO THE WHEEL
Motor: |tau| <= TAU_MAX, derated linearly with |w|/W_NL when it would speed the wheel further up.
"""
import math, sys, itertools
import numpy as np
from scipy.linalg import solve_continuous_are

G = 9.81
DT = 0.001


def lqr(M, l, J1, Jw, q, r):
    k = M * G * l / J1
    A = np.array([[0, 1, 0], [k, 0, 0], [-k, 0, 0]], float)
    B = np.array([[0], [-1 / J1], [1 / Jw + 1 / J1]], float)
    P = solve_continuous_are(A, B, np.diag(q), np.array([[r]]))
    return (B.T @ P / r).ravel()          # u = -K x


def simulate(M, l, Jt, Jw, tau_max, w_nl, k_pump=40.0, tmax=25.0, a0=math.pi - 0.05,
             catch_deg=18.0, q=(300.0, 3.0, 0.05), r=300.0, e_target=1.0, pert=None):
    J1 = Jt - Jw
    Mgl = M * G * l
    K = lqr(M, l, J1, Jw, q, r)

    def motor(u, w):
        t = max(-tau_max, min(tau_max, u))
        lim = max(0.0, 1.0 - abs(w) / w_nl)
        if t * w > 0:
            t *= lim
        return t

    def deriv(x, tau):
        a, ad, w = x
        add = (Mgl * math.sin(a) - tau) / J1
        return (ad, add, tau / Jw - add)

    x = [a0, 0.0, 0.0]
    mode = "pump"
    t = 0.0
    t_catch = None
    wpk = 0.0
    held = 0.0
    while t < tmax:
        a, ad, w = x
        aw = (a + math.pi) % (2 * math.pi) - math.pi            # wrap to (-pi, pi], 0 = up
        if mode == "pump":
            E = 0.5 * J1 * ad * ad + Mgl * (math.cos(a) - 1.0)    # 0 = upright at rest, -2Mgl = hanging at rest
            sgn = 1.0 if ad >= 0 else -1.0
            u = k_pump * (E - (e_target - 1.0) * 0.0) * sgn
            # also let the wheel recover toward zero speed once energy is nearly there (helps the catch)
            if abs(aw) < math.radians(45):
                u += -0.01 * w
            if abs(aw) < math.radians(catch_deg) and abs(ad) < 6.0:
                mode = "lqr"
                t_catch = t
        else:
            xs = np.array([aw, ad, w])
            u = float(-K @ xs)
            if abs(aw) > math.radians(60):                        # lost it: back to pumping
                mode = "pump"
                t_catch = None
        tau = motor(u, w)
        # RK4 with zero-order-hold torque
        k1 = deriv(x, tau)
        k2 = deriv([x[i] + 0.5 * DT * k1[i] for i in range(3)], tau)
        k3 = deriv([x[i] + 0.5 * DT * k2[i] for i in range(3)], tau)
        k4 = deriv([x[i] + DT * k3[i] for i in range(3)], tau)
        x = [x[i] + DT / 6 * (k1[i] + 2 * k2[i] + 2 * k3[i] + k4[i]) for i in range(3)]
        t += DT
        wpk = max(wpk, abs(x[2]))
        aw2 = (x[0] + math.pi) % (2 * math.pi) - math.pi
        if mode == "lqr" and abs(aw2) < math.radians(2) and abs(x[1]) < 0.3:
            held += DT
            if held > 2.0:
                return dict(ok=True, t_catch=t_catch, t_done=t, wpk=wpk)
        else:
            held = 0.0 if mode == "pump" else held
    return dict(ok=False, t_catch=t_catch, t_done=t, wpk=wpk)


def candidate(L, mw, Dw, ring_f=1.6, mm=0.065, ma=0.020):
    M = mm + mw + ma
    l = (mm * L + mw * L + ma * L / 2) / M
    Jw = 0.5 * mw * (Dw / 2) ** 2 * ring_f
    Jt = mm * L ** 2 + ma * L ** 2 / 3 + mw * L ** 2 + Jw
    return M, l, Jt, Jw


if __name__ == "__main__":
    tau_max = float(sys.argv[1]) if len(sys.argv) > 1 else 0.030
    print(f"tau_max = {tau_max} N m   (W_NL 272 rad/s at 12 V)")
    print(f"{'L(mm)':>6} {'mw(g)':>6} {'Dw':>4} {'M(g)':>5} {'Mgl':>6} {'Jw':>8} {'tau/Mgl':>7} | {'caught':>6} {'t_catch':>7} {'w_peak':>7}")
    for L in (0.08, 0.10, 0.12):
        for mw, Dw in ((0.030, 0.100), (0.045, 0.100), (0.060, 0.100), (0.030, 0.080), (0.050, 0.080)):
            M, l, Jt, Jw = candidate(L, mw, Dw)
            r = simulate(M, l, Jt, Jw, tau_max, 272.0)
            tc = "--" if r["t_catch"] is None else f"{r['t_catch']:.1f}s"
            print(f"{L*1000:6.0f} {mw*1000:6.0f} {Dw*1000:4.0f} {M*1000:5.0f} {M*G*l:6.3f} {Jw:8.1e} {tau_max/(M*G*l):7.2f} | {str(r['ok']):>6} {tc:>7} {r['wpk']:7.0f}")
