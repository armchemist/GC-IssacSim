// ============================================================
//  OMX_F Gripper — V-Groove Tip Insert
//  Target: 13 mm OD glass test tube
//  Zone  : blade X = 55 → 65 mm (finger-local frame)
//  Print : TPU 95A recommended (glass-safe, high friction)
//
//  Geometry logic
//  ─────────────
//  • Insert slides onto blade tip from +X (open end faces housing)
//  • C-clip profile wraps blade in Y and Z → friction fit
//  • 90° V-groove on inner face (-Y for link6, +Y for link7)
//    sized for 13 mm tube: groove_width=13 mm, depth≈2.7 mm
//  • Mirrored in Y for link7 (inner face = +Y)
// ============================================================

// ── USER PARAMETERS ─────────────────────────────────────────

tube_od       = 13.0;   // target tube outer diameter (mm)
clearance     = 0.25;   // blade fit clearance (mm) — reduce if loose
wall          = 2.2;    // min wall around blade (mm)
clip_lip      = 0.8;    // snap-fit undercut depth on outer Y face (mm)
groove_angle  = 90;     // V-groove included angle (deg) — 90° = self-centering
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
tube_r       = tube_od / 2;
groove_half  = tan(groove_angle/2) * tube_r;   // half-width at groove mouth
groove_depth = tube_r * (1/sin(groove_angle/2) - 1); // tube center height
// For 90°: groove_half=6.5 mm, groove_depth≈2.69 mm

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

// 90° V-groove running full length on the inner -Y face
// The groove is centered in Z, open toward -Y
module v_groove() {
    // Prism: ▽ cross-section, extruded along X
    // At each X position the groove mouth width = 2*groove_half
    // and depth = groove_depth
    // We cut it slightly wider than calculated to ensure full tube contact
    gw = groove_half * 2 + 0.5;   // groove mouth width (Y)
    gd = groove_depth + 0.4;      // groove depth (into insert, Z direction... wait)

    // The V opens toward -Y (inner face).
    // We translate so the groove sits at the -Y face surface.
    hull()
        for (i = [0:N]) {
            x = X_START + i * INS_LEN / N;
            // -Y face is at y = -(bhy(x) + wall + clearance)
            face_y = -(bhy(x) + wall + clearance);
            translate([x, face_y + gd, 0])
                // Thin wedge: wide in Y, deep in -Y, zero in Z center
                rotate([0, 90, 0])
                    cylinder(r=0.01, h=0.01, center=true, $fn=3);
        }
    // Simpler approach: just use a linear_extrude-like approach via hull
    // Actually let's do a proper swept prism:
    linear_extrude_v_groove_inner();
}

// V-groove as a swept cut: separate module for clarity
module linear_extrude_v_groove_inner() {
    // Use minkowski or simple hull of wedge shapes per slice
    gw = groove_half * 2 + 0.5;
    gd = groove_depth + 0.5;

    hull()
        for (i = [0:N]) {
            x = X_START + i * INS_LEN / N;
            face_y = -(bhy(x) + wall + clearance);   // inner face -Y
            // The V tip is deepest inside the body (toward +Y)
            // The V mouth is at the face_y surface (outermost -Y)
            translate([x, 0, 0]) {
                // Mouth corners
                translate([0, face_y, -gw/2])
                    cube([0.01, 0.01, 0.01]);
                translate([0, face_y, +gw/2])
                    cube([0.01, 0.01, 0.01]);
                // V tip
                translate([0, face_y + gd, 0])
                    cube([0.01, 0.01, 0.01]);
            }
        }
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
        linear_extrude_v_groove_inner();  // V-groove on -Y face
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
//  Orientation: lay flat — X along bed, V-groove face up
//  Layer h   : 0.15 mm for smooth V surface
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
//  V-GROOVE GEOMETRY (13 mm tube, 90° angle)
//  ──────────────────────────────────────────
//  groove mouth width : 13.0 mm
//  groove depth       : ~2.7 mm
//  tube contact angle : 45° from vertical on each side
//  → tube self-centers and cannot roll out during motion
// ============================================================
