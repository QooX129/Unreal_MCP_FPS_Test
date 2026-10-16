"""Bounded PIE perception, burst, search, damage, and death validation."""

import builtins
import json
import os
import time
import traceback
import unreal

assert not hasattr(builtins, "_survival_enemy_test")
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
ph = player.get_component_by_class(health_class)
eh = enemy.get_component_by_class(health_class)
assert ph.get_editor_property("Health") == 100
assert eh.get_editor_property("Health") == 100
assert not eh.get_editor_property("bRegenerates")
ph.set_editor_property("MaxHealth", 100.0)
ph.set_editor_property("bRegenerates", False)
state = {"stage": "behind", "samples": [], "results": {}, "start": time.monotonic()}
builtins._survival_enemy_test = state


def now():
    return unreal.SystemLibrary.get_game_time_in_seconds(enemy)


def get(name):
    return enemy.get_editor_property(name)


def place(actor, xyz, yaw=0):
    actor.character_movement.stop_movement_immediately()
    actor.set_actor_location(unreal.Vector(*xyz), False, True)
    actor.set_actor_rotation(unreal.Rotator(yaw=yaw), False)


def stage(name):
    state["stage"] = name
    state["since"] = now()


def finish(passed, error=None):
    unreal.unregister_slate_post_tick_callback(state["handle"])
    state["results"]["passed"] = passed
    if error:
        state["results"]["error"] = error
        unreal.log_error("Enemy validation failed: " + error)
    path = os.path.join(unreal.Paths.project_saved_dir(), "Automation", "SurvivalEnemy.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as output:
        json.dump({"results": state["results"], "samples": state["samples"]}, output, indent=2)
    builtins._survival_enemy_report = state
    del builtins._survival_enemy_test
    unreal.log("Enemy validation finished: " + str(state["results"]))


enemy.get_controller().stop_movement()
enemy.character_movement.set_editor_property("max_walk_speed", 0.0)
enemy.character_movement.set_editor_property("rotation_rate", unreal.Rotator())
place(enemy, (2000, 2200, 93))
place(player, (1400, 2200, 93))
assert enemy.get_editor_property("ShotsFired") == 0
unreal.GameplayStatics.apply_damage(enemy, 20, pc, player, unreal.DamageType)
stage("behind")


def step():
    ph = player.get_component_by_class(health_class)
    eh = enemy.get_component_by_class(health_class)
    t = now()
    elapsed = t - state["since"]
    shots = get("ShotsFired")
    visible = get("bCanSeePlayer")
    hp = ph.get_editor_property("Health")
    position = enemy.get_actor_location()
    state["samples"].append({
        "time": t, "stage": state["stage"], "state": get("AIState"),
        "visible": visible, "shots": shots, "player_hp": hp,
        "position": [position.x, position.y, position.z],
    })
    assert time.monotonic() - state["start"] < 50, "Enemy validation timed out"
    if state["stage"] == "behind":
        assert not visible and shots == 0, "Player behind enemy was detected"
        if elapsed >= .5:
            state["results"]["fov_rejects_player_behind"] = True
            place(enemy, (2000, 2200, 93))
            place(player, (2100 + get("SightRange"), 2200, 93))
            stage("range")
    elif state["stage"] == "range":
        assert not visible and shots == 0, "Player beyond SightRange was detected"
        if elapsed >= .5:
            state["results"]["sight_range_cm"] = get("SightRange")
            state["results"]["beyond_sight_range_rejected"] = True
            place(enemy, (2000, 2200, 93))
            place(player, (2600, 2200, 93))
            state["shot_times"] = []
            state["previous_shots"] = 0
            state["previous_hp"] = hp
            state["damage_steps"] = []
            stage("bursts")
    elif state["stage"] == "bursts":
        if visible and "acquired" not in state:
            state["acquired"] = t
        if shots != state["previous_shots"]:
            assert shots == state["previous_shots"] + 1
            state["shot_times"].append(get("LastShotTime"))
            state["previous_shots"] = shots
        if hp != state["previous_hp"]:
            state["damage_steps"].append(state["previous_hp"] - hp)
            state["previous_hp"] = hp
        if shots >= 9:
            times = state["shot_times"]
            reaction = times[0] - state["acquired"]
            assert get("ReactionDelay") - .1 <= reaction <= get("ReactionDelay") + .2, reaction
            intervals = [z - a for a, z in zip(times, times[1:])]
            for i, interval in enumerate(intervals):
                expected = 2 if i % 3 == 2 else .45
                assert expected - .03 <= interval <= expected + .16, intervals
            assert state["damage_steps"] and all(
                abs(d - 10) < .001 for d in state["damage_steps"]), state["damage_steps"]
            assert eh.get_editor_property("Health") == 80, "Enemy regenerated"
            state["results"].update(
                reaction_seconds=reaction, burst_intervals=intervals,
                actual_damage_steps=state["damage_steps"],
                enemy_does_not_regenerate=True,
            )
            state["last_known"] = get("LastKnownLocation")
            state["shots_at_loss"] = shots
            place(enemy, (500, 2400, 93))
            place(player, (1000, 2400, 93))
            stage("occluded")
    elif state["stage"] == "occluded":
        if elapsed > .15:
            assert not visible and shots == state["shots_at_loss"], "Firing through wall"
            assert get("AIState") == ("Search" if elapsed < 7.8 else get("AIState"))
            assert get("LastKnownLocation") == state["last_known"], "Tracked hidden player"
        if elapsed >= 8.3:
            assert get("AIState") == "Patrol", get("AIState")
            state["results"].update(wall_blocks_sight_and_damage=True,
                                    last_known_is_not_hidden_player=True,
                                    search_expires_to_patrol=True)
            place(enemy, (2000, 2200, 93))
            place(player, (2600, 2200, 93))
            state["reacquire_shots"] = shots
            stage("reacquire")
    elif state["stage"] == "reacquire":
        if shots > state["reacquire_shots"]:
            reaction = get("LastShotTime") - state["since"]
            assert get("ReactionDelay") - .05 <= reaction <= get("ReactionDelay") + .25, reaction
            state["results"]["reacquisition_reaction_seconds"] = reaction
            unreal.GameplayStatics.apply_damage(player, hp, pc, enemy, unreal.DamageType)
            state["shots_at_player_death"] = shots
            stage("player-dead")
    elif state["stage"] == "player-dead":
        if elapsed >= .5:
            assert get("ShotsFired") == state["shots_at_player_death"]
            assert get("AIState") == "Idle"
            state["results"]["player_death_stops_enemy_fire"] = True
            unreal.GameplayStatics.apply_damage(enemy, 80, pc, player, unreal.DamageType)
            assert eh.get_editor_property("Health") == 0
            assert eh.get_editor_property("bDead")
            assert get("AIState") == "Dead"
            assert not enemy.is_actor_tick_enabled()
            assert enemy.get_velocity().length() < 1
            state["results"]["enemy_death_stops_tick_and_movement"] = True
            state["death_time"] = t
            stage("cleanup")


def tick(delta):
    try:
        if state["stage"] == "cleanup":
            if not unreal.SystemLibrary.is_valid(enemy):
                state["results"]["corpse_cleanup_seconds"] = (
                    unreal.SystemLibrary.get_game_time_in_seconds(player) - state["death_time"])
                assert state["results"]["corpse_cleanup_seconds"] <= 0.1
                finish(True)
            return
        step()
    except Exception as error:
        finish(False, traceback.format_exc())


state["handle"] = unreal.register_slate_post_tick_callback(tick)
print("Started bounded enemy perception/combat validation.")
