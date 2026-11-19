# External electronics enclosure — modular assembly

The existing viewer now shows four production prints: common base, independent
ESP32 mount, independent driver mount and carrier retaining frame. It is a
preliminary CAD assembly review, not physically validated hardware.

From the **repository root** of your checkout:

```sh
python3 -m http.server 8765 --bind 127.0.0.1 --directory .
```

Open exactly:

<http://127.0.0.1:8765/CTS_Simple_Visulizers/External%20Electronics%20Enclosure/index.html>

The bare `/` URL deliberately redirects to SAT-1 Commissioning and is unchanged.
Hard refresh **Cmd+Shift+R** after updates. If8765 is occupied, inspect the
listener with `lsof -nP -iTCP:8765 -sTCP:LISTEN`, its command with
`ps -p <PID> -o pid=,command=` and working directory with
`lsof -a -p <PID> -d cwd`. Stop only a confirmed stale preview server, preferably
Control-C in its terminal; restart with the explicit repository root.

Nine stages show kit, base/feet, side-entry frame nuts/carrier, retaining frame,
ESP32 seating, driver preassembly, insertion of complete mounts, module-to-base
fastening and complete assembly. Two base screws release either complete module;
its PCB/frame fasteners remain fitted. Retainer nuts are beneath real solid roofs.
Frame hard stops leave deliberate carrier capture play, not PCB compression.

Use Play/Pause, Previous/Next, kit/exploded/complete, scrubber, camera presets,
drag/orbit, scroll/zoom, labels, part quantities and visibility. Section/outlines
are retained. No electrical wiring or motor/control simulation is introduced.

The primary page loads local Three.js, `assembly-viewer.js` and one fetched
`scene.json`. CSS is inline. `viewer.js`, `viewer.css` and OrbitControls still
support the preserved local ADCS Testbench; they are not housing dependencies.
Do not remove them as part of this contribution.

For optional one-file offline sharing, after installing the housing requirements,
from the repository root run:

```sh
python ONE_DOF_RW/Edge_Rev1/external_electronics/analysis/build_enclosure_viewer.py --standalone ../cts-enclosure.html
```

Use a Python environment with its `requirements.txt`. The generated distribution
contains geometry, runtime, CSS, Three.js and license; no scene fetch. Open the
file directly. It is a generated sharing artifact, not an additional editable
source or proposed committed duplicate. Manufacturing instructions remain in
[PARTS.md](../../ONE_DOF_RW/Edge_Rev1/external_electronics/PARTS.md).

Use the [housing README](../../ONE_DOF_RW/Edge_Rev1/external_electronics/README.md)
for independent CAD generation, fit-coupon exports, mechanical/retention/browser
checks, configurable hardware assumptions and exact proposed commit scope.
The legacy combined builder is disabled to prevent overwriting this viewer.

**Fit coupons first.** Board identity, pins/sockets, connector dimensions, nut-roof
bridge quality, actual thread engagement, retention strength and temperature
performance require physical measurement/testing. No print-ready fit claim.
