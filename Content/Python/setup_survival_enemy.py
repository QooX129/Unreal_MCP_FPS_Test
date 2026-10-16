"""Create Part 5 enemy assets and editable tuning; no random spawner."""

import unreal

ROOT = "/Game/Shooter/Blueprints/"
lib = unreal.BlueprintEditorLibrary
bp = unreal.load_asset(ROOT + "BP_SurvivalEnemy")
if not bp:
    factory = unreal.BlueprintFactory()
    factory.set_editor_property("parent_class", unreal.load_asset(
        "/Game/ThirdPerson/Blueprints/BP_ThirdPersonCharacter").generated_class())
    bp = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        "BP_SurvivalEnemy", "/Game/Shooter/Blueprints", unreal.Blueprint, factory)
assert bp
assert not any(str(n).endswith(".SightRange") for n in lib.list_member_variable_names(bp))
real = lib.get_member_variable_type(unreal.load_asset(ROOT + "BP_SurvivalHealth"), "Health")
defaults = {
    "SightRange": 20000.0, "SightDotThreshold": .5, "FireRange": 20000.0,
    "ReactionDelay": 1.0, "EnemyDamage": 10.0, "ShotInterval": .45,
    "BurstPause": 2.0, "SpreadDegrees": 5.0, "SearchDuration": 8.0,
    "PatrolRadius": 900.0, "SearchRadius": 400.0, "PositionRadius": 650.0,
    "MoveInterval": 2.0, "NextMoveTime": 0.0, "NextShotTime": 0.0,
    "ReactionEndTime": 0.0, "SearchEndTime": -1.0, "LastShotTime": -100.0,
}
for name in defaults:
    assert lib.add_member_variable(bp, name, real)
    lib.set_blueprint_variable_category(bp, name, "Enemy AI")
    if name in (
        "SightRange", "SightDotThreshold", "FireRange", "ReactionDelay", "EnemyDamage",
        "ShotInterval", "BurstPause", "SpreadDegrees", "SearchDuration", "PatrolRadius",
        "SearchRadius", "PositionRadius", "MoveInterval",
    ):
        lib.set_blueprint_variable_instance_editable(bp, name, True)
for name in ("HomeLocation", "LastKnownLocation", "MoveGoal", "CandidatePosition"):
    assert lib.add_member_variable(bp, name, lib.get_member_variable_type(
        unreal.load_asset(ROOT + "BP_SurvivalCharacter"), "AimPoint"))
for name in ("bHadSight", "bCanSeePlayer"):
    assert lib.add_member_variable(bp, name, lib.get_basic_type_by_name("bool"))
for name in ("ShotsFired", "BurstShots", "MoveFailures"):
    assert lib.add_member_variable(bp, name, lib.get_basic_type_by_name("int"))
assert lib.add_member_variable(bp, "AIState", lib.get_basic_type_by_name("string"))
factory = unreal.BlueprintFactory()
factory.set_editor_property("parent_class", unreal.AIController)
controller = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
    "BP_SurvivalEnemyController", "/Game/Shooter/Blueprints", unreal.Blueprint, factory)
assert controller
lib.compile_blueprint(controller)
assert unreal.EditorAssetLibrary.save_loaded_asset(controller, only_if_is_dirty=False)
lib.compile_blueprint(bp)
cdo = unreal.get_default_object(bp.generated_class())
for name, value in defaults.items():
    cdo.set_editor_property(name, value)
cdo.set_editor_property("AIState", "Patrol")
cdo.set_editor_property("ai_controller_class", controller.generated_class())
cdo.set_editor_property("auto_possess_ai", unreal.AutoPossessAI.PLACED_IN_WORLD_OR_SPAWNED)
cdo.set_editor_property("use_controller_rotation_yaw", False)
cdo.character_movement.set_editor_property("max_walk_speed", 220)
cdo.character_movement.set_editor_property("orient_rotation_to_movement", True)
cdo.character_movement.set_editor_property("rotation_rate", unreal.Rotator(yaw=360))
cdo.set_actor_tick_interval(.1)

sub = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
slib = unreal.SubobjectDataBlueprintFunctionLibrary
handles = sub.k2_gather_subobject_data_for_blueprint(bp)
capsule = next(h for h in handles if slib.get_object(
    sub.k2_find_subobject_data_from_handle(h)).get_name() == "CollisionCylinder")


def component(name, cls, parent):
    handle, error = sub.add_new_subobject(unreal.AddNewSubobjectParams(
        parent_handle=parent, new_class=cls, blueprint_context=bp
    ))
    assert not str(error), str(error)
    assert sub.rename_subobject(handle, name)
    obj = slib.get_object_for_blueprint(sub.k2_find_subobject_data_from_handle(handle), bp)
    assert obj
    return handle, obj


_, health = component("HealthComponent", unreal.load_asset(ROOT + "BP_SurvivalHealth").generated_class(), handles[0])
health.set_editor_property("bRegenerates", False)
gun_handle, gun = component("EnemyRifle", unreal.SceneComponent, capsule)
gun.set_editor_property("relative_location", unreal.Vector(30, 18, 30))
cube = unreal.load_asset("/Engine/BasicShapes/Cube")
dark = unreal.load_asset("/Game/Greybox/ConcreteAtrium/Materials/M_RecessCharcoal")
for name, location, scale in (
    ("Receiver", (0, 0, 0), (.40, .08, .10)),
    ("Barrel", (35, 0, 0), (.35, .035, .035)),
    ("Stock", (-25, 0, 0), (.20, .07, .12)),
    ("Magazine", (0, 0, -10), (.10, .06, .17)),
):
    _, part = component("Enemy" + name, unreal.StaticMeshComponent, gun_handle)
    part.set_static_mesh(cube)
    part.set_material(0, dark)
    part.set_editor_property("relative_location", unreal.Vector(*location))
    part.set_editor_property("relative_scale3d", unreal.Vector(*scale))
    part.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
_, muzzle = component("EnemyMuzzle", unreal.SceneComponent, gun_handle)
muzzle.set_editor_property("relative_location", unreal.Vector(55, 0, 0))
_, flash = component("EnemyFlash", unreal.StaticMeshComponent, gun_handle)
flash.set_static_mesh(unreal.load_asset("/Engine/BasicShapes/Sphere"))
flash.set_material(0, unreal.load_asset("/Game/Shooter/Materials/M_RifleFlash"))
flash.set_editor_property("relative_location", unreal.Vector(57, 0, 0))
flash.set_editor_property("relative_scale3d", unreal.Vector(.12, .065, .065))
flash.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
flash.set_editor_property("cast_shadow", False)
flash.set_visibility(False)

material = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
    "M_EnemyGreybox", "/Game/Shooter/Materials", unreal.Material, unreal.MaterialFactoryNew()
)
assert material
color = unreal.MaterialEditingLibrary.create_material_expression(material, unreal.MaterialExpressionConstant3Vector)
color.set_editor_property("constant", unreal.LinearColor(.5, .12, .05, 1))
assert unreal.MaterialEditingLibrary.connect_material_property(color, "", unreal.MaterialProperty.MP_BASE_COLOR)
unreal.MaterialEditingLibrary.recompile_material(material)
assert unreal.EditorAssetLibrary.save_loaded_asset(material, only_if_is_dirty=False)
lib.compile_blueprint(bp)
cdo = unreal.get_default_object(bp.generated_class())
for index in range(cdo.mesh.get_num_materials()):
    cdo.mesh.set_material(index, material)
assert unreal.EditorAssetLibrary.save_loaded_asset(bp, only_if_is_dirty=False)
print("Enemy/controller/health/rifle created; graph authoring required.")
