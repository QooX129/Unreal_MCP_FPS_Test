import json
import math
import unreal

LEVEL = "/Game/Greybox/Lvl_ConcreteAtrium"
ROOT = "/Game/Greybox/ConcreteAtrium"
editor = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
assert editor.get_editor_world().get_path_name().startswith(LEVEL + ".")
assert not actors.get_all_level_actors(), "Build requires an empty level."

cube = unreal.load_asset("/Engine/BasicShapes/Cube")
materials = {}


def material(name, color, roughness=0.86):
    path = ROOT + "/Materials/" + name
    assert not unreal.EditorAssetLibrary.does_asset_exist(path), path
    asset = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        name, ROOT + "/Materials", unreal.Material, unreal.MaterialFactoryNew()
    )
    assert asset, path
    base = unreal.MaterialEditingLibrary.create_material_expression(
        asset, unreal.MaterialExpressionConstant3Vector, -250, 0
    )
    base.set_editor_property("constant", unreal.LinearColor(*color, 1))
    unreal.MaterialEditingLibrary.connect_material_property(
        base, "", unreal.MaterialProperty.MP_BASE_COLOR
    )
    rough = unreal.MaterialEditingLibrary.create_material_expression(
        asset, unreal.MaterialExpressionConstant, -250, 150
    )
    rough.set_editor_property("r", roughness)
    unreal.MaterialEditingLibrary.connect_material_property(
        rough, "", unreal.MaterialProperty.MP_ROUGHNESS
    )
    unreal.MaterialEditingLibrary.recompile_material(asset)
    materials[name] = asset
    return asset


concrete = material("M_ConcreteGrey", (0.43, 0.46, 0.44))
edge = material("M_LightConcrete", (0.57, 0.59, 0.56))
floor_mat = material("M_WalkwayGrey", (0.36, 0.39, 0.37))
dark = material("M_RecessCharcoal", (0.075, 0.09, 0.085))
seam = material("M_JointGrey", (0.19, 0.215, 0.20))
proxy_mat = material("M_PlantProxy", (0.20, 0.245, 0.18))
created = []


def box(name, xyz, size, mat=concrete, rotation=(0, 0, 0), folder="Structure"):
    actor = actors.spawn_actor_from_class(
        unreal.StaticMeshActor, unreal.Vector(*xyz),
        unreal.Rotator(pitch=rotation[0], yaw=rotation[1], roll=rotation[2])
    )
    assert actor, name
    actor.set_actor_label(name)
    actor.set_folder_path("Greybox/" + folder)
    comp = actor.static_mesh_component
    comp.set_static_mesh(cube)
    comp.set_material(0, mat)
    actor.set_actor_scale3d(unreal.Vector(*(v / 100 for v in size)))
    created.append(actor)
    return actor


def tilted(name, x, z, length, height, mat=concrete):
    y = -1110 + (z + 600) * 0.30
    return box(
        name, (x, y, z), (length, 50, height), mat,
        (0, 0, math.degrees(math.atan(0.30))), "InclinedFacade"
    )


# Walkway datum is Z=0; the atrium drops six metres below it.
box("Walkway_StructuralSlab", (2400, 280, -25), (6400, 640, 50), floor_mat, folder="Walkway")
box("Atrium_LowerFloor", (2400, -460, -650), (6400, 1420, 80), floor_mat, folder="Atrium")
box("Exterior_GroundProxy", (2400, -3600, -730), (12000, 7000, 80), edge, folder="Exterior")
box("Exterior_ContextScreen", (2400, -3600, 450), (12000, 80, 2400), edge, folder="Exterior")
box("Lower_RightRetainingWall", (2400, 625, -340), (6400, 50, 620))
box("Atrium_EndWall", (5640, -360, 400), (80, 1600, 2100))
box("Near_EntryLanding", (-850, 280, -25), (200, 640, 50), floor_mat, folder="Walkway")

for i in range(22):
    x = -750 + i * 300
    if x <= 5500:
        box("FloorJoint_Transverse_%02d" % i, (x, 280, 0.3), (1.5, 620, 0.6), seam, folder="Walkway/Joints")
for i, y in enumerate((95, 305, 515)):
    box("FloorJoint_Longitudinal_%02d" % i, (2400, y, 0.3), (6370, 1.4, 0.6), seam, folder="Walkway/Joints")

box("Atrium_ContinuousParapet", (2400, -58, 48), (6400, 36, 96), concrete, folder="Walkway")
box("Atrium_ParapetCoping", (2400, -58, 101), (6400, 44, 10), edge, folder="Walkway")
for i in range(15):
    box("CopingJoint_%02d" % i, (-700 + i * 450, -58, 106.2), (1.8, 43, 0.5), seam, folder="Walkway/Joints")

