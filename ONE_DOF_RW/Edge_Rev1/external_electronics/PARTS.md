# Manufacturing checklist — modular external housing

**Preliminary CAD, not physically validated. Print fit coupons before the case.**
Units: mm. The 125 × 90 × 35 open-top housing remains stationary, separate from
the moving Edge Cube. Stock hardware counts, heads and electronics are unmeasured.

## A. Printable components

All listed meshes are closed, connected individual pieces and already oriented
on z=0. Proposed process: unfilled PETG, 0.4 mm nozzle, 0.2 mm layers; use the
printer/material's calibrated profile. These are starting process choices, not
validated settings. Inspect perimeters around small holes, posts and nut roofs.
No small printed threads or snap tabs are used.

Production files under `print_ready/stl/`:

| STL | Qty | Actual generated bounds | Function | Bed orientation | Support / bridge requirement | Physical testing needed |
|---|---:|---|---|---|---|---|
| `External_Tray.stl` | 1 | 125 × 90 × 35 | Common base, bearings, locator pins, four M2.5 interfaces, service windows, exits and tie anchors | Floor down, open top up | No supports indicated by geometric layer probe | Yes: module seating, tool/feet/tie access |
| `ESP32_Mount.stl` | 1 | 76.2 × 60 × 12.1 | Replaceable carrier mount, landing posts, stops, side-entry nut pockets and USB saddle | Flat plate down, posts up | Two **6.4 mm maximum-span roof bridges**; coupon validation required | Yes: roof, nut retention, carrier and USB |
| `Driver_Mount.stl` | 1 | 35 × 60 × 8 | Replaceable four-position driver mount | Flat plate down, posts up | No supports indicated | Yes: actual PCB, holes, supports and insulation |
| `Carrier_Retainer.stl` | 1 | 69 × 60 × 3 | Carrier capture, hard-stop bearing and access notches for module tools | Broad underside down | No supports indicated | Yes: capture play, release and repeated service |

Coupon files under `print_ready/fit_tests/`; PETG and process should match the
production parts. These are **test pieces, not extra parts in the enclosure**. Every coupon needs physical testing; none is a validated clip/pin mechanism:

| STL | Qty per trial | Bounds | Purpose / use | Bed orientation | Support / bridge requirement |
|---|---:|---|---|---|---|
| `Fit_Retention_Base.stl` | 1 | 12 × 14 × 9.5 | First print: cropped actual ESP nut boss, side port and real roof | Flat base down, roof/post up | One 6.4 mm roof bridge; qualify first |
| `Fit_Retention_Cap.stl` | 1 | 12 × 13 × 3 | First print: matching cropped frame; use one M2.5 ×10 and nut | Broad underside down | No supports indicated |
| `Fit_ESP_Carrier.stl` | 1 | 74.2 × 60 × 12.1 | Actual landing/locating/retention/USB features, cropped from ESP mount; use the **production Carrier_Retainer**, two screws/nuts and actual carrier/sockets | Flat plate down, posts up | Two 6.4 mm roof bridges; qualify first |
| `Fit_Driver_Mount.stl` | 1 | 32 × 27.5 × 8 | Actual four posts and holes cropped from driver mount; use actual PCB and four M2 screws/nuts | Flat plate down, posts up | No supports indicated |

Retention-base and ESP coupons contain the same roof bridges as the production
mount. No other unsupported layer was detected; a filled-pocket control removes
that layer's unsupported area. This identifies a deliberate short bridge, **not**
a demonstrated printable or strong roof. Check bridge sag before inserting nuts.
If the bridge or roof fails, adjust the shared pocket/printing parameters and
repeat the coupon before the full mount. Do not treat the layer report as a
strength certification.

`mechanical/*.stl` are the same four production solids in assembly coordinates,
useful for Fusion assembly import. For slicing use the bed-oriented files above.
Do not print board, socket or hardware visualization proxies.

## B. Existing electronics and prepared carrier

| Item | Qty | Requirement / provisional allowance | Availability / optional? |
|---|---:|---|---|
| ESP32 development board | 1 | Approximately55 ×28 **overall envelope**, not a confirmed PCB revision or header datum | Reported existing; required, no extra board purchase assumed |
| SimpleFOC Mini | 1 | DFRobot v1.0 reference26 ×21.5; four Ø2 holes on22 ×17.5; actual purchased board unconfirmed | Purchased kit; required, delivered revision unverified |
| Prepared insulating carrier | 1 | 60 ×40 ×1.6 allowance; no mounting holes required; bare support corners and edge strips required | Prepare/obtain if absent; required for selected arrangement |
| Female socket rows | 2 | Length46, width2.6, row spacing25.4, height6 and centered origin are configurable allowances; determine pin count/pitch from actual board | Stock unconfirmed; obtain if absent, required; pin count must be measured |

