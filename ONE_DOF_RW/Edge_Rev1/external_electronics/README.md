# Modular external electronics housing

**Preliminary CAD contribution — physical fitting still required.** The enclosure
remains stationary outside the Edge Rev1 balancing cube. Its open-top outside
size is125 ×90 ×35 mm. No wiring or motor-control firmware is implemented here.

![Current assembled housing](../../../CTS_Simple_Visulizers/External%20Electronics%20Enclosure/preview/assembled.png)

## Architecture decision

| Criterion | A: correct the integrated mounting | C: replaceable mounts — selected |
|---|---|---|
| Production prints | 2 | 4: tray, ESP mount, driver mount, retaining frame |
| Screws / nuts / washers | 6 /6 /0 nominal | 10 /10 /0 nominal |
| Board-footprint correction | Reprint large tray | Reprint only the affected mount within fixed bay capacity |
| Electronics preassembly | On the case or case-integrated supports | Independently off the case, with underside access |
| Module replacement | No separate electronics module | Two accessible base screws release either complete module |
| Printing | Fewer parts; case carries board-specific features | More small parts, economical fitting; only ESP nut roofs have short bridges |
| Cable/USB access | Existing directions | Same directions; USB saddle moves with ESP module |

C is selected because both PCB interfaces are still provisional and the user
prioritizes replacement, fit testing and low reprint cost. The extra four screws
provide independent module fastening instead of coupling electronics retention to
case removal. No snap tabs, tiny printed threads or elaborate rail mechanisms.

The prior open-top ESP nut pockets did **not** anchor the frame. Current side-entry
pockets have solid roofs; independent screws attach frame to ESP mount. Frame
preload closes on printed hard-stop columns, leaving0.4 mm deliberate carrier
capture play. The carrier is restrained without intentionally squeezing its PCB.
The four M2 driver fasteners remain because reference mounting holes give defined
contact locations, unlike an unmeasured retaining bracket.

| Before this revision | Current design |
|---|---|
| 2 prints,6 screws,6 nuts | **4 prints,10 screws,10 nuts** |
| ESP frame not positively anchored | Real side-loaded nut roofs; withdrawal regression checks |
| No controlled carrier contact allowance | Defined hard stops and capture gap with a provisional Z tolerance budget |
| About0.215 mm tail/post gap under carrier movement | **1.872 mm sampled minimum**,1.172 after provisional print/solder allowances |
| Integrated board-specific supports | Separate mounts; base invariance checked under board-specific parameter changes |
| Four additional insulating M2 ×20 screws | **Four insulating M2 ×12 screws** |
| Seven viewer stages | **Nine physical assembly stages** |
| Legacy renderer import / overwrite-capable combined builder | Independent renderer / disabled historical builder |

[Complete BOM, manufacturing and fit-test checklist](PARTS.md).

## Final fastening decision — 2026-11-19

**Retain Option 1: the current commercial fasteners and existing printed supports.**
The assembly remains four production prints, six kit-listed M2.5 ×10 screws/nuts
and four additional commercial insulating M2 ×12 screws/nuts. No new bracket,
locking pin, clip, slide or printed screw is selected or exported. Existing CAD,
STLs, assembly stages and positive ESP frame anchorage are preserved.

The four M2 driver screws are additional stock, but replacing them now would add
unqualified PCB contact, connector-routing and printed-mechanism interfaces.
Current M2 bearing areas and shaft fit also require actual-board verification;
the decision is to test a defined fastening arrangement, not to claim it is
physically qualified. No actual PCB holes will be enlarged.

The comparison below uses **illustrative complete-assembly counts** for the
unimplemented options. Only Option 1 is dimensioned and computationally checked.
Counts for alternative clips/latches would change with their eventual design.

