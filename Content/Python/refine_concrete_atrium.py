"""Refine the saved atrium greybox using the eye-level and elevated references.

Run through Unreal's Python executor with Lvl_ConcreteAtrium open. The v1 backup
must exist. Only the previous greybox geometry is replaced; lighting and cameras
are retained. Dimensions are estimates from the images, in centimetres.
Reference: https://80.lv/articles/001agt-003qxl-005cg-setting-up-minimalistic-scenes-in-ue4
"""

import json
import math
import os
import unreal

LEVEL = "/Game/Greybox/Lvl_ConcreteAtrium"
ROOT = "/Game/Greybox/ConcreteAtrium"
subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
editor = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
viewports = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
assert editor.get_editor_world().get_path_name().startswith(LEVEL + ".")
backup_file = os.path.join(
    unreal.Paths.project_content_dir(), "Greybox", "Lvl_ConcreteAtrium_v1.umap"
)
assert os.path.isfile(backup_file) and os.path.getsize(backup_file) > 0

START, END = -1000, 5500
MID = (START + END) / 2
LENGTH = END - START
PITCH = 760
WINDOWS = [-180 + i * PITCH for i in range(8)]
SLOPE = 0.35
ANGLE = math.degrees(math.atan(SLOPE))
COS = 1 / math.sqrt(1 + SLOPE * SLOPE)
WALKWAY_WIDTH = 360
LOWER_FLOOR = -440
UPPER_FLOOR = 420

cube = unreal.load_asset("/Engine/BasicShapes/Cube")
sphere = unreal.load_asset("/Engine/BasicShapes/Sphere")
assert cube and sphere
materials = {
    name: unreal.load_asset(ROOT + "/Materials/" + name)
    for name in (
        "M_ConcreteGrey", "M_LightConcrete", "M_WalkwayGrey",
        "M_RecessCharcoal", "M_JointGrey", "M_PlantProxy",
    )
}
assert all(materials.values())
concrete = materials["M_ConcreteGrey"]
light = materials["M_LightConcrete"]
floor = materials["M_WalkwayGrey"]
dark = materials["M_RecessCharcoal"]
joint = materials["M_JointGrey"]
existing = subsystem.get_all_level_actors()
retained = {
    actor.get_actor_label(): actor for actor in existing
    if str(actor.get_folder_path()) in (
        "Greybox/Lighting", "Greybox/Cameras", "Greybox/Gameplay",
    )
}
assert all(name in retained for name in (
    "Camera_ReferenceView", "PlayerStart_AtriumEntry",
    "Lighting_AtriumSun", "Lighting_SoftSky", "Lighting_Exposure",
))
for actor in existing:
    if actor.get_actor_label() not in retained:
        assert str(actor.get_folder_path()).startswith("Greybox/"), actor.get_actor_label()

active_key = viewports.get_active_viewport_config_key()
if viewports.get_pilot_level_actor(active_key):
    viewports.eject_pilot_level_actor(active_key)
subsystem.clear_actor_selection_set()
for actor in existing:
    if actor.get_actor_label() not in retained:
        assert subsystem.destroy_actor(actor)

created = []


def box(name, center, size, mat=concrete, folder="Structure", roll=0, mesh=cube):
    actor = subsystem.spawn_actor_from_class(
        unreal.StaticMeshActor, unreal.Vector(*center), unreal.Rotator(roll=roll)
    )
    assert actor, name
    actor.set_actor_label(name)
    actor.set_folder_path("Greybox/" + folder)
    assert actor.static_mesh_component.set_static_mesh(mesh), name
    actor.static_mesh_component.set_material(0, mat)
    actor.set_actor_scale3d(unreal.Vector(*(v / 100 for v in size)))
    created.append(actor)
    return actor


def facade_y(z):
    return -790 + SLOPE * z


def wall_piece(name, x0, x1, bottom, top, mat=concrete, thickness=55):
    z = (bottom + top) / 2
    return box(
        name, ((x0 + x1) / 2, facade_y(z), z),
        (x1 - x0, thickness, (top - bottom) / COS), mat,
        "InclinedFacade", ANGLE,
    )