for i in range(8):
    x = -800 + i * 900
    tilted("InclinedWall_Pier_%02d" % i, x, 400, 365, 2200)
tilted("InclinedWall_EntryAbutment", -530, 400, 300, 2200)
tilted("InclinedWall_LowerBand", 2350, -610, 6660, 220)
tilted("InclinedWall_MidBand", 2350, 535, 6660, 300)
tilted("InclinedWall_UpperBand", 2350, 1290, 6660, 650)
for i in range(7):
    x = -350 + i * 900
    tilted("InclinedWall_WindowSill_%02d" % i, x, -350, 535, 110, edge)
    tilted("InclinedWall_WindowHead_%02d" % i, x, 305, 535, 95, edge)
    tilted("InclinedWall_UpperOpeningSill_%02d" % i, x, 760, 535, 110, edge)
for z in (-440, 405, 685, 1020, 1450):
    y = -1110 + (z + 600) * 0.30 + 28
    box("InclinedWall_HorizontalJoint_%d" % z, (2350, y, z), (6660, 1.8, 1.8), seam, folder="InclinedFacade/Joints")

for i in range(7):
    x = -150 + i * 900
    box("Gallery_Pier_%02d" % i, (x, 650, 270), (145, 230, 540), concrete, folder="Gallery")
    box("Gallery_PierFoot_%02d" % i, (x, 650, 14), (155, 245, 28), edge, folder="Gallery")
    box("Gallery_RecessFloor_%02d" % i, (x + 435, 895, -3), (720, 440, 36), floor_mat, folder="Gallery")
    box("Gallery_BackPanel_%02d" % i, (x + 435, 1110, 250), (720, 32, 500), concrete, folder="Gallery")
    box("Gallery_ShadowDoor_%02d" % i, (x + 705, 1087, 150), (115, 10, 300), dark, folder="Gallery")
    box("Gallery_PanelReveal_%02d" % i, (x + 68, 529, 270), (8, 7, 520), dark, folder="Gallery")
    for z in (170, 390):
        box("Gallery_FormworkJoint_%02d_%d" % (i, z), (x, 533.8, z), (144, 1.2, 1.5), seam, folder="Gallery/Joints")
    box("Gallery_Bench_%02d" % i, (x + 215, 905, 36), (190, 65, 24), edge, folder="Gallery")
    box("Gallery_BenchPlinth_%02d" % i, (x + 215, 905, 15), (135, 45, 30), concrete, folder="Gallery")

box("Gallery_UpperCantilever", (2400, 872, 565), (6500, 800, 65), concrete, folder="Gallery")
box("Gallery_UpperFascia", (2400, 492, 687), (6500, 40, 190), concrete, folder="Gallery")
box("Gallery_UpperCoping", (2400, 492, 788), (6500, 47, 12), edge, folder="Gallery")
box("Gallery_UpperBackWall", (2400, 1190, 1060), (6500, 50, 1000), concrete, folder="Gallery")
for i in range(15):
    box("Fascia_PanelJoint_%02d" % i, (-750 + i * 450, 470.8, 686), (1.8, 1.5, 180), seam, folder="Gallery/Joints")

for i in range(6):
    x = 100 + i * 1000
    box("Atrium_UpperCrossBeam_%02d" % i, (x, -75, 775), (60, 1200, 85), concrete, folder="Atrium/Beams")
    box("Atrium_MidCrossBeam_%02d" % i, (x + 350, -388, 370), (65, 680, 85), concrete, folder="Atrium/Beams")
    box("Atrium_LowerCrossBeam_%02d" % i, (x + 350, -555, -235), (65, 1000, 85), concrete, folder="Atrium/Beams")
for i in range(19):
    box("Roof_PergolaRib_%02d" % i, (-650 + i * 350, -40, 1490), (35, 1500, 42), concrete, folder="Roof")
box("Roof_LongitudinalEdge", (2400, 690, 1490), (6500, 48, 65), concrete, folder="Roof")

