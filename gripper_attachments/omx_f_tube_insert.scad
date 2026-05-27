// ============================================================
//  OMX_F Gripper — Tube-Grip Tip Insert
//  Target: 13 mm OD glass test tube held VERTICALLY (tube axis = Z)
//  Zone  : blade X = 40 → 65 mm (finger-local frame)
//  Print : TPU 95A recommended (glass-safe, high friction)
//
//  Retention strategy (top-view layout along finger length)
//  ────────────────────────────────────────────────────────
//   X=40 ─── 45.6 ──── 59.4 ─── 65 ── 67.5
//   |  GRIP  |  CRADLE  |  GRIP  |CAP|
//    (-X wrap   (-Y cut    (+X wrap  (closed
//     full      for tube)   full)    tip past
//     blade)                          blade)
//
//   • GRIP zones: insert wraps blade on all 4 sides (Y±, Z±) →
//     friction fit + clip_lip on +Y face holds insert on blade.
//   • CAP: solid material past blade tip stops insert from sliding
//     off in +X direction. Blade tip butts against inside of cap.
//   • CRADLE: cylindrical cut (axis ‖ Z) on -Y face for vertical
//     tube. Two fingers' bites combine into full circle when closed.
//   • Mirrored in Y for link7 (inner face = +Y).
// ============================================================

// ── USER PARAMETERS ─────────────────────────────────────────

tube_od       = 13.0;   // target tube outer diameter (mm)
tube_clear    = 0.4;    // gap between tube and cradle (mm)
clearance     = 0.25;   // blade fit clearance (mm) — reduce if loose
wall          = 2.2;    // min wall around blade (mm)
clip_lip      = 0.8;    // snap-fit undercut depth on outer Y face (mm)
cap_thick     = 2.5;    // closed tip cap past blade tip (mm) — +X retention
cradle_x_frac = 0.5;    // tube center along insert X: 0=start, 1=end (0.5=mid)
cradle_sink   = 0.0;    // mm to recess tube center into +Y past inner face
                        //   0 = exact half-cylinder cut (cradle = half tube)
                        //   >0 = deeper bite (more grip, less Y material)
show_phantom  = false;  // show translucent blade for alignment check
which_finger  = "both"; // "link6" | "link7" | "both"

// ── BLADE CROSS-SECTION TABLE (X=40..65 zone) ───────────────
//   [ X, half_Y, half_Z ]  — measured via trimesh.section()
blade_pts = [
    [ 40, 3.0, 14.4 ],
    [ 46, 2.8, 12.7 ],
    [ 55, 3.5, 10.3 ],
    [ 62, 3.5,  8.3 ],
    [ 65, 3.0,  7.6 ],
];

X_START = 40;
X_END   = 65;
INS_LEN = X_END - X_START;  // 25 mm

// ── DERIVED ──────────────────────────────────────────────────
tube_r   = tube_od / 2;
cradle_r = tube_r + tube_clear;          // cradle radius (cut)
X_CTR    = X_START + cradle_x_frac * INS_LEN;

// ── HELPERS ──────────────────────────────────────────────────
function lerp(a, b, t) = a + (b-a)*t;

// Find segment index i s.t. blade_pts[i].x <= x < blade_pts[i+1].x
function seg(x, i=0) =
    (i >= len(blade_pts)-2) ? i :
    (x <= blade_pts[i+1][0]) ? i : seg(x, i+1);

function bhy(x) =
    let(i = seg(x), x0 = blade_pts[i][0], x1 = blade_pts[i+1][0])
    lerp(blade_pts[i][1], blade_pts[i+1][1], (x-x0)/(x1-x0));

function bhz(x) =
    let(i = seg(x), x0 = blade_pts[i][0], x1 = blade_pts[i+1][0])
    lerp(blade_pts[i][2], blade_pts[i+1][2], (x-x0)/(x1-x0));

N = 16;  // hull slices

// ── MODULES ──────────────────────────────────────────────────

// Outer body: blade envelope + wall, extended past tip by cap_thick.
// Cavity stops at X_END → x=X_END..X_END+cap_thick is solid (tip cap).
module insert_outer() {
    hull() {
        for (i = [0:N]) {
            x = X_START + i * INS_LEN / N;
            hy = bhy(x) + wall + clearance;
            hz = bhz(x) + wall + clearance;
            translate([x, 0, 0])
                cube([0.01, hy*2, hz*2], center=true);
        }
        // Tip cap slice (same Y/Z dims as X_END)
        hy_end = bhy(X_END) + wall + clearance;
        hz_end = bhz(X_END) + wall + clearance;
        translate([X_END + cap_thick, 0, 0])
            cube([0.01, hy_end*2, hz_end*2], center=true);
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

// Full-finger phantom — imports actual STL (curved geometry).
// STL native units = mm, finger-local frame (pivot at x=0, tip at x=65).
// link6 = motorized side; link7 phantom handled by parent scale([1,-1,1]).
STL_LINK6 = "model/omx_f_mesh/follower_07_gripper_motorized.stl";

module blade_phantom() {
    color("cyan", 0.25)
        import(STL_LINK6, convexity = 10);
}

// Entry lead-in: chamfer the open end (X_START side) so blade slides in
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