| Option | Production printed pieces | Purchased screws / nuts, entire housing | Practical assessment |
|---|---:|---|---|
| **1. Current commercial fastening — selected** | **4** | **6 M2.5 +4 insulating M2 / same nut counts** | Positive through-fastening at four reference PCB holes; independent module removal; obtain eight additional M2 hardware pieces and fit-test them |
| 2. Printed insulating bracket, two M2.5 screws | 5 | 8 M2.5 /8 M2.5; no M2 | Best fallback after actual board measurement; fewer commercial pieces but extra contact pads, hard stops, anchors and connector-clearance qualification |
| 3. Bracket, two headed smooth pins and two locking clips | 9 | 6 M2.5 /6 M2.5; no M2 | Example adds five printed pieces; clips themselves need positive capture, good access and repeated-service qualification; greater small-part handling/fracture risk |
| 4. Integral snap rails or a removable sliding cover | 4–5 | 6 M2.5 /6 M2.5; no M2 | Fast only after tuning; requires clear PCB edges, insertion travel, release access and a positive end lock; tolerance, creep and catch-wear risks |

No washers are assumed in these conceptual counts; actual contact/bearing checks
could require them and a revised stack. A bracket's screw length is **not chosen**
without a modeled stack; do not assume the current10 mm length would apply.

### Engineering comparison

| Criterion | Current fastening | Bracket + M2.5 | Bracket + pins/clips | Sliding/snap retention |
|---|---|---|---|---|
| Positive retention | Heads, shafts and nuts close known loops | Bolts anchor bracket, but PCB capture must be designed | Pin heads plus independently locked clips required; friction wedge is insufficient | Rails alone insufficient; end stop and releasable positive lock required |
| PCB/electrical contact | Four reference-hole bearing regions still must be inspected | Additional verified bare pads/edge regions and hard stops needed | Same bracket contact uncertainties | Continuous slide path/edge contact needs inspection |
| Board bending | Four supported holes; do not force non-flat parts together | Gap/stops must limit loads; no pressing on ICs, capacitor or terminals | Pins must not drive bracket into PCB | Insertion/release forces must not flex PCB |
| Printing/tolerance | Existing geometry and four coupons; two ESP roof bridges | Added bracket bridges/pad-height accuracy | Pin/clip fits and orientation sensitive; more loose small parts | Rail fit, hook undercut and release strain sensitive |
| Assembly effort | Four driver screws/nuts, accessible off case | Potentially two same-tool screws, after fitting | More printed retainers to manipulate and keep track of | Low only after successful tuning; connectors may obstruct sliding |
| Disassembly | Remove driver nuts off case; no disposable catches | Two screws and lift-off bracket | Access/release each clip without prying on PCB | Need deliberate accessible release and clear travel |
| Repeated use | Commercial threads; printed supports/roofs still need creep/damage checks | Commercial threads, printed bracket flex/creep to qualify | Clip fracture, pin wear or hole ovalization to qualify | Catch wear, stress relaxation and fatigue to qualify |
| Thermal/connector access | Four small heads; existing service envelopes | Open bridge may work, but contact/air/connector clearance unverified | Same bracket limits plus pin/clip space | Rails must avoid hot components, copper and connectors |
| PCB tolerance changes | Change small driver module and repeat coupon | Contact pads/stop heights also change | Bracket plus locking fit can change | Edge thickness/shape strongly affects fitting |
| Replacing complete driver module | Two base screws; PCB remains retained | Preserve independent bracket fastening to module | Preserve independent pin locks | Preserve independent latch while module is removed |

An illustrative geometric probe placed two Ø8 printed anchor bosses at driver
center X and Y±20, spanning z7–17.6. It intersects the current front control-plug
and rear phase-plug allowance volumes by approximately99 and121 mm³ respectively.
These are **hypothetical anchor locations**, not actual PCB holes or a completed
bracket design. The result rejects that simple placement only; it does not prove
all brackets impossible. The service envelopes themselves remain unmeasured.
The rectangular PCB proxy does not establish the delivered board's shaped edges,
copper, component-free areas, temperatures or safe bracket bearing regions.

