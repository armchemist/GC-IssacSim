// ============================================================
//  OMX_F Gripper Finger Sleeve
//  Fits link6 (motorized) AND link7 (gear) — blade zone only
//  Blade X range: 22 mm → 65 mm  (finger-local frame)
//  Source dimensions: OMX_F gripper finger spec sheet
// ============================================================

// ── USER PARAMETERS ─────────────────────────────────────────

// Wall thickness around the blade (mm)
wall = 1.8;

// Extra clearance added to every cross-section (mm, tweak for print fit)
clearance = 0.3;

// Grip surface texture: "smooth", "ridged", "dotted"
grip_texture = "ridged";

// Ridged texture settings (ignored if grip_texture != "ridged")
ridge_pitch = 4.0;   // spacing between ridges (mm)
ridge_depth = 0.6;   // depth of each ridge (mm)

// Show the finger phantom (for visual check — disable before exporting)
show_phantom = false;

// Which finger to generate: "link6", "link7", or "both"
finger = "both";

// ── BLADE CROSS-SECTION DATA (from spec sheet) ───────────────
//   [ X,  half_Y, half_Z ]  — all mm, finger-local frame
blade_pts = [
    [ 22,  5.7, 19.4 ],
    [ 28,  4.2, 17.7 ],
    [ 36,  3.1, 15.5 ],
    [ 46,  2.8, 12.7 ],
    [ 55,  3.5, 10.3 ],
    [ 62,  3.5,  8.3 ],
    [ 65,  3.0,  7.6 ],
];

// ── DERIVED VALUES ────────────────────────────────────────────
sleeve_x_start = blade_pts[0][0];          // 22
sleeve_x_end   = blade_pts[len(blade_pts)-1][0];  // 65
sleeve_length  = sleeve_x_end - sleeve_x_start;   // 43

// ── HELPERS ───────────────────────────────────────────────────

// Linearly interpolate blade cross-section at a given X position
function blade_half_y(x) =
    let(i = search_segment(x))
    let(x0 = blade_pts[i][0],   y0 = blade_pts[i][1],
        x1 = blade_pts[i+1][0], y1 = blade_pts[i+1][1])
    y0 + (y1-y0) * (x-x0)/(x1-x0);

function blade_half_z(x) =
    let(i = search_segment(x))
    let(x0 = blade_pts[i][0],   z0 = blade_pts[i][2],
        x1 = blade_pts[i+1][0], z1 = blade_pts[i+1][2])
    z0 + (z1-z0) * (x-x0)/(x1-x0);

// Return the blade_pts index i such that blade_pts[i][0] <= x < blade_pts[i+1][0]
function search_segment(x, i=0) =
    (i >= len(blade_pts)-2) ? i :
    (x <= blade_pts[i+1][0]) ? i : search_segment(x, i+1);

// ── SLEEVE BODY ───────────────────────────────────────────────
// Built as a hull of scaled rectangles along X, then subtract the
// inner cavity (blade shape + clearance).

N_SLICES = 20;   // number of cross-section slices

module blade_slice(x, extra_y=0, extra_z=0) {
    hy = blade_half_y(x) + extra_y;
    hz = blade_half_z(x) + extra_z;
    translate([x, 0, 0])
        cube([0.01, hy*2, hz*2], center=true);
}

module sleeve_outer() {
    hull()
        for (i = [0:N_SLICES]) {
            x = sleeve_x_start + i * sleeve_length / N_SLICES;
            blade_slice(x, extra_y = wall + clearance,
                           extra_z = wall + clearance);
        }
}

module sleeve_inner_cavity() {
    // finger blade + clearance gap
    hull()
        for (i = [0:N_SLICES]) {
            x = sleeve_x_start + i * sleeve_length / N_SLICES;
            blade_slice(x, extra_y = clearance,
                           extra_z = clearance);
        }
}

// Entry chamfer — open the back end so the blade slides in easily
module entry_chamfer() {
    chamfer = 3.0;
    hull() {
        blade_slice(sleeve_x_start,
            extra_y = clearance + wall,
            extra_z = clearance + wall);
        blade_slice(sleeve_x_start,
            extra_y = clearance + wall + chamfer,
            extra_z = clearance + wall + chamfer);
        translate([sleeve_x_start - chamfer, 0, 0])
            blade_slice(sleeve_x_start,
                extra_y = clearance + wall + chamfer,
                extra_z = clearance + wall + chamfer);
    }
}

// Ridged grip texture on the outer −Y face (inner/gripping side)
module add_ridges() {
    n_ridges = floor(sleeve_length / ridge_pitch);
    for (i = [0:n_ridges-1]) {
        x = sleeve_x_start + (i + 0.5) * ridge_pitch;
        if (x < sleeve_x_end) {
            hy_out = blade_half_y(x) + wall + clearance;
            hz_out = blade_half_z(x) + wall + clearance;
            // Ridge sits on the −Y (inner/gripping) face
            translate([x, -hy_out, 0])
                rotate([0, 90, 0])
                    cylinder(d=ridge_depth*2, h=1.0, center=true, $fn=8);
        }
    }
}

// Full sleeve for one finger
module sleeve(mirror_y=false) {
    scale([1, mirror_y ? -1 : 1, 1])
    difference() {
        union() {
            sleeve_outer();
            if (grip_texture == "ridged") add_ridges();
        }
        sleeve_inner_cavity();
        entry_chamfer();
    }
}

// ── PHANTOM FINGER (visual check only) ───────────────────────
module finger_phantom() {
    color("cyan", 0.25)
    hull()
        for (i = [0:N_SLICES]) {
            x = sleeve_x_start + i * sleeve_length / N_SLICES;
            blade_slice(x);
        }
}

// ── RENDER ───────────────────────────────────────────────────
// link6: inner face = −Y  (no Y mirror needed)
// link7: inner face = +Y  (mirror in Y)

Y_OFFSET = 22;   // visual separation when showing both

if (finger == "link6") {
    sleeve(mirror_y=false);
    if (show_phantom) finger_phantom();

} else if (finger == "link7") {
    sleeve(mirror_y=true);
    if (show_phantom) finger_phantom();

} else { // "both" — side by side
    translate([0,  Y_OFFSET, 0]) {
        sleeve(mirror_y=false);
        if (show_phantom) finger_phantom();
    }
    translate([0, -Y_OFFSET, 0]) {
        sleeve(mirror_y=true);
        if (show_phantom) finger_phantom();
    }
}

// ============================================================
// USAGE NOTES
// ─────────────────────────────────────────────────────────────
// 1. Open in OpenSCAD ≥ 2021.01
// 2. Set `show_phantom = false` before exporting STL
// 3. Render (F6) → Export as STL (F7)
// 4. Print orientation: lay flat (X axis = print bed length)
// 5. Recommended: PETG or TPU for grip; 3–4 walls, 20 % infill
// 6. If sleeve is loose, increase `wall`; if too tight, increase `clearance`
// 7. Inner/outer face convention:
//      link6 "inner" (gripping) = local −Y  → sleeve open on −Y side
//      link7 "inner" (gripping) = local +Y  → mirrored
// ============================================================