The carrier is a separately prepared FR4/perfboard part, not a printed PCB. Cut,
deburr and prepare it before checking fit; reserve contact areas without solder,
components or exposed conductors. A printed socket cradle could replace it later,
but is not part of this revision. Perfboard copper and wiring must respect the
actual antenna region; do not assume overall outline center locates the headers.

Reference drawing: <https://dfimg.dfrobot.com/wiki/19354/DRI0058_simplefocmini-driver-board_dimension_V1.0.jpg>.
Espressif's example DevKitC V4 has48.26 ×27.94 main PCB plus6.04 antenna overhang;
that does not identify the team's board: <https://dl.espressif.com/dl/schematics/esp32_devkitc_v4_dimensions.pdf>.
Never mix v1.0/v1.1/v2.3 driver mechanical specifications or enlarge PCB holes
based on this model.

## C. Fastener BOM

**Final fastening review, 2026-11-19: unchanged.** Retain commercial insulating
M2 driver fasteners and the existing M2.5 fastening. No speculative printed
bracket/pin/clip is added. The [README comparison](README.md#final-fastening-decision--2026-11-19)
records why the alternatives are not selected. This decision does not validate
actual hole fit, bare bearing areas, printed strength or available stock counts.


All lengths are **under the head**. The kit lists M2.5 lengths4/6/8/10/14/18/20,
nuts, flat and lock washers. It does not establish actual quantities/head sizes
and does not contain the required M2 hardware by assumption.

| Item | Qty installed | Purpose | Head / nut assumption | Stock status |
|---|---:|---|---|---|
| **M2.5 ×10 screws** | **4** | Two per complete module to common base | Socket-head label; actual shape/drive unknown, modeled envelope Ø5.5 ×3 | Listed kit length; count/measure4 |
| **M2.5 ×10 screws** | **2** | ESP carrier frame to its own mount, independently of case fastening | Same Ø5.5 ×3 envelope | Listed kit length; count/measure2 |
| M2.5 hex nuts | 4 | Ordinary underside module nuts | AF5 ×2 allowance | Listed kit type; actual size/count unknown |
| M2.5 hex nuts | 2 | Side-loaded frame captive nuts | AF5 ×2 allowance | Listed kit type; check fit/antirotation on coupon |
| **Commercial insulating M2 ×12 screws** | **4** | Driver PCB through printed posts/plate | Head Ø4 ×2.5 allowance; actual shape/drive must be selected against PCB bearing clearance | **Additional stock to obtain** |
| Insulating M2 nuts | 4 | Driver mounting, accessible off case | AF4 ×1.6 allowance | **Additional stock to obtain** |
| Flat washers / lock washers | 0 /0 | None in nominal stacks | Conditional on actual bearing checks; do not add without recalculating stack | Kit contains M2.5 washers but none assumed necessary |
| Bought spacers / heat-set inserts | 0 /0 | Printed supports replace spacers | No printed thread engagement | Not required |

Total: **10 screws, 10 nuts, no washers, no bought spacers**. No extra M2.5 length
is required by the nominal geometry. Coupons can reuse this hardware; no extra
installed quantity is hidden in the BOM.

### Calculated stacks

| Mount | Head seat z | Nut interval z, assembled | Grip before nut | Length | Tip z | Projection beyond nut |
|---|---:|---|---:|---:|---:|---:|
| Module → base, four positions | 7.0 | −2 to0 | 7.0 | **M2.5 ×10** | −3.0 | **1.0** |
| Carrier frame → ESP mount, two positions | 17.5 | 8.3 to10.3 | 7.2 | **M2.5 ×10** | 7.5 | **0.8** |
| Driver → removable mount, four positions | 14.6 | 3.4 to5.0 | 9.6 | **M2 ×12** | 2.6 | **0.8** |

The frame nuts can initially rest atz8.0–10.0, before lifting0.3 to the roof when
tightened; projection is still0.5 at that initial seat. Loaded roof thickness is
**4.2**. All nut/shaft geometry is nominal; actual tip chamfers and incomplete
threads can reduce usable engagement. Measure before accepting the lengths.

- Module grip = floor3 + base support2 + mount plate2 =7. Four ordinary nuts
  bear below the floor. Two independent screws release either complete mount.
- Frame grip = frame3 + solid material down to nut roof4.2 =7.2. Nut roof at10.3
  is a real barrier above the nut, with the entry port on the side. Installed
  screw prevents the nut escaping through that port. This closes the load path
  through **frame → printed column/roof → nut → screw** within the ESP mount.
- Driver grip = plate2 + printed support6 + PCB1.6 =9.6. Fit nuts from below
  while the mount is off case. Generic base windows clear nut tools and tips.
- A6 mm frame screw no longer reaches the nut adequately. An8 mm module screw
  ends at the nut's far face with no projection. An10 mm M2 driver screw is too
  short for the full9.6 grip +1.6 nut. Keep the selected lengths pending measurement.
- Six M2.5 screws are all×10 for practical assembly. Do not substitute longer
  ones casually: base feet leave only **3 mm nominal below module screw tips**.

### Contact, preload, heads and tools

Frame tightening stops on two broad printed column tops atz14.5. Carrier top is
z14.1; **0.4 mm intentional capture play**, not compressive PCB preload. The frame
retains bare carrier edge strips after this limited movement. With assumed
carrier thickness error0.1 and relative print-height error2 ×0.1, the remaining
nominal gap is0.1. These are **unverified budgets**, not printer specifications.
Check actual play/rocking on the coupon and update parameters before full print.
Do not tighten harder to remove play or flatten a PCB.

Carrier contact regions: nominal front/rear bare strips y27–30 and64–67, plus
four landing pads. Landing centers are our fixture geometry, **not ESP32 holes**.
All four landing contacts retain at least17.33 mm² area in sampled allowed carrier
poses. Actual bare corner regions, flatness, copper and pin locations need inspection.

The frame has Ø7 open tool/head-access notches over the ESP module-to-base
fasteners. Vertical nominal head/tool envelopes are clear of printed parts and
board proxies. Real hex-key bends, fingers and screwdriver handles are not modeled.
Hold the four base nuts with an appropriate small wrench while turning the top
screws. Side-loaded frame nuts should resist rotation; test this gently on coupon.

Do not assume button-head hardware. M2.5 Ø5.5 ×3 and M2 Ø4 ×2.5 are envelopes,
not identified stock. Driver corner bearing areas and metal trace clearance are
unconfirmed; **M2.5 must not pass through Ø2 reference PCB holes**. Nominal M2 in a
nominal Ø2 hole still requires a free physical fit. If insulating washers or a
different head are required, revise the stack, not the actual PCB holes.
Printed M2.5 clearance isØ3.1, M2 support boreØ2.6, locator pinØ2.6 withØ3.6/elongated receiving holes. These conservative nominal clearances still require coupon fitting.
Hand-tighten gently, without a power driver. No tightening torque rating is given.

## D. Other required components

| Item | Qty / size | Existing stock / additional need | Optional? |
|---|---|---|---|
| Insulating adhesive feet | 4; provisional Ø8 ×6 | Stock unconfirmed; obtain if absent. Centers inset8 from x edges and6 from y edges; check actual diameter/placement | Required; compressed height must leave ≥2 mm below module screw tips and actual tie loops |
| Jacket ties | Up to4, one per populated paired anchor; width/thickness measured to fit | Stock unconfirmed; obtain for the cables actually fitted | Required where strain relief is used, omit only for unused anchors; do not silently omit loaded-cable restraint |
| Soft cable-contact sleeving/pad | As needed for real contact points; size after cable fitting | Obtain if actual jacket/boot would rub a hard edge | Conditional; not required at a non-contacting surface |
| USB source and cable | 1 compatible cable/source; actual connector unconfirmed | Existing bench assumption; verify stock and plug/bend fit | Cable required for physical USB test; powered source not required for initial unpowered fitting |
| Current-limited12 V lab supply | 1 | Existing laboratory assumption, not a newly designed housing component | Not needed for unpowered fit coupons; needed for subsequent reviewed powered bench tests |

Fasteners are listed only in C and carrier/socket hardware only in B; they are
not hidden optional purchases. M2.5 screws/nuts are kit-listed, quantities and
actual dimensions uncounted. M2 screws/nuts are additional stock. Zero washers
are required by the nominal stack; add insulating/bearing washers only after
checking need and recalculating length. No commercial spacer or threaded insert
is required. Printed support geometry provides spacing.


No lid, fan, tiny printed fasteners or additional driver bracket is required.
Use clean insulating bench support: the base has open service/vent windows below
the modules and is a laboratory prototype, not a sealed protective enclosure.

## E. Tools

Printer/slicer; calibrated calipers with depth measurement; small rule/feeler
shims; correct M2.5 driver for actual kit heads; driver matching actual M2 heads;
small nut wrench/driver; tweezers, cutters and deburring/file tools. Preparing the
carrier may require soldering equipment and lead restraint. Use a multimeter for
unpowered continuity/short checks and temperature measurement for powered bench
trials. Disconnect power before assembly, measuring electronics or removing nuts.

## F. Measurements before the first full print

Record these on actual components, including maximum protrusions rather than
nominal catalog values:

| Measure / inspect | Record |
|---|---|
| ESP32 manufacturer/revision, main PCB outline, total outline/overhangs, thickness | __________ |
| Header pin count/pitch, row spacing and origin relative to USB/main PCB | __________ |
| Socket body dimensions, installed height, seating depth and retention | __________ |
| Carrier outline/thickness/flatness, bare landing areas and frame strips | __________ |
| Maximum underside pin/solder projection and actual solder footprint | __________ |
| Antenna keepout, BOOT/EN access and accessible GPIO connections | __________ |
| USB plug/boot dimensions, mating travel, bend direction and insertion loads | __________ |
| Driver revision, shaped outline, hole diameters and X/Y centers | __________ |
| Driver underside parts, top components, populated rows and mating connectors | __________ |
| Component/trace-free head/post bearing areas around all four driver holes | __________ |
| Actual M2.5/M2 lengths, head/drive sizes, nut AF/heights, usable threads and counts | __________ |
| Feet diameter/compressed height, tie width/thickness and loop clearance | __________ |
| Printer/nozzle/filament/profile and measured hole/pocket/height errors | __________ |

## Fit-test procedure and acceptance record

All tests below start **unpowered**, with actual electronics supported and
protected from loose tools. PETG/process/orientation are specified in A. Reuse
coupon hardware in the final assembly; no extra installed quantity is required.
The pass/fail criteria are preliminary project screening criteria, not a rated
pull force, fatigue life, certified electrical spacing or thermal qualification.

### 1. Retention base and cap — print first

**Print:** `Fit_Retention_Base.stl` and `Fit_Retention_Cap.stl`, one each. Base flat
down, cap broad underside down. Use proposed unfilled PETG/0.4 nozzle/0.2 layers
and record actual profile. The base contains a short roof bridge; inspect it
before inserting anything. **Required:** one kit M2.5 ×10 screw, one actual nut,
matching driver, calipers and optionally a force gauge.

1. Measure printed hole, nut-port/well, roof sag and actual nut/head/thread sizes.
2. Side-load the nut without forcing it; place cap on the hard-stop surface.
3. Insert screw, verify full usable engagement and gently seat it against stops.
4. Attempt a gentle direct upward withdrawal of the cap. Record force if measured;
   otherwise record only a qualitative result, never an invented load rating.
5. Remove screw; cap and nut must release deliberately without breaking/prying.

**Pass:** nut enters freely, is restrained against free rotation when engaged,
roof is complete with no crack/whitening/delamination, screw traverses full usable
nut, cap cannot withdraw with screw fitted, and releases after screw removal.
**Fail:** free withdrawal, nut spinning, thread stripping/bottoming, bridge sag
blocking the nut, damaged roof or forced assembly. Stop and update shared CAD or
print settings before a full mount. A passed hand test is not proof of strength
at arbitrary load or temperature.

### 2. Driver mounting coupon

**Print:** `Fit_Driver_Mount.stl`, flat plate down/posts up; same PETG/process.
**Required:** actual driver, four commercial insulating M2 ×12 screws and four
matching insulating nuts, correct driver/nut tool, calipers and inspection light.

1. Confirm delivered revision and measure outline, four hole diameters/centers,
   PCB thickness, underside parts, connector bodies and bare bearing regions.
2. Check each actual M2 shaft passes the actual PCB hole freely; never drill or
   force the PCB. Place it on all four supports without holding it bent flat.
3. Fit four screws/nuts off case, gently and progressively. Check actual head
   bearing, thread projection and access; washers are not silently added.
4. Inspect for PCB rocking, bending, component/copper contact and obstruction of
   connectors. Gently check axial seating; remove the board and inspect the pads.

**Pass:** all four holes align without force, all supports contact appropriate
bare areas, fasteners engage fully, PCB is retained without new bow/rocking,
heads do not load components or terminals, and board can be removed intact.
**Fail:** any shaft interference, forced alignment, loss of seating, lifted or
bent PCB, component/trace damage, inadequate usable thread or unsafe contact.
The reference rectangular proxy is not evidence that these checks have passed.
The computational head/nut withdrawal check verifies nominal rigid barriers and
the nut-removed release path; it does not establish insulating-fastener strength,
thread durability or safe contact on the delivered PCB.

### 3. ESP32 carrier coupon and production retainer

**Print:** `Fit_ESP_Carrier.stl` plus `Carrier_Retainer.stl`, each with its broad
base down; same PETG/process. Retainer can be reused in production. **Required:**
prepared carrier, matching two socket rows, actual ESP32, two M2.5 ×10 screws and
two nuts, actual USB cable, calipers/feeler shims and inspection light.

1. Measure socket origin/count/pitch/height, carrier thickness/flatness and the
   complete pin/solder footprint. Inspect bare landing corners and capture strips.
2. Side-load nuts, seat carrier and fit retainer screws gently to printed stops.
3. Measure carrier play before and after seating ESP32 evenly. Current nominal
   gap is0.4; provisional expected range from the stated Z budget is0.1–0.7.
   A result outside that range requires dimension/process review, not more torque.
4. Inspect underside at all allowed movement extremes: no pin/solder contact,
   ≥1 mm residual tail/post clearance is the current project target. Check actual
   plug/body/bend space, BOOT/EN/GPIO and antenna clearance.
5. Support the board while inserting/removing USB; check carrier stays captured
   and the board does not lever out of sockets or bend pins. Lift out the ESP32
   evenly, remove frame screws and inspect all contact areas.

**Pass:** hard stops seat, carrier has positive limited play without compression,
frame prevents its withdrawal beyond capture play, all supports remain usable,
actual electrical/contact regions are clear, USB can be serviced with support,
and board/carrier release intentionally without damage. **Fail:** pinch/bow,
excessive or lost capture, interference, inadequate clearance, pin bending,
unintended socket unseating or damaged roof/threads.

### Repeated-service screen and complete assembly

For each coupon, perform **10 careful assembly/removal cycles** as an initial
screen. This is a proposed screening count, not a validated service life. Record
fit, gap/thread engagement and damage at cycles1,5 and10. Stop immediately at a
failure; do not finish the count by forcing parts. Pass requires repeatable
intentional release, retained seating and no growing looseness, cracks, whitening,
delamination or PCB/pin damage. Record the operator, tools, actual hardware and
whether any pull force was measured. There are no new printed clip/pin mechanisms
to test in the selected design; none should be substituted on the basis of this
procedure without its own geometry and repeated-use qualification.

Only after coupon results and parameter corrections, print/fit complete modules
and tray. Check two-screw module removal with PCB/frame still fastened, tool
access, tie clearance and compressed feet. Current module tips extend3 below the
base; require ≥2 mm to the bench after compression and check tie loops separately.
Measure any rocking before tightening; do not force the boards flat.

After unpowered insulation checks and a separately reviewed electrical setup,
observe temperature/creep, loosening and stability under the intended bench load.
Open top and windows are airflow features, not thermal qualification. Neither
FDM material nor commercial insulating screws are assigned a temperature/torque
rating by these CAD checks. No clips, snap hooks, pins or threaded alternatives
are approved by passing a purely geometric simulation.

### Trial record

| Field | Record |
|---|---|
| Date/operator, coupon filename, CAD parameter file/revision | __________ |
| Printer, nozzle, material, layer/perimeter/bridge profile | __________ |
| Actual screw/head/nut dimensions and usable thread | __________ |
| Printed hole/port/well sizes and bridge sag | __________ |
| PCB/carrier/socket dimensions and actual contact regions | __________ |
| Capture gap, minimum tail/post gap and USB clearance | __________ |
| Seating/retention/release at cycles1,5,10 | __________ |
| Pull force/direction if measured; otherwise qualitative only | __________ |
| PCB movement/bending, pin damage, cracks/whitening/creep | __________ |
| Pass/fail, failed criterion and required correction | __________ |

Keep failed measurements. A failure blocks that physical assembly until corrected;
it does not justify a speculative replacement mechanism without a verified contact
map and positive locking design. Print the small retention pair first.

## Computational clearance limits

Default sampled carrier tail/post gap: **2.524 centered**, **1.872 across691 allowed
sampled translation/rotation poses**. Subtract the assumed0.4 paired XY error and
0.3 extra solder allowance: **1.172 residual**. This is a finite sampled budget
using provisional rectangular tail strips, not a physical-fit guarantee.
Tail-to-floor allowance6.5; tail-to-remaining-plate-top2.5. Both socket origin
coordinates are configurable and must be measured before relying on these values.

USB boot/frame rail nominal gap1.0; driver power service/frame lateral gap2.0.
Service envelopes include unmeasured plug allowances. Driver PCB underside isz13,
ESP undersidez20.1. The provisional driver mating envelope reachesz36.6, above
the open35 mm rim. Confirm actual component and connector heights.

Resolved current results are generated into `mechanical/validation.json`.
