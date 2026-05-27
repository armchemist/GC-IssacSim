// ============================================================
//  OMX_F Gripper — Tube-Grip Tip Insert
//  Target: 13 mm OD glass test tube held VERTICALLY (tube axis = Z)
//  Zone  : blade X = 55 → 65 mm (finger-local frame)
//  Print : TPU 95A recommended (glass-safe, high friction)
//
//  Geometry logic
//  ─────────────
//  • Insert slides onto blade tip from +X (open end faces housing)
//  • C-clip profile wraps blade in Y and Z → friction fit
//  • Cylindrical cut on inner face (-Y for link6, +Y for link7):
//    half-circle cradle, axis ‖ Z (vertical tube). Two fingers
//    closing combine the two half-cradles into a full circle.
//  • Mirrored in Y for link7 (inner face = +Y)
//  • Top-view of grip: two ] [ profiles cradling a vertical tube.
// ============================================================

// ── USER PARAMETERS ─────────────────────────────────────────

tube_od       = 13.0;   // target tube outer diameter (mm)
tube_clear    = 0.4;    // gap between tube and cradle (mm)
clearance     = 0.25;   // blade fit clearance (mm) — reduce if loose
wall          = 2.2;    // min wall around blade (mm)
clip_lip      = 0.8;    // snap-fit undercut depth on outer Y face (mm)
cradle_x_frac = 0.5;    // tube center along insert X: 0=start, 1=end (0.5=mid)
cradle_sink   = 0.0;    // mm to recess tube center into +Y past inner face
                        //   0 = exact half-cylinder cut (cradle = half tube)
                        //   >0 = deeper bite (more grip, less Y material)
show_phantom  = false;  // show translucent blade for alignment check
which_finger  = "both"; // "link6" | "link7" | "both"

// ── BLADE CROSS-SECTION TABLE (X=55..65 zone only) ──────────
//   [ X, half_Y, half_Z ]
blade_pts = [
    [ 55, 3.5, 10.3 ],
    [ 62, 3.5,  8.3 ],
    [ 65, 3.0,  7.6 ],
];

X_START = 55;
X_END   = 65;
INS_LEN = X_END - X_START;  // 10 mm

// ── DERIVED ──────────────────────────────────────────────────
tube_r   = tube_od / 2;
cradle_r = tube_r + tube_clear;          // cradle radius (cut)
X_CTR    = X_START + cradle_x_frac * INS_LEN;

// ── HELPERS ──────────────────────────────────────────────────
function lerp(a, b, t) = a + (b-a)*t;

// Blade half_Y at local X (linear interp across 3 pts)
function bhy(x) =
    (x <= blade_pts[1][0])
        ? lerp(blade_pts[0][1], blade_pts[1][1],
               (x-blade_pts[0][0])/(blade_pts[1][0]-blade_pts[0][0]))
        : lerp(blade_pts[1][1], blade_pts[2][1],
               (x-blade_pts[1][0])/(blade_pts[2][0]-blade_pts[1][0]));

// Blade half_Z at local X
function bhz(x) =
    (x <= blade_pts[1][0])
        ? lerp(blade_pts[0][2], blade_pts[1][2],
               (x-blade_pts[0][0])/(blade_pts[1][0]-blade_pts[0][0]))
        : lerp(blade_pts[1][2], blade_pts[2][2],
               (x-blade_pts[1][0])/(blade_pts[2][0]-blade_pts[1][0]));

N = 16;  // hull slices

// ── MODULES ──────────────────────────────────────────────────

// Outer body of the insert (blade envelope + wall)
module insert_outer() {
    hull()
        for (i = [0:N]) {
            x = X_START + i * INS_LEN / N;
            hy = bhy(x) + wall + clearance;
            hz = bhz(x) + wall + clearance;
            translate([x, 0, 0])
                cube([0.01, hy*2, hz*2], center=true);
        }
}

// Blade cavity (blade shape + clearance)
module blade_cavity() {
    // Full pass-through cavity — open at X_START end for sliding
    translate([-0.1, 0, 0])   // extend slightly past start
    hull()
        for (i = [0:N]) {
            x = X_START + i * INS_LEN / N;
            hy = bhy(x) + clearance;
            hz = bhz(x) + clearance;
            translate([x, 0, 0])
                cube([0.01, hy*2, hz*2], center=true);
        }
}