Smooth pins could be useful through **printed bracket features** if larger heads
and positively retained cross-locks prevent withdrawal. A friction/taper fit, loose
wedge or clip whose own escape is uncontrolled is not sufficient. Printed pins
through the nominal Ø2 PCB holes would retain the small-feature/fit problem;
they are not adopted. Split pins or small spring clips add unqualified strain and
repeated-use behavior. No new mechanism is justified for the ESP carrier either:
keep its properly roofed nuts and independent frame screws.

Larger printed thumb screws can attach to a printed bracket, never an incompatible
PCB hole. They would need bulkier bosses, real thread-wear/strength tests and the
same PCB-contact qualification. They offer no demonstrated benefit over the kit
M2.5 screws here. Tiny FDM M2/M2.5 threads are not adopted.

Primary manufacturing guidance supports treating FDM snap fit tolerance, load
orientation and repeated-use behavior as process-dependent, and favors larger
printed threads over tiny ones: [snap-fit guidance](https://formlabs.com/blog/designing-3d-printed-snap-fit-enclosures/),
[printed-thread guidance](https://formlabs.com/blog/adding-screw-threads-3d-printed-parts/),
[FDM feature/tolerance guidance](https://help.prusa3d.com/article/modeling-with-3d-printing-in-mind_164135).
These sources do not qualify this enclosure or identify the purchased board.

**Proceed to fit testing, not another speculative redesign.** If the actual M2
shaft or bearing checks fail, stop that assembly and record the dimensions; the
replaceable driver mount confines a measured correction to the small module.
A two-M2.5 bracket is the first alternative to revisit only if measurements show
a clear advantage. Do not buy or print the rejected concept mechanisms now.
See [PARTS.md](PARTS.md) for the complete unchanged inventory and coupon pass/fail
procedure. No staging, commit or push is performed by this investigation.

## Common mounting interface and load paths

Both bays use two diagonal M2.5 through holes on a **24 ×52 mm** pitch, a
**z5 seating plane**, four bearing pads and two locating pins. One round hole and
one elongated locating hole allow assembly without two tightly constrained round
pins. ESP nominal plate envelope is72 ×60; driver35 ×60. They share the fastening
datum but different usable bay outlines; arbitrary board sizes are not guaranteed.

The base contains no PCB hole pattern, carrier landing pattern or USB-height
support. Those are on removable mounts. Generic30 ×30 floor service/vent windows
clear driver underside hardware and admit air/tool access. Base invariant checks
cover changed driver hole pitch/outline, carrier supports, carrier thickness and
socket origin/height. Changes beyond bay or cable-corridor capacity may still
require reconsidering the base.

- **Mount to case:** two M2.5 ×10 through-bolts per mount, ordinary nuts below
  floor. The nut bearing against the floor gives a positive withdrawal barrier.
- **Frame to ESP mount:** two M2.5 ×10 and side-loaded nuts under4.2 mm solid
  roofs. The shaft blocks side escape and the nut is geometrically prevented
  from freely turning. This loop remains intact when the complete module is
  removed from the case.
- **Carrier:** four landing pads and locating stops below a retaining frame with
  controlled clearance. No ESP32 or carrier holes. Bare contact areas required.
- **Driver to its mount:** four commercial insulating M2 ×12 screws/nuts through
  the reference PCB holes and plain printed posts; assemble off case.

Frame U-notches expose the independent ESP base screw heads and tool paths.
Hand-tighten gently against the printed stops; do not crank hardware to remove
capture play or flatten electronics. Geometric checks do not establish roof
strength, thread quality, clamp force, print quality or physical USB retention.

## Assembly / disassembly

The viewer has nine stages (0–8):

0. Exploded kit, including four production prints and separate hardware.
1. Deburr base, fit insulating feet and initial cable ties.
2. Support ESP mount off case; side-load nuts, then place prepared socket carrier.
3. Fit frame and its independent two screws; inspect capture play/hard-stop seating.
4. Seat ESP32 evenly, USB left; check buttons, pins and antenna region.
5. Fit driver PCB/four M2 bolts/nuts to its mount off case.
6. Lift complete modules above rim, translate and lower onto common locating pins.
7. Install two M2.5 base screws per module, holding underside nuts with a wrench.
8. Inspect complete stationary housing; perform unpowered checks before bench tests.

To replace a mount, disconnect its cables, remove only its two base screws/nuts
and lift the complete module. Frame and driver PCB fasteners remain installed.
For carrier service, remove the frame screws off case, then lift carrier/ESP32 as
appropriate. For driver service, remove its M2 hardware off case. No simulated
thread rotation, elastic deflection, flexible wiring or motor motion is implied.

## Single CAD source and outputs

```text
external_electronics/
  mechanical/
    make_housing.py                Parameters, four solids, cropped fit coupons
    assembly_parts.py              exact print solids + unmeasured board/socket proxies
    fasteners.py                   commercial hardware envelopes + stack arithmetic
    *.stl                         four assembly-coordinate Fusion exchange exports
    housing_parameters.json        generated resolved values, not editable input
    validation.json                generated geometry/retention/clearance results
    housing_assembly_validation.json
    housing_browser_validation.json
  analysis/
    check_housing.py
    build_enclosure_viewer.py
    check_enclosure_assembly.py
    render_enclosure.py            independent renderer; no legacy imports
    test_enclosure_assembly.cjs
  print_ready/
    stl/                          four bed-oriented production CANDIDATE meshes
    fit_tests/                    four coupon pieces for three fit-test assemblies
  preview/layout.svg              generated current footprint review
  README.md
  PARTS.md
  requirements.txt
```

`build()` is the sole source of printed geometry. `fit_tests()` crops those exact
solids rather than redrawing holes or nut traps. `Parameters` includes socket
origin/length/width, support inset, PCB/carrier sizes, hardware dimensions, capture
play and explicit error allowances. The source intentionally labels purchased
components and all print-error budgets as physically unverified.

The existing folder name `print_ready` describes bed orientation/export, **not**
physical approval. All8 individual printable meshes are closed and connected.
The ESP mount/coupon roofs contain deliberate short6.4 mm bridges; print the small
retention coupon first. Other layer geometry passes the existing0.2 mm/40° probe.

The active viewer remains:

```text
CTS_Simple_Visulizers/External Electronics Enclosure/
  index.html                      generated original-style page
  assembly-viewer.js               authored housing-only controls
  scene.json                      ONE generated mesh/pose payload
  vendor/three.min.js              existing local Three0.128
  vendor/THREE-LICENSE.txt
  preview/assembled.png
  preview/exploded.png
  README.md
```

The older `viewer.js`, `viewer.css`, `vendor/OrbitControls.js` still serve the local
ADCS Testbench and are preserved unchanged. They are not housing dependencies.
The page uses inline CSS reused from Jonathan's unchanged assembly template.

## Independent regeneration and verification

Run all commands below from the **repository root** of a fresh checkout. Use
Python **3.14** (`python3 --version`); exact validated Python package versions are
pinned in `requirements.txt`. The environment and optional sharing/browser
outputs live beside the checkout, not in its proposed commit. No pre-existing
virtual environment, local audit report or historical untracked script is needed.

```sh
python3 --version
python3 -m venv ../cts-housing-venv
. ../cts-housing-venv/bin/activate
export PYTHONDONTWRITEBYTECODE=1
CTS_HOUSING=ONE_DOF_RW/Edge_Rev1/external_electronics
python -m pip install -r "$CTS_HOUSING/requirements.txt"
python -m pip check

# Generate parametric CAD and all eight bed-oriented STL exports.
python "$CTS_HOUSING/mechanical/make_housing.py"
# Regenerate and validate meshes, retention, fit coupons and nominal clearances.
python "$CTS_HOUSING/analysis/check_housing.py"
# Generate the scene/page and optional single-file offline viewer.
python "$CTS_HOUSING/analysis/build_enclosure_viewer.py" --standalone ../cts-enclosure.html
python "$CTS_HOUSING/analysis/check_enclosure_assembly.py"
python "$CTS_HOUSING/analysis/render_enclosure.py"
```

Generation produces assembly-coordinate exchange STLs, resolved parameter JSON
and validation reports locally in `mechanical/`; these are reproducible outputs,
not prerequisites or additional proposed commit files. Only bed-oriented STLs,
the current layout SVG, viewer scene/page and two active previews are included.
STL exports use millimetres. Default generation uses the approved parameters.

Two existing **tracked** repository sources are reused without modification:
`ONE_DOF_RW/Edge_Rev1/analysis/assembly_template.html` supplies viewer CSS, and
`ONE_DOF_RW/Edge_Rev1/mechanical/export_print_ready.py` supplies mesh/layer checks
(and imports its tracked sibling `make_cube_parts.py`). They are present in a
normal checkout; no legacy housing/testbench generator is imported.

All generators resolve repository paths from their own file locations. For a
variant, supply `--parameters ./overrides.json` to `make_housing.py`,
`check_housing.py` and `build_enclosure_viewer.py`; scene checks read its resolved
parameters. The JSON is a partial object overriding `Parameters` fields. Do not
edit generated scene or metadata files to change CAD. Re-run the whole sequence
after a variant change. Physical measurements are required before changing fit
parameters or treating a variant as suitable for actual hardware.

The optional standalone export includes scene, runtime, CSS, Three.js and license
in one generated HTML file. Open `../cts-enclosure.html` directly for offline
assembly review. Repository-relative preview/document links are replaced with
plain text; keep PARTS.md with any manufacturing handoff. Do not edit/commit this
duplicate sharing artifact as another source of truth. The primary implementation
remains maintainable and modular. No large build system or runtime download is
needed to view the committed page.

### What checks establish

- Closed connected meshes, actual STL bounds/volume/triangle agreement and bed orientation.
- Ordinary layer support; separately reported controlled nut-roof bridges with a
  filled-pocket control, not an unconditional support-free claim.
- Assembled interference, reference hole alignment, printed clearance bores,
  screw projections, modeled heads/tools and side nut entry/antirotation.
- **Positive retention:** the installed frame/screws/nuts encounter the roof under
  small upward motion, including bore play; intentionally reopened wells reproduce
  the old free-withdrawal defect. Removing screws allows intended service.
- Separate base-nut retention and carrier capture/contact with an explicit Z budget.
- Driver PCB lift is blocked by the screw heads; the loaded board/fasteners are
  blocked by underside nuts at the mount. A nut-removed control must lift free.
-691 permitted sampled carrier translation/rotation poses; support footprints,
  tail/post clearance and assumed paired XY/solder budgets.
- Rigid loaded module insertion above the rim, and all21 scene mesh groups matching CAD.
- Base geometry invariant under tested board-specific parameter changes.

None establishes physical fit, calibrated tolerance, flexible pin/PCB behavior,
thread pullout, preload force, fatigue/creep, adhesive performance, thermal/RF or
powered balance performance. Print and measure coupons before full production.

## Viewer launch and browser QA

From the **repository root**, in a separate terminal:

```sh
python3 -m http.server 8765 --bind 127.0.0.1 --directory .
```

Open exactly:

<http://127.0.0.1:8765/CTS_Simple_Visulizers/External%20Electronics%20Enclosure/index.html>

The bare root URL deliberately redirects to SAT-1 Commissioning; it is unchanged.
Hard refresh after updates (Cmd+Shift+R on macOS). The scene fetch uses
`cache: no-store`. If 8765 is occupied, reuse a server only after confirming that
it serves this checkout, or choose another port; never terminate an unrelated
listener. The viewer's local JS, scene and vendored Three.js need no npm install
or external network requests.

Browser QA additionally requires Node.js/npm (validated with Node24/npm11),
Playwright1.65.1 and its Chromium. From repository root with the server running:

```sh
npm install --prefix ../cts-housing-browser playwright@1.65.1
../cts-housing-browser/node_modules/.bin/playwright install chromium
NODE_PATH="$PWD/../cts-housing-browser/node_modules" \
CTS_STANDALONE_PATH="$PWD/../cts-enclosure.html" \
node ONE_DOF_RW/Edge_Rev1/external_electronics/analysis/test_enclosure_assembly.cjs
```

On Linux, install the operating-system packages required by Playwright Chromium
if prompted; `playwright install --with-deps chromium` can install those packages
where administrator access is available. The default test uses Playwright's
matching Chromium. `CTS_CHROME_EXECUTABLE` is an optional explicit browser override,
not a required local installation. `CTS_VIEWER_BASE_URL` overrides the server
address. Optional `CTS_SCREENSHOT_DIR` writes review screenshots outside the
repository. Tests cover Play/Pause, Next/Previous, all nine stages, loaded
geometry, quantities, visibility, labels, section/outlines, orbit/zoom, camera
presets, mobile layout and offline HTML. Reports are generated locally and should
remain outside the housing commit. No private preservation manifest is imported.

## Preserved local experiments and proposed commit

ADCS Testbench, its shared runtime, wiring diagrams and historical broad audits
are **not part of this contribution**. They remain locally unchanged. The old
combined `build_viewers.py` now stops before generation, preventing an obsolete
scene schema from overwriting the housing. Its historical body is preserved for
a separately reviewed integration effort. Legacy `render_previews.py`, combined
checks and historical reports remain local; the housing no longer imports them.
Historical PNGs under this mechanical project's preview folder and viewer top.png
remain local, excluded from the active build/document links and commit scope.
No untracked files have been deleted.

Exact proposed contribution (28 files; stage only after isolated verification):

Under `ONE_DOF_RW/Edge_Rev1/external_electronics/`:

```text
README.md
PARTS.md
requirements.txt
mechanical/make_housing.py
mechanical/assembly_parts.py
mechanical/fasteners.py
analysis/check_housing.py
analysis/build_enclosure_viewer.py
analysis/check_enclosure_assembly.py
analysis/render_enclosure.py
analysis/test_enclosure_assembly.cjs
print_ready/stl/External_Tray.stl
print_ready/stl/ESP32_Mount.stl
print_ready/stl/Driver_Mount.stl
print_ready/stl/Carrier_Retainer.stl
print_ready/fit_tests/Fit_Retention_Base.stl
print_ready/fit_tests/Fit_Retention_Cap.stl
print_ready/fit_tests/Fit_ESP_Carrier.stl
print_ready/fit_tests/Fit_Driver_Mount.stl
preview/layout.svg
```

Under `CTS_Simple_Visulizers/External Electronics Enclosure/`:

```text
README.md
index.html
assembly-viewer.js
scene.json
vendor/three.min.js
vendor/THREE-LICENSE.txt
preview/assembled.png
preview/exploded.png
```

Exclude ADCS Testbench; wiring/electrical experiments; shared old viewer runtime
and OrbitControls; legacy combined generators/checks; historical AUDIT.md and
original_*.json; generated parameter/validation JSON; assembly-coordinate
mechanical STLs; old preview copies; standalone export and temporary browser
screenshots. Fusion exchange meshes are useful local outputs, not obsolete files.
The guarded legacy builder remains local, not a requirement of a fresh housing-only
checkout. Do not stage entire untracked directories wholesale.

No original Edge Cube file, firmware or root redirect is changed. Stage only the
explicit contribution above after verification; inspect the cached diff before
requesting commit approval. Do not commit, push, merge or create a PR without
separate approval. Actual hardware fitting,
bridge/retention testing, insulation checks and thermal trials remain physical tasks.
