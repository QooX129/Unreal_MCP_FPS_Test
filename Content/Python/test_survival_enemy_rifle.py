"""Observe real player rifle input defeating a 100-HP enemy in exactly five hits."""

import builtins
import json
import os
import time
import traceback
import unreal

assert not hasattr(builtins, "_survival_enemy_rifle")
world = unreal.EditorLevelLibrary.get_game_world()
assert world
player = unreal.GameplayStatics.get_player_pawn(world, 0)
pc = unreal.GameplayStatics.get_player_controller(world, 0)
enemies = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.load_class(
    None, "/Game/Shooter/Blueprints/BP_SurvivalEnemy.BP_SurvivalEnemy_C"))
assert len(enemies) == 1 and enemies[0].get_actor_label() == "TEMP_EnemyValidation"
enemy = enemies[0]
health_class = unreal.load_class(
    None, "/Game/Shooter/Blueprints/BP_SurvivalHealth.BP_SurvivalHealth_C")
assert enemy.get_component_by_class(health_class).get_editor_property("Health") == 100
assert player.get_editor_property("Ammo") == 30
enemy.get_controller().stop_movement()
enemy.set_actor_tick_enabled(False)
enemy.character_movement.stop_movement_immediately()
enemy.set_actor_location(unreal.Vector(2600, 2265, 93), False, True)
enemy.set_actor_rotation(unreal.Rotator(yaw=180), False)
player.character_movement.stop_movement_immediately()
player.set_actor_location(unreal.Vector(2000, 2200, 93), False, True)
player.set_actor_rotation(unreal.Rotator(), False)
pc.set_control_rotation(unreal.Rotator())
state = {"started": time.monotonic(), "previous_hp": 100,
         "initial_shots": player.get_editor_property("ShotsFired"),
         "damage_steps": [], "results": {}, "samples": []}
builtins._survival_enemy_rifle = state


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(state["handle"])
    state["results"]["passed"] = error is None
    if error:
        state["results"]["error"] = error
        unreal.log_error("Player versus enemy rifle test failed: " + error)
    path = os.path.join(unreal.Paths.project_saved_dir(), "Automation", "SurvivalEnemyRifle.json")
    with open(path, "w", encoding="utf-8") as output:
        json.dump(state, output, indent=2, default=str)
    del builtins._survival_enemy_rifle
    unreal.log("Player versus enemy rifle test finished: " + str(state["results"]))


def tick(delta):
    try:
        assert time.monotonic() - state["started"] < 120, "No rifle-input result before timeout"
        t = unreal.SystemLibrary.get_game_time_in_seconds(player)
        if not unreal.SystemLibrary.is_valid(enemy):
            assert player.get_editor_property("ShotsFired") - state["initial_shots"] == 5
            assert state["previous_hp"] in (0, 20)
            assert len(state["damage_steps"]) in (4, 5)
            assert all(damage == 20 for damage in state["damage_steps"]), (
                        "Enemy disappeared before five confirmed rifle hits",
                        state["damage_steps"],
                    )
            assert player.get_editor_property("Ammo") == 25
            cleanup = t - state.get(
                "death_time", state.get("last_alive_sample_time", t)
            )
            assert cleanup <= 0.1, cleanup
            state["results"]["corpse_cleanup_seconds"] = cleanup
            state["results"].update(actual_player_rifle_hits=5, damage_per_hit=20,
                                    initial_enemy_hp=100, ammo_at_defeat=25)
            finish()
            return
        h = enemy.get_component_by_class(health_class)
        hp = h.get_editor_property("Health")
        shots = player.get_editor_property("ShotsFired") - state["initial_shots"]
        state["samples"].append({"time": t, "hp": hp, "shots": shots,
                                 "ammo": player.get_editor_property("Ammo")})
        state["last_alive_sample_time"] = t
        if hp != state["previous_hp"]:
            damage = state["previous_hp"] - hp
            assert damage == 20, damage
            state["damage_steps"].append(damage)
            state["previous_hp"] = hp
        if hp == 0 and "death_time" not in state:
            assert shots == 5 and state["damage_steps"] == [20] * 5, (shots, state["damage_steps"])
            assert h.get_editor_property("bDead")
            assert enemy.get_editor_property("AIState") == "Dead"
            assert player.get_editor_property("Ammo") == 25
            state["death_time"] = t
            state["results"].update(actual_player_rifle_hits=5, damage_per_hit=20,
                                    initial_enemy_hp=100, ammo_at_defeat=25)
    except Exception:
        finish(traceback.format_exc())


state["handle"] = unreal.register_slate_post_tick_callback(tick)
print("Enemy/player aligned. Hold left mouse to validate five real rifle hits.")
