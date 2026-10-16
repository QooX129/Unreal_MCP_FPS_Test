"""Validate actual native enemy path following up every stair flight in PIE."""

import builtins
import json
import os
import time
import unreal

assert not hasattr(builtins, "_survival_enemy_stairs")
world = unreal.EditorLevelLibrary.get_game_world()
assert world
enemies = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.load_class(
    None, "/Game/Shooter/Blueprints/BP_SurvivalEnemy.BP_SurvivalEnemy_C"))
assert len(enemies) == 1 and enemies[0].get_actor_label() == "TEMP_EnemyValidation"
enemy = enemies[0]
controller = enemy.get_controller()
assert controller
initial = enemy.get_actor_location()
enemy.set_actor_tick_enabled(False)
tests = [
    (route, x, flight, y0, floor0, y1, floor1)
    for route, x in (("West", -475), ("East", 4975))
    for flight, y0, floor0, y1, floor1 in (
        ("LowerToMain", 1800, -440, 3100, 0),
        ("MainToUpper", 3100, 0, 4400, 420),
    )
]
state = {"index": 0, "results": [], "started": time.monotonic()}
builtins._survival_enemy_stairs = state


def begin():
    route, x, flight, y0, floor0, y1, floor1 = tests[state["index"]]
    controller.stop_movement()
    enemy.character_movement.stop_movement_immediately()
    enemy.set_actor_location(unreal.Vector(x, y0, floor0 + 93), False, True)
    enemy.character_movement.set_movement_mode(unreal.MovementMode.MOVE_WALKING)
    result = controller.move_to_location(
        unreal.Vector(x, y1, floor1 + 5), 25, False, True, True, False, None, False)
    state["request"] = str(result)
    state["started"] = time.monotonic()
    assert result != unreal.PathFollowingRequestResult.FAILED, (route, flight, result)


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(state["handle"])
    controller.stop_movement()
    enemy.set_actor_location(initial, False, True)
    enemy.set_actor_tick_enabled(True)
    report = {"passed": error is None and all(r["passed"] for r in state["results"]),
              "results": state["results"]}
    if error:
        report["error"] = error
        unreal.log_error("Enemy stair validation failed: " + error)
    path = os.path.join(unreal.Paths.project_saved_dir(), "Automation", "SurvivalEnemyStairs.json")
    with open(path, "w", encoding="utf-8") as output:
        json.dump(report, output, indent=2)
    del builtins._survival_enemy_stairs
    unreal.log("Enemy stair validation finished: " + str(report))


def tick(delta):
    try:
        assert unreal.SystemLibrary.is_valid(enemy), "Enemy disappeared during navigation"
        route, x, flight, y0, floor0, y1, floor1 = tests[state["index"]]
        position = enemy.get_actor_location()
        elapsed = time.monotonic() - state["started"]
        if abs(position.y - y1) < 45 or elapsed > 20:
            feet = position.z - enemy.capsule_component.get_scaled_capsule_half_height()
            passed = abs(position.y - y1) < 45 and abs(feet - floor1) < 12
            state["results"].append({
                "route": route, "flight": flight, "passed": passed,
                "position": [position.x, position.y, position.z],
                "feet_z": feet, "expected_floor": floor1, "elapsed": elapsed,
                "move_request": state["request"], "partial_paths_allowed": False,
            })
            assert passed, state["results"][-1]
            state["index"] += 1
            if state["index"] == len(tests):
                finish()
            else:
                begin()
    except Exception as error:
        finish(repr(error))


state["handle"] = unreal.register_slate_post_tick_callback(tick)
try:
    begin()
except Exception as error:
    finish(repr(error))
print("Started all four native enemy stair-path tests.")
