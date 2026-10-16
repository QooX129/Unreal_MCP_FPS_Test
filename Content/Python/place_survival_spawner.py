"""Replace the three fixed review enemies with the survival spawner."""

import unreal

actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
assert world.get_path_name() == "/Game/Shooter/Maps/Lvl_AtriumSurvival.Lvl_AtriumSurvival"

review_names = {
    "Enemy_Review_Main",
    "Enemy_Review_Lower",
    "Enemy_Review_Upper",
}
existing = actors.get_all_level_actors()
assert sum(a.get_actor_label() == "SurvivalSpawner" for a in existing) == 0
assert all(
    a.get_class().get_name() == "BP_SurvivalEnemy_C"
    for a in existing
    if a.get_actor_label() in review_names
)
for actor in existing:
    if actor.get_actor_label() in review_names:
        assert actors.destroy_actor(actor)

spawner_class = unreal.load_class(
    None, "/Game/Shooter/Blueprints/BP_SurvivalSpawner.BP_SurvivalSpawner_C"
)
assert spawner_class
spawner = actors.spawn_actor_from_class(
    spawner_class, unreal.Vector(2250, 3000, 0), unreal.Rotator()
)
assert spawner
spawner.set_actor_label("SurvivalSpawner")
spawner.set_folder_path("Survival/Spawner")

remaining = actors.get_all_level_actors()
assert not any(a.get_actor_label() in review_names for a in remaining)
assert sum(a.get_actor_label() == "SurvivalSpawner" for a in remaining) == 1
assert len(remaining) == 926, len(remaining)
assert unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
print("Saved one survival spawner in place of the three fixed review enemies.")