// Cylindrical tube cradle — axis ‖ Z (vertical tube).
// Cut center sits on (or sinks past) the inner -Y face; the cylinder
// removes a half-circle bite from the insert in the XY plane. The two
// fingers' bites combine into a full cylinder when the gripper closes.
module tube_cradle() {
    face_y = -(bhy(X_CTR) + wall + clearance);   // inner -Y face at X_CTR
    cy     = face_y + cradle_sink;               // tube axis Y
    // height: full Z extent of insert + margin (cuts through top/bottom)
    h_z = max(bhz(X_START), bhz(X_END)) * 2 + 2*wall + 4*clearance + 10;
    translate([X_CTR, cy, 0])
        cylinder(r = cradle_r, h = h_z, center = true, $fn = 80);
}

// Snap-fit clip lip on outer +Y face (keeps insert from sliding off blade)
module clip_lip() {
    hull()
        for (i = [0:N]) {
            x = X_START + i * INS_LEN / N;
            hy_out = bhy(x) + wall + clearance;
            hz_out = bhz(x) + wall + clearance;
            translate([x, hy_out, 0])
                cube([0.01, clip_lip*2, hz_out*1.2], center=true);
        }
}

// Phantom blade for visual alignment check
module blade_phantom() {
    color("cyan", 0.2)
    hull()
        for (i = [0:N]) {
            x = X_START + i * INS_LEN / N;
            translate([x, 0, 0])
                cube([0.01, bhy(x)*2, bhz(x)*2], center=true);
        }
}

// Entry lead-in: chamfer the open end (X=55 side) so blade slides in
module entry_chamfer() {
    ch = 1.5;  // chamfer size
    hull() {
        // Normal profile at X_START
        translate([X_START, 0, 0]) {
            hy = bhy(X_START) + clearance;
            hz = bhz(X_START) + clearance;
            cube([0.01, hy*2, hz*2], center=true);
        }
        // Enlarged profile slightly before X_START
        translate([X_START - ch, 0, 0]) {
            hy = bhy(X_START) + clearance + ch;
            hz = bhz(X_START) + clearance + ch;
            cube([0.01, hy*2, hz*2], center=true);
        }
    }
}

// Complete insert for link6 (inner = -Y)
module insert_link6() {
    difference() {
        union() {
            insert_outer();
            clip_lip();         // snap ridge on outer +Y
        }
        blade_cavity();
        tube_cradle();      // half-cylinder cut for vertical tube on -Y face
        entry_chamfer();
    }
    if (show_phantom) blade_phantom();
}

// Complete insert for link7 (inner = +Y, mirror of link6)
module insert_link7() {
    scale([1, -1, 1])
        insert_link6();
}

// ── RENDER ───────────────────────────────────────────────────
SEP = 45;  // Y separation when showing both

if (which_finger == "link6") {
    insert_link6();
} else if (which_finger == "link7") {
    insert_link7();
} else {
    translate([0,  SEP/2, 0]) insert_link6();
    translate([0, -SEP/2, 0]) insert_link7();
}

// ============================================================
//  PRINT GUIDE
// ─────────────────────────────────────────────────────────────
//  Material  : TPU 95A  (Shore hardness gives compliance +
//              grip on glass; PLA/PETG alternative if no TPU)
//  Orientation: stand on +X end — Z axis vertical = cradle axis vertical
//              (avoids supports inside the cradle arc).
//  Layer h   : 0.15 mm for smooth cradle surface
//  Walls     : 3 perimeters (no infill needed — solid is fine
//              for such a small part)
//  Supports  : none needed
//
//  FIT TUNING
//  ──────────
//  Too loose on blade → decrease clearance (try 0.15)
//  Too tight          → increase clearance (try 0.35)
//  Clip doesn't snap  → increase clip_lip (try 1.2)
//
//  TUBE CRADLE GEOMETRY (13 mm tube, vertical = Z axis)
//  ─────────────────────────────────────────────────────
//  cradle radius      : 6.5 + tube_clear mm
//  cradle axis        : Z (tube vertical)
//  cradle center X    : X_START + cradle_x_frac * INS_LEN  (default mid)
//  bite shape         : half-cylinder cut into inner Y face
//  → two fingers' bites = full circle around tube when closed
//  → tube extends vertically through the open ends in Z
//
//  GEOMETRY CONSTRAINT
//  ───────────────────
//  Tube radius (6.5 mm) > finger half-Y at tip (~3 mm), so the cradle
//  cuts past the finger centerline in Y. This is expected: the cradle
//  is shared between both fingers when closed. The +Y wall remains
//  ~(half_Z + wall - cradle_r) thick — verify visually before printing.
// ============================================================
