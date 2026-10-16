"""Create editable Blueprint encounter-spawner tuning and death notification state."""

import unreal

root = "/Game/Shooter/Blueprints/"
enemy = unreal.load_asset(root + "BP_SurvivalEnemy")
spawner = unreal.load_asset(root + "BP_SurvivalSpawner")
if not spawner:
    factory = unreal.BlueprintFactory()
    factory.set_editor_property("parent_class", unreal.Actor)
    spawner = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        "BP_SurvivalSpawner", "/Game/Shooter/Blueprints", unreal.Blueprint, factory)
assert enemy and spawner
lib = unreal.BlueprintEditorLibrary
real = lib.get_member_variable_type(enemy, "ReactionDelay")
integer = lib.get_member_variable_type(enemy, "ShotsFired")
boolean = lib.get_member_variable_type(enemy, "bDeathReported")
vector = lib.get_member_variable_type(
    unreal.load_asset(root + "BP_SurvivalCharacter"), "AimPoint")

if not any(str(name).endswith(".bDeathReported")
           for name in lib.list_member_variable_names(enemy)):
    assert lib.add_member_variable(enemy, "bDeathReported", boolean)
    lib.set_blueprint_variable_category(enemy, "bDeathReported", "Combat")
lib.compile_blueprint(enemy)
assert enemy.status == unreal.BlueprintStatus.BS_UP_TO_DATE
unreal.get_default_object(enemy.generated_class()).set_editor_property(
    "bDeathReported", False)
assert unreal.EditorAssetLibrary.save_loaded_asset(enemy, only_if_is_dirty=False)

defaults = {
    "InitialPopulation": (integer, 3, True),
    "bInitialWaveStarted": (boolean, False, False),
    "TargetPopulation": (integer, 3, False),
    "AliveCount": (integer, 0, False),
    "TotalKills": (integer, 0, False),
    "KillsSinceRamp": (integer, 0, False),
    "SpawnAttempts": (integer, 0, False),
    "PreferredFloor": (integer, -1, False),
    "RampKills": (integer, 3, True),
    "MaxAttemptsBeforeVisible": (integer, 8, True),
    "ReplacementDelay": (real, 5.0, True),
    "SpawnInterval": (real, 0.5, True),
    "MinimumSpawnDistance": (real, 1200.0, True),
    "SpawnRadius": (real, 1300.0, True),
    "OffscreenDot": (real, 0.3, True),
    "NextSpawnTime": (real, 0.0, False),
    "SpawnOrigin": (vector, unreal.Vector(), False),
}
for name, (pin_type, default, editable) in defaults.items():
    if not any(str(item).endswith("." + name)
               for item in lib.list_member_variable_names(spawner)):
        assert lib.add_member_variable(spawner, name, pin_type)
        lib.set_blueprint_variable_category(spawner, name, "Encounter")
    if editable:
        lib.set_blueprint_variable_instance_editable(spawner, name, True)

if any(
    str(name).endswith(".MaxPopulation")
    for name in lib.list_member_variable_names(spawner)
):
    lib.set_blueprint_variable_instance_editable(spawner, "MaxPopulation", False)

lib.compile_blueprint(spawner)
assert spawner.status == unreal.BlueprintStatus.BS_UP_TO_DATE
cdo = unreal.get_default_object(spawner.generated_class())
for name, (_, default, _) in defaults.items():
    cdo.set_editor_property(name, default)
cdo.set_editor_property("SpawnOrigin", unreal.Vector(2250, 3000, 5))
cdo.set_actor_tick_interval(0.5)
assert unreal.EditorAssetLibrary.save_loaded_asset(spawner, only_if_is_dirty=False)
print("Created BP_SurvivalSpawner with uncapped population growth, a 5-second replacement delay, and enemy death guard.")
