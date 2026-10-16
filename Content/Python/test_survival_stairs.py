"""Bounded PIE movement test for all four stair flights. Outputs JSON to Saved."""

import builtins
import json
import os
import time
import unreal

assert not hasattr(builtins, "_survival_stair_test"), "A stair test is already running."
world = unreal.EditorLevelLibrary.get_game_world()
assert world
pawn = unreal.GameplayStatics.get_player_pawn(world, 0)
assert pawn
tests = [
    (route, x, flight, start_y, base, end_y, top)
    for route, x in (("West", -475), ("East", 4975))
    for flight, start_y, base, end_y, top in (
        ("LowerToMain", 1800, -440, 3100, 0),
        ("MainToUpper", 3100, 0, 4400, 420),
    )
]
state = {
    "index": 0, "results": [], "started": time.monotonic(),
    "initial_position": pawn.get_actor_location(),
}
builtins._survival_stair_test = state


def begin():
    _, x, _, y, z, _, _ = tests[state["index"]]
    pawn.character_movement.stop_movement_immediately()
    pawn.set_actor_location(
        unreal.Vector(x, y, z + pawn.capsule_component.get_scaled_capsule_half_height() + 3),
        False, True,
    )
    state["started"] = time.monotonic()


def finish():
    pawn.character_movement.stop_movement_immediately()
    pawn.set_actor_location(state["initial_position"], False, True)
    unreal.unregister_slate_post_tick_callback(state["handle"])
    path = os.path.join(unreal.Paths.project_saved_dir(), "Automation", "SurvivalStairs.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as output:
        json.dump(state["results"], output, indent=2)
    unreal.log("Survival stair movement test finished: " + json.dumps(state["results"]))
    del builtins._survival_stair_test


def tick(delta):
    if not unreal.SystemLibrary.is_valid(pawn):
        unreal.log_error("Survival stair test aborted: PIE pawn no longer exists.")
        unreal.unregister_slate_post_tick_callback(state["handle"])
        del builtins._survival_stair_test
        return
    route, x, flight, start_y, base, end_y, top = tests[state["index"]]
    position = pawn.get_actor_location()
    elapsed = time.monotonic() - state["started"]
    if position.y >= end_y - 30 or elapsed > 15:
        feet = position.z - pawn.capsule_component.get_scaled_capsule_half_height()
        passed = position.y >= end_y - 30 and abs(feet - top) < 12
        state["results"].append({
            "route": route, "flight": flight, "passed": passed,
            "position": [position.x, position.y, position.z], "feet_z": feet,
            "expected_floor_z": top, "elapsed_seconds": elapsed,
        })
        if not passed:
            unreal.log_error("Stair traversal failed: " + json.dumps(state["results"][-1]))
        state["index"] += 1
        if state["index"] == len(tests):
            finish()
        else:
            begin()
        return
    pawn.add_movement_input(unreal.Vector(0, 1, 0), 1, True)


begin()
state["handle"] = unreal.register_slate_post_tick_callback(tick)
print("Started bounded movement tests for all four stair flights.")