def text(name, words, center, size, yaw=180, folder="Wayfinding"):
    actor = subsystem.spawn_actor_from_class(
        unreal.TextRenderActor, unreal.Vector(*center), unreal.Rotator(yaw=yaw)
    )
    assert actor, name
    actor.set_actor_label(name)
    actor.set_folder_path("Greybox/" + folder)
    actor.text_render.set_text(words)
    actor.text_render.set_world_size(size)
    actor.text_render.set_text_render_color(unreal.Color(64, 75, 73, 255))
    created.append(actor)
    return actor


# Continuous floors also support the gallery recesses; no unintentional gaps.
box("Walkway_AndGallerySlab", (MID, 510, -20), (LENGTH, 1020, 40), floor, "Walkway")
box("Atrium_LowerFloor", (MID, -15, LOWER_FLOOR - 25), (LENGTH, 2110, 50), floor, "Atrium")
box("Atrium_WalkwayRetainingWall", (MID, -12, -235), (LENGTH, 24, 410))
box("Exterior_GroundProxy", (MID, -3300, -540), (14500, 6000, 80), light, "Exterior")
box("Exterior_ContextScreen", (MID, -2500, 350), (14500, 60, 1900), light, "Exterior")
box("Atrium_EndWall", (END + 30, 40, 230), (60, 2150, 1640))
box("Gallery_BackWall", (MID, 1040, 220), (LENGTH, 40, 440))

for i in range(27):
    x = START + i * 250
    if x < END:
        box("Paving_Transverse_%02d" % i, (x, 510, 0.2), (1, 1018, 0.4), joint, "Walkway/Joints")
for i, y in enumerate((120, 360, 600, 840)):
    box("Paving_Longitudinal_%02d" % i, (MID, y, 0.2), (LENGTH, 1, 0.4), joint, "Walkway/Joints")

# Keep the facade monolithic; sparse cutouts replace the original open colonnade.
for i, (bottom, top) in enumerate(((-560, -440), (-180, -90), (300, 610), (830, 1080))):
    wall_piece("InclinedWall_SolidBand_%02d" % i, START, END, bottom, top)
for row, bottom, top, width in (("Lower", -440, -180, 220), ("Main", -90, 300, 240), ("Upper", 610, 830, 100)):
    left = START
    for i, x in enumerate(WINDOWS):
        wall_piece("InclinedWall_%s_Solid_%02d" % (row, i), left, x - width / 2, bottom, top)
        for side in (-1, 1):
            edge_x = x + side * (width / 2 + 4)
            wall_piece(
                "Window_%s_%02d_Jamb_%d" % (row, i, side),
                edge_x - 4, edge_x + 4, bottom, top, light, 66,
            )
        left = x + width / 2
    wall_piece("InclinedWall_%s_End" % row, left, END, bottom, top)
for i, z in enumerate((-470, -130, 340, 590, 865)):
    box(
        "Facade_HorizontalJoint_%02d" % i,
        (MID, facade_y(z) + 29 / COS, z),
        (LENGTH, 0.8, 0.9), joint, "InclinedFacade/Joints", ANGLE,
    )
for i in range(9):
    x = START + i * PITCH
    if x < END:
        box(
            "Facade_VerticalJoint_%02d" % i, (x, facade_y(260) + 29 / COS, 260),
            (0.9, 0.8, 1640 / COS), joint, "InclinedFacade/Joints", ANGLE,
        )

# Actual narrow crosswalks align with the facade openings.
last = START
for i, x in enumerate(WINDOWS):
    opening_left, opening_right = x - 108, x + 108
    if opening_left > last:
        length = opening_left - last
        box("Walkway_Parapet_%02d" % i, ((last + opening_left) / 2, -20, 48), (length, 40, 96), folder="Walkway")
        box("Walkway_Coping_%02d" % i, ((last + opening_left) / 2, -20, 100), (length, 44, 8), light, "Walkway")
    last = opening_right
    for level, datum, width in (("Main", 0, 216), ("Lower", LOWER_FLOOR, 196)):
        far = facade_y(datum) - 20
        span = -far
        box("Bridge_%s_%02d_Deck" % (level, i), (x, far / 2, datum - 20), (width, span, 40), floor, "Atrium/Bridges")
        for side in (-1, 1):
            bx = x + side * (width / 2 - 8)
            box("Bridge_%s_%02d_Rail_%d" % (level, i, side), (bx, far / 2, datum + 48), (16, span, 96), folder="Atrium/Bridges")
            box("Bridge_%s_%02d_Cap_%d" % (level, i, side), (bx, far / 2, datum + 99), (19, span, 6), light, "Atrium/Bridges")
