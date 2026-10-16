"""PIE-only range boundary, distant damage, and wall-occlusion regression."""

import builtins
import json
import os
import time
import traceback

import unreal

assert not hasattr(builtins, "_survival_enemy_range")
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
player = unreal.GameplayStatics.get_player_pawn(world, 0)
enemy_class = unreal.load_class(
    None, "/Game/Shooter/Blueprints/BP_SurvivalEnemy.BP_SurvivalEnemy_C")
enemy, = unreal.GameplayStatics.get_all_actors_of_class(world, enemy_class)
health_class = unreal.load_class(
    None, "/Game/Shooter/Blueprints/BP_SurvivalHealth.BP_SurvivalHealth_C")
player_bp = unreal.load_asset("/Game/Shooter/Blueprints/BP_SurvivalCharacter")
range_node = unreal.load_object(
    None, player_bp.get_path_name() + ":EventGraph.K2Node_CallFunction_11")
reach = float(range_node.find_input_pin("B").get_pin_value())
assert enemy.get_editor_property("SightRange") == reach
assert enemy.get_editor_property("FireRange") == reach
player.get_component_by_class(health_class).set_editor_property("bRegenerates", False)
enemy.set_editor_property("SpreadDegrees", 0.0)
enemy.get_controller().stop_movement()
enemy.get_controller().set_actor_tick_enabled(False)
enemy.get_controller().set_control_rotation(unreal.Rotator())
enemy.character_movement.set_editor_property("rotation_rate", unreal.Rotator())
for actor in (enemy, player):
    actor.character_movement.stop_movement_immediately()
    actor.character_movement.set_movement_mode(unreal.MovementMode.MOVE_FLYING)
    actor.character_movement.set_editor_property("max_fly_speed", 0.0)
    actor.set_actor_rotation(unreal.Rotator(), False)
enemy.set_actor_location(unreal.Vector(0, 0, 3000), False, True)
player.set_actor_location(unreal.Vector(reach + 100, 0, 3000), False, True)
block = next(a for a in unreal.GameplayStatics.get_all_actors_of_class(
    world, unreal.StaticMeshActor) if a.get_actor_label() == "Upper_Cover_00")
block.static_mesh_component.set_mobility(unreal.ComponentMobility.MOVABLE)
block.static_mesh_component.set_static_mesh(unreal.load_asset("/Engine/BasicShapes/Cube"))
block.set_actor_location(unreal.Vector(reach / 2, 0, 3000), False, True)
block.set_actor_scale3d(unreal.Vector(1, 20, 20))
block.set_actor_enable_collision(False)
state = {"stage": "outside", "started": time.monotonic(),
         "since": time.monotonic(), "results": {"matched_range_cm": reach}}
builtins._survival_enemy_range = state


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(state["handle"])
    state["results"]["passed"] = error is None
    if error:
        state["results"]["error"] = error
        unreal.log_error("Enemy range regression failed: " + error)
    path = os.path.join(unreal.Paths.project_saved_dir(), "Automation",
                        "SurvivalEnemyRange.json")
    with open(path, "w", encoding="utf-8") as output:
        json.dump(state["results"], output, indent=2)
    del builtins._survival_enemy_range


def tick(_delta):
    try:
        assert time.monotonic() - state["started"] < 12, state["stage"] + " timed out"
        elapsed = time.monotonic() - state["since"]
        shots = enemy.get_editor_property("ShotsFired")
        hp = player.get_component_by_class(health_class).get_editor_property("Health")
        if state["stage"] == "outside":
            assert shots == 0 and hp == 100
            if elapsed > .5:
                assert not enemy.get_editor_property("bCanSeePlayer")
                state["results"]["outside_range_rejected"] = True
                player.set_actor_location(unreal.Vector(reach - 100, 0, 3000), False, True)
                state.update(stage="inside", since=time.monotonic())
        elif state["stage"] == "inside":
            if elapsed > .3:
                assert enemy.get_editor_property("bCanSeePlayer")
            if hp < 100:
                assert shots == 1 and hp == 90, (shots, hp)
                distance = unreal.MathLibrary.vector_distance(
                    enemy.get_actor_location(), player.get_actor_location())
                assert abs(distance - (reach - 100)) < 1
                state["results"].update(damage_distance_cm=distance, damage=10,
                                        spread_disabled_only_in_fixture=True)
                block.set_actor_enable_collision(True)
                state.update(stage="wall", since=time.monotonic(), shots=shots, hp=hp)
        elif state["stage"] == "wall" and elapsed > .2:
            assert not enemy.get_editor_property("bCanSeePlayer")
            assert shots == state["shots"] and hp == state["hp"], "Fired through wall"
            if elapsed > 1.5:
                state["results"]["wall_blocks_long_range_fire"] = True
                finish()
    except Exception:
        finish(traceback.format_exc())


state["handle"] = unreal.register_slate_post_tick_callback(tick)
