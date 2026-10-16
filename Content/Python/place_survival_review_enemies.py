"""Replace only Part 5 validation fixtures with three fixed review enemies."""

import unreal

actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
assert world.get_path_name() == "/Game/Shooter/Maps/Lvl_AtriumSurvival.Lvl_AtriumSurvival"
existing = actors.get_all_level_actors()
placements = (
    ("Enemy_Review_Main", (1500, 2200, 93), 180),
    ("Enemy_Review_Lower", (2600, 1800, -347), 180),
    ("Enemy_Review_Upper", (4000, 4700, 513), -135),
)
assert not any(a.get_actor_label() in {p[0] for p in placements} for a in existing)
for actor in existing:
    if actor.get_actor_label() in ("TEMP_EnemyValidation", "TEMP_EnemyMuzzleBlock"):
        assert actors.destroy_actor(actor)
cls = unreal.load_class(None, "/Game/Shooter/Blueprints/BP_SurvivalEnemy.BP_SurvivalEnemy_C")
for label, xyz, yaw in placements:
    actor = actors.spawn_actor_from_class(cls, unreal.Vector(*xyz), unreal.Rotator(yaw=yaw))
    assert actor
    actor.set_actor_label(label)
    actor.set_folder_path("Survival/Enemies")
    assert actor.capsule_component.get_collision_response_to_channel(
        unreal.CollisionChannel.ECC_VISIBILITY) == unreal.CollisionResponseType.ECR_BLOCK
assert len(actors.get_all_level_actors()) == 928
assert unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
print("Saved three fixed review enemies, one per floor. No random spawning or replacement.")