if last < END:
    box("Walkway_Parapet_End", ((last + END) / 2, -20, 48), (END - last, 40, 96), folder="Walkway")
    box("Walkway_Coping_End", ((last + END) / 2, -20, 100), (END - last, 44, 8), light, "Walkway")

# Rail openings provide passage between the lower crosswalks and lower gallery.
last = START
for i, x in enumerate(WINDOWS + [END + 98]):
    left = min(x - 98, END)
    if left > last:
        center = (last + left) / 2
        box("Lower_Parapet_%02d" % i, (center, -430, LOWER_FLOOR + 48), (left - last, 32, 96), folder="Atrium")
        box("Lower_Coping_%02d" % i, (center, -430, LOWER_FLOOR + 100), (left - last, 38, 8), light, "Atrium")
    last = x + 98

# Exhibition faces are on the near ends of deep wall fins, facing down the aisle.
for i in range(9):
    x = -650 + i * PITCH
    box("Gallery_ExhibitionFin_%02d" % i, (x, 690, 194), (150, 660, 388), folder="Gallery")
    box("Gallery_UpperFin_%02d" % i, (x, 720, 644), (150, 600, 388), folder="Gallery/Upper")
    box("Gallery_LowerFin_%02d" % i, (x, 690, -240), (150, 660, 400), folder="Gallery/Lower")
    for z in (120, 265):
        box("Gallery_FinJoint_%02d_%d" % (i, z), (x - 75.5, 690, z), (0.8, 658, 0.9), joint, "Gallery/Joints")
    box("Gallery_FinVerticalJoint_%02d" % i, (x - 75.5, 780, 194), (0.8, 0.9, 386), joint, "Gallery/Joints")
    if i > 0:
        text("Exhibition_Heading_%02d" % i, "EXHIBITION", (x - 76.5, 455, 302), 19)
        text("Exhibition_Number_%02d" % i, str(i), (x - 76.8, 455, 250), 51)
        for line in range(13):
            width = 225 - (line % 4) * 17
            box(
                "Exhibition_TextProxy_%02d_%02d" % (i, line),
                (x - 76.4, 680 - width / 2, 199 - line * 8),
                (0.7, width, 0.75), joint, "Wayfinding",
            )
    if i < 8:
        box("Gallery_FloorReveal_%02d" % i, (x + 95, 680, 0.35), (4, 620, 0.7), dark, "Gallery")
        box("Gallery_RecessPortal_%02d" % i, (x + 455, 1016, 135), (115, 6, 270), dark, "Gallery")
    if i in (2, 4, 6):
        box("Gallery_BenchSeat_%02d" % i, (x + 260, 520, 40), (145, 52, 14), light, "Gallery")
        box("Gallery_BenchBase_%02d" % i, (x + 260, 520, 17), (115, 38, 34), folder="Gallery")

box("Gallery_UpperFloor", (MID, 655, 404), (LENGTH, 730, 32), floor, "Gallery/Upper")
box("Gallery_UpperBalustrade", (MID, 290, 475), (LENGTH, 32, 110), folder="Gallery/Upper")
box("Gallery_UpperCoping", (MID, 290, 534), (LENGTH, 38, 8), light, "Gallery/Upper")
box("Gallery_UpperBackWall", (MID, 1040, 655), (LENGTH, 40, 470), folder="Gallery/Upper")
box("Gallery_UpperRoof", (MID, 670, 857), (LENGTH, 760, 38), folder="Gallery/Upper")
for i in range(22):
    x = START + i * 300
    if x < END:
        box("Upper_FasciaJoint_%02d" % i, (x, 273, 475), (0.9, 0.8, 108), joint, "Gallery/Joints")

for i, x in enumerate(WINDOWS):
    z = 548 if i % 2 == 0 else 885
    far = facade_y(z)
    box("Atrium_UpperCrossBeam_%02d" % i, (x, (far + 290) / 2, z), (65, 290 - far, 74), folder="Atrium/Beams")
for i in range(12):
    x = START + 100 + i * 570
    if x < END:
        box("Roof_SkylightRib_%02d" % i, (x, -130, 1050), (28, 1000, 34), folder="Roof")