# Simple muted masses indicate hanging planting, rather than finished foliage.
for i, x in enumerate((500, 1450, 2400, 3350, 4300, 5150)):
    box("Planting_UpperTrough_%02d" % i, (x, 387, 600), (370, 135, 95), concrete, folder="PlantingProxies")
    for j in range(4):
        z = 680 - j * 100
        actor = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(x + j * 35, 330 - j * 45, z))
        assert actor
        actor.set_actor_label("Planting_HangingMass_%02d_%02d" % (i, j))
        actor.set_folder_path("Greybox/PlantingProxies")
        actor.static_mesh_component.set_static_mesh(cube)
        actor.static_mesh_component.set_material(0, proxy_mat)
        actor.set_actor_scale3d(unreal.Vector(2.0 - j * 0.35, 0.9 - j * 0.13, 1.05))
        created.append(actor)
    box("Planting_LowerBed_%02d" % i, (x, -780, -565), (430, 220, 90), proxy_mat, folder="PlantingProxies")

for i in range(1, 5):
    x = -150 + i * 900
    sign = actors.spawn_actor_from_class(unreal.TextRenderActor, unreal.Vector(x + 435, 1088, 320), unreal.Rotator(yaw=-90))
    assert sign
    sign.set_actor_label("Exhibition_Wayfinding_%02d" % i)
    sign.set_folder_path("Greybox/Wayfinding")
    sign.text_render.set_text("EXHIBITION\n%02d" % i)
    sign.text_render.set_world_size(30)
    sign.text_render.set_text_render_color(unreal.Color(48, 55, 51, 255))
    created.append(sign)

sun = actors.spawn_actor_from_class(unreal.DirectionalLight, unreal.Vector(1000, -1500, 1800), unreal.Rotator(pitch=-48, yaw=65))
sun.set_actor_label("Lighting_AtriumSun")
sun.set_folder_path("Greybox/Lighting")
sun.light_component.set_editor_property("mobility", unreal.ComponentMobility.MOVABLE)
sun.light_component.set_editor_property("intensity", 8.0)
sun.light_component.set_editor_property("light_source_angle", 4.0)
sun.light_component.set_editor_property("atmosphere_sun_light", True)
created.append(sun)

sky = actors.spawn_actor_from_class(unreal.SkyAtmosphere, unreal.Vector(0, 0, 0))
sky.set_actor_label("Lighting_SkyAtmosphere")
sky.set_folder_path("Greybox/Lighting")
created.append(sky)
skylight = actors.spawn_actor_from_class(unreal.SkyLight, unreal.Vector(2400, 0, 1400))
skylight.set_actor_label("Lighting_SoftSky")
skylight.set_folder_path("Greybox/Lighting")
skylight.light_component.set_editor_property("mobility", unreal.ComponentMobility.MOVABLE)
skylight.light_component.set_editor_property("real_time_capture", True)
skylight.light_component.set_editor_property("intensity", 2.2)
created.append(skylight)

pp = actors.spawn_actor_from_class(unreal.PostProcessVolume, unreal.Vector(0, 0, 0))
pp.set_actor_label("Lighting_Exposure")
pp.set_folder_path("Greybox/Lighting")
pp.set_editor_property("unbound", True)
settings = pp.get_editor_property("settings")
settings.set_editor_property("override_auto_exposure_min_brightness", True)
settings.set_editor_property("override_auto_exposure_max_brightness", True)
settings.set_editor_property("auto_exposure_min_brightness", 1.0)
settings.set_editor_property("auto_exposure_max_brightness", 1.0)
settings.set_editor_property("override_auto_exposure_bias", True)
settings.set_editor_property("auto_exposure_bias", 0.65)
pp.set_editor_property("settings", settings)
created.append(pp)

player = actors.spawn_actor_from_class(unreal.PlayerStart, unreal.Vector(-480, 280, 100), unreal.Rotator())
player.set_actor_label("PlayerStart_AtriumEntry")
player.set_folder_path("Greybox/Gameplay")
created.append(player)
camera = actors.spawn_actor_from_class(unreal.CameraActor, unreal.Vector(-610, 270, 170), unreal.Rotator(pitch=2, yaw=-1))
camera.set_actor_label("Camera_ReferenceView")
camera.set_folder_path("Greybox/Cameras")
camera.camera_component.set_editor_property("field_of_view", 83.0)
camera.camera_component.set_editor_property("aspect_ratio", 2.35)
created.append(camera)
unreal.EditorLevelLibrary.set_level_viewport_camera_info(unreal.Vector(-610, 270, 170), unreal.Rotator(pitch=2, yaw=-1))
assert unreal.EditorAssetLibrary.save_directory(ROOT, only_if_is_dirty=True, recursive=True)
print(json.dumps({"level": LEVEL, "created_actors": len(created), "materials": len(materials), "walkway_width_cm": 620, "atrium_drop_cm": 610, "length_cm": 6400, "camera": [-610, 270, 170]}))
