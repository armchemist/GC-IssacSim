// =====================================================================
//  OMX_F gripper finger sleeve — slide-on cover
//  Fits over the fingertip blade (finger-local x = 22..65 mm).
//  Open end pushes onto the finger from the tip side and slides toward
//  the housing until seated.
//
//  variant : "vgroove" (cradle for cylinders, Φ4..16 mm)
//          : "cup"     (concave dimples for spheres / small parts)
//  mirror_y: false = link6 (motorized side)
//            true  = link7 (gear side)   — mirrored pair
//
//  Print suggestion: PLA/PETG, 0.2 mm layer, 4 walls, 30% infill.
//  Print orientation: lay flat on +Z face (grip pad facing up).
//  If too tight, increase `clearance` by 0.1. If too loose, decrease.
// =====================================================================

variant   = "vgroove";   // "vgroove" | "cup"
mirror_y  = false;

clearance = 0.4;         // gap between sleeve cavity and finger (per side)
wall      = 1.6;         // shell wall thickness
$fn       = 80;

// ---------------------------------------------------------------------
// Blade outer envelope (symmetrized, derived from STL cross-sections
// of follower_07_gripper_motorized.stl over finger-local x = 22..65 mm).
// Format: [x_from_sleeve_base, half_width_Y, half_height_Z]
// ---------------------------------------------------------------------
profile = [
  [ 0.0, 18.5, 5.0],
  [ 6.0, 16.5, 3.8],
  [14.0, 14.0, 3.2],
  [24.0, 11.0, 3.5],
  [33.0,  8.0, 3.2],
  [40.0,  7.5, 1.6],
  [43.0,  7.0, 1.2],
];
N = len(profile);
L = profile[N-1][0];        // total sleeve length along finger axis

// ---------------------------------------------------------------------
// Helpers — tapered solid built by chained hulls of thin slabs
// ---------------------------------------------------------------------
module slab(i, ey, ez) {
  s = profile[i];
  translate([s[0], 0, 0])
    cube([0.02, 2*(s[1]+ey), 2*(s[2]+ez)], center=true);
}
module taper(ey, ez) {
  for (i = [0 : N-2]) hull() { slab(i, ey, ez); slab(i+1, ey, ez); }
}

// ---------------------------------------------------------------------
// Shell = outer taper − inner cavity (cavity opens at x = 0)
// ---------------------------------------------------------------------
module shell() {
  difference() {
    taper(clearance + wall, clearance + wall);
    // base opening: cut through x = 0 face
    translate([-3, 0, 0])
      cube([3.02,
            2*(profile[0][1] + clearance),
            2*(profile[0][2] + clearance)], center=true);
    // inner cavity matching blade with clearance
    taper(clearance, clearance);
  }
}

// ---------------------------------------------------------------------
// Grip pad on −Y face (the "inner" face that meets the partner finger
// for link6; mirrored for link7 via the top-level mirror).
// ---------------------------------------------------------------------
pad_len = 34;
pad_h   = 14;       // Z extent
pad_thk = 4.5;      // protrusion in −Y from outer wall
pad_x0  = 4;

pad_y_attach = -(profile[0][1] + clearance + wall);  // pad's +Y face (into shell)
pad_y_grip   = pad_y_attach - pad_thk;               // pad's −Y face (gripping surface)

module pad_block() {
  // overlap +1 mm into shell so the union is robust
  translate([pad_x0, pad_y_grip, -pad_h/2])
    cube([pad_len, pad_thk + 1.0, pad_h]);
}

// V-groove: triangular notch running along Z, centered along X on the pad.
// Cylinder lies vertically (along Z) and seats in the V.
module v_cutter() {
  groove_w = 9.0;     // width at the grip surface
  groove_d = 2.8;     // depth into pad
  translate([pad_x0 + pad_len/2, pad_y_grip, -pad_h/2 - 2])
    linear_extrude(height = pad_h + 4)
      polygon([
        [-groove_w/2, 0     ],   // left lip on grip surface
        [ groove_w/2, 0     ],   // right lip
        [ 0,          groove_d]  // apex, inward into pad
      ]);
}

// Cup: two hemispherical dimples on grip face for small spheres / parts.
module cup_cutter() {
  r_big   = 4.5;   // ~Φ9 cavity → holds Φ6–10 mm objects
  r_small = 3.0;   // ~Φ6 cavity → holds Φ3–6 mm objects
  // sphere center sits ON the grip surface → cuts a hemisphere into the pad
  translate([pad_x0 + 11, pad_y_grip, 0]) sphere(r = r_big);
  translate([pad_x0 + 24, pad_y_grip, 0]) sphere(r = r_small);
}

// ---------------------------------------------------------------------
// Assembly
// ---------------------------------------------------------------------
module sleeve() {
  difference() {
    union() {
      shell();
      pad_block();
    }
    if (variant == "vgroove") v_cutter();
    else if (variant == "cup") cup_cutter();
  }
}

// Mirror for link7 if requested
if (mirror_y) mirror([0, 1, 0]) sleeve();
else sleeve();