box("Roof_LongitudinalEdge", (MID, 350, 1050), (LENGTH, 35, 45), folder="Roof")

# Sparse planting envelopes stay behind the upper rail, not across the aisle.
for i, x in enumerate((1200, 3000, 4650)):
    box("Planting_Trough_%02d" % i, (x, 375, 450), (250, 90, 60), folder="PlantingProxies")
    box("Planting_Envelope_%02d" % i, (x, 375, 494), (215, 65, 38), joint, "PlantingProxies")

figure = (420, 175)
for name, offset, size, mesh in (
    ("Head", (0, 0, 169), (22, 22, 22), sphere),
    ("Neck", (0, 0, 155), (12, 14, 12), cube),
    ("Torso", (0, 0, 120), (25, 42, 65), cube),
    ("LeftArm", (0, -30, 119), (13, 13, 57), cube),
    ("RightArm", (0, 30, 119), (13, 13, 57), cube),
    ("LeftLeg", (0, -12, 44), (17, 16, 82), cube),
    ("RightLeg", (0, 12, 44), (17, 16, 82), cube),
    ("LeftFoot", (6, -12, 5), (30, 18, 10), cube),
    ("RightFoot", (6, 12, 5), (30, 18, 10), cube),
):
    box(
        "ScaleFigure_180cm_" + name,
        (figure[0] + offset[0], figure[1] + offset[1], offset[2]),
        size, light, "ScaleReference", mesh=mesh,
    )

text("Atrium_BridgeWayfinding", "ASTRONOMY SPACE", (WINDOWS[1] - 118, -600, 57), 16)
retained["Lighting_AtriumSun"].set_actor_rotation(unreal.Rotator(pitch=-48, yaw=45), False)
retained["Lighting_AtriumSun"].light_component.set_editor_property("intensity", 6.0)
retained["Lighting_AtriumSun"].light_component.set_editor_property("light_source_angle", 4.0)
retained["Lighting_SoftSky"].light_component.set_editor_property("intensity", 3.1)
retained["Lighting_SoftSky"].light_component.set_light_color(unreal.LinearColor(1.0, 0.98, 0.93, 1))
exposure = retained["Lighting_Exposure"].get_editor_property("settings")
exposure.set_editor_property("auto_exposure_bias", 0.8)
retained["Lighting_Exposure"].set_editor_property("settings", exposure)
retained["PlayerStart_AtriumEntry"].set_actor_location(unreal.Vector(-800, 170, 100), False, False)

eye_camera = retained["Camera_ReferenceView"]
eye_camera.set_actor_location(unreal.Vector(-820, 180, 165), False, False)
eye_camera.set_actor_rotation(unreal.Rotator(pitch=1, yaw=-2), False)
eye_camera.camera_component.set_editor_property("field_of_view", 80)
eye_camera.camera_component.set_editor_property("constrain_aspect_ratio", False)
overview = retained.get("Camera_ElevatedReference")
if overview is None:
    overview = subsystem.spawn_actor_from_class(unreal.CameraActor, unreal.Vector())
    assert overview
    overview.set_actor_label("Camera_ElevatedReference")
    overview.set_folder_path("Greybox/Cameras")
overview.set_actor_location(unreal.Vector(-850, 160, 390), False, False)
overview.set_actor_rotation(unreal.Rotator(pitch=-13, yaw=-2), False)
overview.camera_component.set_editor_property("field_of_view", 80)
overview.camera_component.set_editor_property("constrain_aspect_ratio", False)

viewports.set_level_viewport_camera_info(
    overview.get_actor_location(), overview.get_actor_rotation(), active_key
)
viewports.set_level_viewport_fov(80, active_key)
viewports.editor_set_viewport_realtime(True)
viewports.editor_invalidate_viewports()
print(json.dumps({
    "level": LEVEL, "actors": len(subsystem.get_all_level_actors()),
    "walkway_clear_width_cm": WALKWAY_WIDTH, "lower_floor_cm": LOWER_FLOOR,
    "upper_floor_cm": UPPER_FLOOR, "main_bridge_count": len(WINDOWS),
    "facade_solid_fraction_at_eye_level": 1 - 240 / PITCH,
    "scale_figure_height_cm": 180, "backup": LEVEL + "_v1",
}))
