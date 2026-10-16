"""Bounded PIE tests for shared health, regeneration, death, and corpse cleanup.

Requires one unsaved BP_RifleTestTarget labelled TEMP_HealthValidationTarget.
Leaves the player dead for screenshot, input-shutdown, and Enter-restart checks.
"""

import builtins
import json
import os
import time
import unreal

assert not hasattr(builtins, "_survival_health_test")
world = unreal.EditorLevelLibrary.get_game_world()
assert world
pawn = unreal.GameplayStatics.get_player_pawn(world, 0)
pc = unreal.GameplayStatics.get_player_controller(world, 0)
health_class = unreal.load_class(None, "/Game/Shooter/Blueprints/BP_SurvivalHealth.BP_SurvivalHealth_C")
player_health = pawn.get_component_by_class(health_class)
targets = unreal.GameplayStatics.get_all_actors_of_class(
    world, unreal.load_class(None, "/Game/Shooter/Tests/BP_RifleTestTarget.BP_RifleTestTarget_C")
)
assert len(targets) == 1
target = targets[0]
enemy_health = target.get_component_by_class(health_class)
assert player_health and enemy_health
assert player_health.get_editor_property("Health") == 100
assert enemy_health.get_editor_property("Health") == 100
assert player_health.get_editor_property("bRegenerates")
assert not enemy_health.get_editor_property("bRegenerates")

state = {
    "stage": "delay", "started": time.monotonic(), "samples": [],
    "results": {"initial_player_hp": 100, "initial_enemy_hp": 100},
}
builtins._survival_health_test = state


def now():
    return unreal.SystemLibrary.get_game_time_in_seconds(pawn)


def damage(actor, amount):
    return unreal.GameplayStatics.apply_damage(actor, amount, pc, pawn, unreal.DamageType)


def value(component, name):
    return component.get_editor_property(name)


def finish(passed, error=None):
    unreal.unregister_slate_post_tick_callback(state["handle"])
    state["results"]["passed"] = passed
    if error:
        state["results"]["error"] = error
        unreal.log_error("Health test failed: " + error)
    path = os.path.join(unreal.Paths.project_saved_dir(), "Automation", "SurvivalHealth.json")
    with open(path, "w", encoding="utf-8") as output:
        json.dump({"results": state["results"], "samples": state["samples"]}, output, indent=2)
    builtins._survival_health_report = state
    del builtins._survival_health_test
    unreal.log("Health test finished: " + json.dumps(state["results"]))


damage(pawn, 40.5)
damage(target, 20)
assert value(player_health, "Health") == 59.5
assert value(enemy_health, "Health") == 80
state["first_damage_time"] = now()
last_damage = value(player_health, "LastDamageTime")
damage(pawn, -10)
damage(pawn, 0)
assert value(player_health, "Health") == 59.5
assert value(player_health, "LastDamageTime") == last_damage
state["results"]["fractional_damage_preserved"] = True
state["results"]["nonpositive_damage_does_not_heal_or_reset_delay"] = True


def step():
    t = now()
    hp = value(player_health, "Health")
    enemy_valid = unreal.SystemLibrary.is_valid(target)
    enemy_hp = value(enemy_health, "Health") if enemy_valid else None
    state["samples"].append({
        "time": t, "stage": state["stage"], "player_hp": hp, "enemy_hp": enemy_hp,
        "dead": value(player_health, "bDead"),
    })
    assert 0 <= hp <= 100
    if state["stage"] == "delay":
        assert hp == 59.5 and enemy_hp == 80
        if t - state["first_damage_time"] >= 3:
            damage(pawn, 10)
            state["second_damage_time"] = now()
            assert value(player_health, "Health") == 49.5
            state["stage"] = "regen-reset-delay"
    elif state["stage"] == "regen-reset-delay":
        elapsed = t - state["second_damage_time"]
        assert enemy_hp == 80
        if elapsed < 4.95:
            assert hp == 49.5, ("Regenerated too early", elapsed, hp)
        if hp > 49.5:
            assert elapsed >= 5, ("Delay not respected", elapsed)
            state["results"]["regen_delay_measured"] = elapsed
            state["results"]["damage_resets_regen_delay"] = True
            state["regen_baseline"] = (t, hp)
            state["stage"] = "regen-rate"
    elif state["stage"] == "regen-rate":
        assert enemy_hp == 80
        elapsed = t - state["regen_baseline"][0]
        if elapsed >= 1.5:
            rate = (hp - state["regen_baseline"][1]) / elapsed
            assert abs(rate - 10) < .25, rate
            state["results"]["regen_hp_per_second_measured"] = rate
            state["stage"] = "regen-cap"
    elif state["stage"] == "regen-cap":
        assert enemy_hp == 80, "Enemies must not regenerate."
        if t - state["second_damage_time"] >= 11:
            assert hp == 100, hp
            state["results"]["regen_capped_at_max"] = True
            state["results"]["enemy_does_not_regenerate"] = True
            target.set_actor_tick_enabled(True)
            damage(target, 1000)
            assert value(enemy_health, "Health") == 0 and value(enemy_health, "bDead")
            assert not target.is_actor_tick_enabled()
            assert not target.get_actor_enable_collision()
            state["enemy_death_time"] = t
            stamp = value(enemy_health, "LastDamageTime")
            damage(target, 1000)
            assert value(enemy_health, "LastDamageTime") == stamp
            assert 0 < target.get_life_span() <= 0.02
            state["stage"] = "corpse-cleanup"
    elif state["stage"] == "corpse-cleanup":
        if not enemy_valid:
            elapsed = t - state["enemy_death_time"]
            assert elapsed <= 0.1, elapsed
            state["results"]["enemy_cleanup_seconds_measured"] = elapsed
            state["results"]["enemy_death_stops_tick_and_collision"] = True
            damage(pawn, 1000)
            assert value(player_health, "Health") == 0 and value(player_health, "bDead")
            assert not pawn.is_actor_tick_enabled()
            assert not pawn.get_actor_enable_collision()
            assert pawn.character_movement.movement_mode == unreal.MovementMode.MOVE_NONE
            assert pawn.get_velocity().length() < .01
            assert pc.is_move_input_ignored() and pc.is_look_input_ignored()
            assert not pawn.get_editor_property("bReloading")
            assert not pawn.get_editor_property("bIsAiming")
            state["player_death_time"] = t
            state["death_shots"] = pawn.get_editor_property("ShotsFired")
            state["death_location"] = pawn.get_actor_location()
            state["stage"] = "no-resurrection"
    elif state["stage"] == "no-resurrection":
        assert hp == 0 and value(player_health, "bDead")
        assert pawn.get_editor_property("ShotsFired") == state["death_shots"]
        if t - state["player_death_time"] >= 6:
            state["results"]["player_death_disables_movement_and_combat"] = True
            state["results"]["dead_player_does_not_regenerate"] = True
            finish(True)


def tick(delta):
    if not unreal.SystemLibrary.is_valid(pawn):
        finish(False, "PIE ended before health tests completed.")
        return
    try:
        assert time.monotonic() - state["started"] < 55, "Health test timed out."
        step()
    except AssertionError as error:
        finish(False, repr(error))


state["handle"] = unreal.register_slate_post_tick_callback(tick)
print("Health tests started; expect completion in approximately 23 seconds, leaving player dead.")
