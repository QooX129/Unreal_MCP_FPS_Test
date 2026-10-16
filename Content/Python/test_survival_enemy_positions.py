"""Validate muzzle obstruction, AI repositioning/pursuit, and missing-player safety."""

import builtins
import json
import os
import time
import traceback
import unreal

assert not hasattr(builtins, "_survival_enemy_positions")
world = unreal.EditorLevelLibrary.get_game_world()
assert world
player = unreal.GameplayStatics.get_player_pawn(world, 0)
enemies = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.load_class(
    None, "/Game/Shooter/Blueprints/BP_SurvivalEnemy.BP_SurvivalEnemy_C"))
assert len(enemies) == 1 and enemies[0].get_actor_label() == "TEMP_EnemyValidation"
enemy = enemies[0]
block = next(a for a in unreal.GameplayStatics.get_all_actors_of_class(
    world, unreal.StaticMeshActor) if a.get_actor_label() == "TEMP_EnemyMuzzleBlock")
state = {"stage": "guard", "samples": [], "results": {}, "started": time.monotonic()}
builtins._survival_enemy_positions = state


def now():
    return unreal.SystemLibrary.get_game_time_in_seconds(enemy)


def get(name):
    return enemy.get_editor_property(name)


def place(actor, xyz):
    actor.character_movement.stop_movement_immediately()
    actor.set_actor_location(unreal.Vector(*xyz), False, True)
    actor.set_actor_rotation(unreal.Rotator(), False)


def stage(name):
    state["stage"] = name
    state["since"] = now()


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(state["handle"])
    block.set_actor_enable_collision(False)
    enemy.get_controller().stop_movement()
    enemy.character_movement.set_editor_property("max_walk_speed", 220.0)
    state["results"]["passed"] = error is None
    if error:
        state["results"]["error"] = error
        unreal.log_error("Enemy position test failed: " + error)
    path = os.path.join(unreal.Paths.project_saved_dir(), "Automation", "SurvivalEnemyPositions.json")
    with open(path, "w", encoding="utf-8") as output:
        json.dump({"results": state["results"], "samples": state["samples"]}, output, indent=2)
    del builtins._survival_enemy_positions
    unreal.log("Enemy position test finished: " + str(state["results"]))


enemy.get_controller().stop_movement()
enemy.character_movement.set_editor_property("max_walk_speed", 0.0)
enemy.character_movement.set_editor_property("rotation_rate", unreal.Rotator())
place(enemy, (2000, 2200, 93))
place(player, (2600, 2200, 93))
block.set_actor_enable_collision(True)
state["initial_shots"] = get("ShotsFired")
stage("guard")


def step():
    assert time.monotonic() - state["started"] < 40, "Position test timed out"
    elapsed = now() - state["since"]
    pos = enemy.get_actor_location()
    goal = get("MoveGoal")
    state["samples"].append({
        "time": now(), "stage": state["stage"], "state": get("AIState"),
        "visible": get("bCanSeePlayer"), "shots": get("ShotsFired"),
        "position": [pos.x, pos.y, pos.z], "goal": [goal.x, goal.y, goal.z],
    })
    if state["stage"] == "guard":
        if elapsed > .2:
            assert get("bCanSeePlayer"), "Low wall unexpectedly blocked eye-level vision"
            assert get("ShotsFired") == state["initial_shots"], "Barrel fired through low wall"
            assert get("AIState") == "Position"
        if elapsed > 1.8:
            state["results"]["visible_player_but_protruding_muzzle_cannot_fire"] = True
            enemy.character_movement.set_editor_property("max_walk_speed", 220.0)
            enemy.character_movement.set_editor_property("rotation_rate", unreal.Rotator(yaw=360))
            state["reposition_start"] = pos
            stage("reposition")
    elif state["stage"] == "reposition":
        if get("ShotsFired") > state["initial_shots"]:
            distance = unreal.MathLibrary.vector_distance(pos, state["reposition_start"])
            assert distance >= 50, distance
            assert get("AIState") == "Attack"
            state["results"]["repositioned_then_fired_cm"] = distance
            block.set_actor_enable_collision(False)
            enemy.get_controller().stop_movement()
            place(enemy, (800, 1500, 93))
            place(player, (2600, 1500, 93))
            state["default_fire_range"] = get("FireRange")
            enemy.set_editor_property("FireRange", 1400.0)
            state["chase_shots"] = get("ShotsFired")
            state["chase_start"] = enemy.get_actor_location()
            stage("pursuit")
        assert elapsed < 15, "No reachable firing position found around low cover"
    elif state["stage"] == "pursuit":
        distance = unreal.MathLibrary.vector_distance(pos, player.get_actor_location())
        if elapsed > .2 and distance > 1400:
            assert get("ShotsFired") == state["chase_shots"], "Fired beyond range"
        if get("ShotsFired") > state["chase_shots"]:
            assert distance <= 1400
            moved = unreal.MathLibrary.vector_distance(pos, state["chase_start"])
            assert moved >= 350, moved
            state["results"].update(pursuit_distance_cm=moved,
                                    firing_distance_cm=distance,
                                    firing_range_enforced=True,
                                    pursuit_fixture_fire_range_cm=1400.0,
                                    default_fire_range_cm=state["default_fire_range"])
            enemy.set_editor_property("FireRange", state["default_fire_range"])
            state["shots_before_missing"] = get("ShotsFired")
            player.set_actor_location(unreal.Vector(8000, 0, -5000), False, True)
            stage("missing-player")
        assert elapsed < 15, "Pursuit did not reach firing range"
    elif state["stage"] == "missing-player":
        if elapsed >= .5:
            assert unreal.GameplayStatics.get_player_pawn(world, 0) is None
            assert get("AIState") == "Idle"
            assert get("ShotsFired") == state["shots_before_missing"]
            assert enemy.get_velocity().length() < 1
            state["results"]["native_kill_z_missing_player_stops_enemy_safely"] = True
            finish()


def tick(delta):
    try:
        step()
    except Exception:
        finish(traceback.format_exc())


state["handle"] = unreal.register_slate_post_tick_callback(tick)
print("Started muzzle guard, repositioning, pursuit, and missing-player validation.")
