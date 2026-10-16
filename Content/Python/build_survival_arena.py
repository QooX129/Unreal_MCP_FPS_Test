"""Part 1 only: expand the gameplay copy without changing the architectural map.

Run in Unreal with /Game/Shooter/Maps/Lvl_AtriumSurvival open.
Creates a 60 x 40 m right-hand arena, three floors, two stair routes, cover,
gallery openings, and review cameras. Navigation is built and tested separately.
"""

import json
import unreal

LEVEL = "/Game/Shooter/Maps/Lvl_AtriumSurvival"
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
editor = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
world = editor.get_editor_world()
assert world.get_outermost().get_name() == LEVEL
existing = actors.get_all_level_actors()
assert not any(str(a.get_folder_path()).startswith("Survival/") for a in existing)
cube = unreal.load_asset("/Engine/BasicShapes/Cube")
root = "/Game/Greybox/ConcreteAtrium/Materials/"
concrete = unreal.load_asset(root + "M_ConcreteGrey")
floor_mat = unreal.load_asset(root + "M_WalkwayGrey")
light = unreal.load_asset(root + "M_LightConcrete")
dark = unreal.load_asset(root + "M_RecessCharcoal")
assert all((cube, concrete, floor_mat, light, dark))
created = []


def box(name, x0, x1, y0, y1, z0, z1, material=concrete, folder="Structure"):
    assert x1 > x0 and y1 > y0 and z1 > z0, name
    actor = actors.spawn_actor_from_class(
        unreal.StaticMeshActor,
        unreal.Vector((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2),
    )
    assert actor, name
    actor.set_actor_label(name)
    actor.set_folder_path("Survival/" + folder)
    assert actor.static_mesh_component.set_static_mesh(cube)
    actor.static_mesh_component.set_material(0, material)
    actor.static_mesh_component.set_collision_profile_name("BlockAll")
    actor.set_actor_scale3d(unreal.Vector(
        (x1 - x0) / 100, (y1 - y0) / 100, (z1 - z0) / 100
    ))
    created.append(actor)
    return actor


def floor(name, x0, x1, y0, y1, z, folder="Floors"):
    return box(name, x0, x1, y0, y1, z - 30, z, floor_mat, folder)


def sign(name, words, xyz, yaw=0, size=32):
    actor = actors.spawn_actor_from_class(
        unreal.TextRenderActor, unreal.Vector(*xyz), unreal.Rotator(yaw=yaw)
    )
    assert actor
    actor.set_actor_label(name)
    actor.set_folder_path("Survival/Wayfinding")
    actor.text_render.set_text(words)
    actor.text_render.set_world_size(size)
    actor.text_render.set_text_render_color(unreal.Color(190, 205, 202, 255))
    created.append(actor)


# Remove only gallery closures and non-gameplay scale props in this copy.
removed = []
for actor in existing:
    name = actor.get_actor_label()
    if name in ("Gallery_BackWall", "Gallery_UpperBackWall") or name.startswith(
        ("Gallery_RecessPortal_", "ScaleFigure_180cm_")
    ):
        assert actors.destroy_actor(actor)
        removed.append(name)

# Ground level, main arena, and an upper perimeter gallery overlook the court.
floor("Arena_LowerFloor", -750, 5250, 1020, 5040, -440)
floor("Arena_MainCentralFloor", -200, 4700, 1020, 5040, 0)
for route, x0, x1 in (("West", -750, -200), ("East", 4700, 5250)):
    floor("Arena_Main_%s_North" % route, x0, x1, 1020, 2000, 0)
    floor("Arena_Main_%s_South" % route, x0, x1, 2960, 5040, 0)
    floor("Arena_Upper_%s_North" % route, x0, x1, 1020, 3260, 420)
    floor("Arena_Upper_%s_South" % route, x0, x1, 4220, 5040, 420)
floor("Arena_UpperWestInner", -200, 50, 1020, 5040, 420)
floor("Arena_UpperEastInner", 4450, 4700, 1020, 5040, 420)
floor("Arena_UpperNorth", 50, 4450, 1020, 1740, 420)
floor("Arena_UpperSouth", 50, 4450, 4340, 5040, 420)

box("Arena_BoundaryWest", -790, -750, 1020, 5080, -470, 980)
box("Arena_BoundaryEast", 5250, 5290, 1020, 5080, -470, 980)
box("Arena_BoundarySouth", -750, 5250, 5040, 5080, -470, 980)
for name, bounds in (
    ("West", (30, 50, 1740, 4340)),
    ("East", (4450, 4470, 1740, 4340)),
    ("North", (50, 4450, 1720, 1740)),
    ("South", (50, 4450, 4340, 4360)),
):
    box("UpperVoid_Parapet_" + name, *bounds, 420, 530)

# Two independent routes connect every floor; 34 cm treads, <=16 cm risers.
for route, x in (("West", -475), ("East", 4975)):
    for flight, y0, base, top in (
        ("LowerToMain", 2000, -440, 0),
        ("MainToUpper", 3260, 0, 420),
    ):
        rise = (top - base) / 28
        tread = 960 / 28
        for step in range(28):
            box(
                "Stairs_%s_%s_Step_%02d" % (route, flight, step + 1),
                x - 190, x + 190,
                y0 + step * tread, y0 + (step + 1) * tread,
                base - 30, base + (step + 1) * rise,
                light, "Stairs/" + route,
            )
            for side in (-1, 1):
                sx = x + side * 198
                box(
                    "Stairs_%s_%s_Rail_%02d_%d" % (route, flight, step, side),
                    sx - 8, sx + 8, y0 + step * tread, y0 + (step + 1) * tread,
                    base + step * rise, base + (step + 1) * rise + 100,
                    concrete, "Stairs/" + route,
                )
        # Keep capsule clearance on the cutout side of the floor.
        inside = x + (260 if route == "West" else -260)
        box(
            "StairWell_%s_%s_Guard" % (route, flight),
            inside - 10, inside + 10, y0, y0 + 960,
            top, top + 110, concrete, "Stairs/" + route,
        )
    sign("StairSign_" + route, "STAIRS\nLOWER / MAIN / UPPER", (x, 1850, 150), yaw=-90, size=24)

# A staggered set of walls breaks long shots while preserving a perimeter loop.
for name, x0, x1, y0, y1, z in (
    ("Main_WestScreen", 700, 740, 2000, 2900, 0),
    ("Main_EastScreen", 3630, 3670, 3000, 4000, 0),
    ("Lower_WestScreen", 1100, 1140, 2100, 3000, -440),
    ("Lower_EastScreen", 3300, 3340, 3150, 4100, -440),
):
    box(name, x0, x1, y0, y1, z, z + 250, folder="CombatCover")
for level, z in (("Main", 0), ("Lower", -440)):
    for i, (x, y, width, depth, height) in enumerate((
        (1350, 1650, 280, 120, 105),
        (3050, 1800, 260, 120, 160),
        (2100, 2800, 320, 140, 105),
        (1250, 3850, 260, 130, 160),
        (3250, 4400, 300, 120, 105),
        (4050, 2250, 200, 120, 105),
    )):
        box(
            "%s_Cover_%02d" % (level, i),
            x - width / 2, x + width / 2, y - depth / 2, y + depth / 2,
            z, z + height, light, "CombatCover",
        )
for i, (x, y) in enumerate(((1250, 1350), (3300, 1350), (1250, 4700), (3300, 4700))):
    box("Upper_Cover_%02d" % i, x - 120, x + 120, y - 45, y + 45, 420, 525, light, "CombatCover")

# Visible doorway frames mark the transition from the atrium to the combat hall.
for i, x in enumerate((-270, 1250, 2770, 4290)):
    for z, label in ((0, "Main"), (420, "Upper"), (-440, "Lower")):
        for side in (-1, 1):
            bx = x + side * 160
            box(
                "Portal_%s_%02d_Jamb_%d" % (label, i, side),
                bx - 10, bx + 10, 1020, 1060, z, z + 300, light, "Portals",
            )
        box("Portal_%s_%02d_Header" % (label, i), x - 170, x + 170, 1020, 1060, z + 300, z + 325, light, "Portals")

for i, (x, y) in enumerate(((350, 1500), (2250, 1600), (4200, 1600), (2250, 4700))):
    lamp = actors.spawn_actor_from_class(unreal.PointLight, unreal.Vector(x, y, -155))
    assert lamp
    lamp.set_actor_label("Lower_FillLight_%02d" % i)
    lamp.set_folder_path("Survival/Lighting")
    lamp.light_component.set_editor_property("mobility", unreal.ComponentMobility.MOVABLE)
    lamp.light_component.set_editor_property("intensity", 14000)
    lamp.light_component.set_editor_property("attenuation_radius", 2000)
    created.append(lamp)
sign("Arena_Title", "ATRIUM / COMBAT HALL", (2200, 5035, 700), yaw=-90, size=65)
sign("Arena_MainLabel", "MAIN  00", (-745, 1500, 170), size=30)
sign("Arena_LowerLabel", "LOWER  -01", (-745, 1500, -270), size=30)
sign("Arena_UpperLabel", "UPPER  +01", (-745, 1500, 590), size=30)

start = next(a for a in existing if a.get_actor_label() == "PlayerStart_AtriumEntry")
start.set_actor_location(unreal.Vector(0, 1450, 100), False, False)
start.set_actor_rotation(unreal.Rotator(yaw=45), False)
world.get_world_settings().set_editor_property(
    "default_game_mode",
    unreal.load_class(None, "/Game/ThirdPerson/Blueprints/BP_ThirdPersonGameMode.BP_ThirdPersonGameMode_C"),
)
world.get_world_settings().set_editor_property("kill_z", -1200)
for name, location, rotation, fov in (
    ("Camera_ArenaOverview", (6500, 7100, 4200), (-28, -137, 0), 75),
    ("Camera_ArenaMain", (200, 1500, 170), (0, 35, 0), 85),
):
    camera = actors.spawn_actor_from_class(
        unreal.CameraActor, unreal.Vector(*location),
        unreal.Rotator(pitch=rotation[0], yaw=rotation[1], roll=rotation[2]),
    )
    camera.set_actor_label(name)
    camera.set_folder_path("Survival/Cameras")
    camera.camera_component.set_editor_property("field_of_view", fov)
    created.append(camera)
view = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
key = view.get_active_viewport_config_key()
view.set_level_viewport_camera_info(
    unreal.Vector(6500, 7100, 4200), unreal.Rotator(pitch=-28, yaw=-137), key
)
view.set_level_viewport_fov(75, key)
view.editor_invalidate_viewports()
nav_volume = actors.spawn_actor_from_class(
    unreal.NavMeshBoundsVolume, unreal.Vector(2250, 2100, 100)
)
assert nav_volume
nav_volume.set_actor_label("NavMesh_AtriumSurvival")
nav_volume.set_folder_path("Survival/Navigation")
# The editor factory initializes the brush; raw World::SpawnActor does not.
_, nav_extent = nav_volume.get_actor_bounds(False)
assert min(nav_extent.x, nav_extent.y, nav_extent.z) > 0
nav_volume.set_actor_scale3d(unreal.Vector(
    3550 / nav_extent.x, 3300 / nav_extent.y, 900 / nav_extent.z
))
print(json.dumps({
    "level": LEVEL, "created": len(created), "removed_closures_and_props": removed,
    "arena_dimensions_m": [60, 40], "floor_heights_cm": [-440, 0, 420],
    "stair_routes": 2, "steps_per_flight": 28,
    "navigation_pending": True, "user_approval_pending": True,
}))
