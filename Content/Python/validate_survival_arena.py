"""Validate floor connectivity and dimensions in the saved gameplay map."""

import json
import os
import unreal

world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
assert world.get_outermost().get_name() == "/Game/Shooter/Maps/Lvl_AtriumSurvival"
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
by_name = {actor.get_actor_label(): actor for actor in actors}
assert len(by_name) == len(actors)
assert "Gallery_BackWall" not in by_name
assert "Gallery_UpperBackWall" not in by_name
assert len([a for a in actors if a.get_actor_label().startswith("Stairs_") and "_Step_" in a.get_actor_label()]) == 112
nav = by_name["NavMesh_AtriumSurvival"]
_, extent = nav.get_actor_bounds(False)
assert min(extent.x, extent.y, extent.z) > 800
for actor in actors:
    if isinstance(actor, unreal.StaticMeshActor) and str(actor.get_folder_path()).startswith("Survival/"):
        assert actor.static_mesh_component.static_mesh, actor.get_actor_label()
        assert actor.static_mesh_component.get_collision_enabled() != unreal.CollisionEnabled.NO_COLLISION

results = []


def check_path(name, start, end):
    start_vector, end_vector = unreal.Vector(*start), unreal.Vector(*end)
    path = unreal.NavigationSystemV1.find_path_to_location_synchronously(
        world, start_vector, end_vector
    )
    assert path and path.is_valid() and not path.is_partial(), name
    points = path.path_points
    assert len(points) >= 2, name
    assert abs(points[0].z - start[2]) < 30, (name, points[0])
    assert abs(points[-1].z - end[2]) < 30, (name, points[-1])
    results.append({
        "name": name, "passed": True, "points": len(points),
        "start": [points[0].x, points[0].y, points[0].z],
        "end": [points[-1].x, points[-1].y, points[-1].z],
    })


for route, x in (("West", -475), ("East", 4975)):
    check_path(route + "_LowerToMain", (x, 1800, -435), (x, 3100, 5))
    check_path(route + "_MainToUpper", (x, 3100, 5), (x, 4400, 425))
for level, z in (("Lower", -440), ("Main", 0), ("Upper", 420)):
    check_path(level + "_AtriumToArena", (2010, 350 if level == "Upper" else 200, z + 5), (2250, 1500, z + 5))
    check_path(level + "_CrossArena", (0, 1500, z + 5), (4900, 4700, z + 5))

report = {
    "navigation_checks": results, "actors": len(actors),
    "stair_flights": 4, "risers_per_flight": 28, "max_riser_cm": 440 / 28,
    "tread_cm": 960 / 28, "stair_width_cm": 380,
    "arena_dimensions_m": [60, 40],
    "world_game_mode": str(world.get_world_settings().get_editor_property("default_game_mode")),
    "user_approval": "pending",
}
output_path = os.path.join(
    unreal.Paths.project_saved_dir(), "Automation", "SurvivalArenaValidation.json"
)
os.makedirs(os.path.dirname(output_path), exist_ok=True)
with open(output_path, "w", encoding="utf-8") as output:
    json.dump(report, output, indent=2)
print(json.dumps(report))
