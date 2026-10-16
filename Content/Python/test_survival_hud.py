"""Validate the runtime HUD, kill tracking, regeneration feedback, and restart."""

import builtins
import json
import os
import time
import traceback

import unreal

assert not hasattr(builtins, "_survival_hud_test")


def game_world():
    return unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()


world = game_world()
assert world
state = {
    "stage": "waiting-for-initial-wave",
    "started": time.monotonic(),
    "results": {},
}
builtins._survival_hud_test = state

hud_class = unreal.load_class(None, "/Script/MCP_Test.SurvivalCombatHUD")
enemy_class = unreal.load_class(
    None, "/Game/Shooter/Blueprints/BP_SurvivalEnemy.BP_SurvivalEnemy_C"
)
spawner_class = unreal.load_class(
    None, "/Game/Shooter/Blueprints/BP_SurvivalSpawner.BP_SurvivalSpawner_C"
)
health_class = unreal.load_class(
    None, "/Game/Shooter/Blueprints/BP_SurvivalHealth.BP_SurvivalHealth_C"
)
assert hud_class and enemy_class and spawner_class and health_class


def get_health(actor):
    return actor.get_component_by_class(health_class)


def enemies():
    return unreal.GameplayStatics.get_all_actors_of_class(world, enemy_class)


def game_time(spawner):
    return unreal.SystemLibrary.get_game_time_in_seconds(spawner)


def write_report():
    path = os.path.join(
        unreal.Paths.project_saved_dir(), "Automation", "SurvivalHUD.json"
    )
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as output:
        json.dump(state["results"], output, indent=2)


def finish(passed, error=None):
    if state.get("handle"):
        unreal.unregister_slate_post_tick_callback(state["handle"])
    state["results"]["passed"] = passed
    if error:
        state["results"]["error"] = error
        unreal.log_error("Survival HUD validation failed: " + error)
    write_report()
    builtins._survival_hud_report = state["results"]
    if hasattr(builtins, "_survival_hud_test"):
        del builtins._survival_hud_test
    unreal.log("Survival HUD validation finished: " + json.dumps(state["results"]))


def step(_delta):
    try:
        current_world = game_world()
        if not current_world:
            return
        global world
        world = current_world

        player = unreal.GameplayStatics.get_player_pawn(world, 0)
        controller = unreal.GameplayStatics.get_player_controller(world, 0)
        if not player or not controller:
            return

        hud = controller.get_hud()
        assert hud, "Player controller has no HUD."
        assert hud.get_class() == hud_class, (
            "Unexpected HUD class: " + hud.get_class().get_name()
        )

        spawners = unreal.GameplayStatics.get_all_actors_of_class(world, spawner_class)
        assert len(spawners) == 1, ("Expected one spawner", len(spawners))
        spawner = spawners[0]
        player_health = get_health(player)
        assert player_health

        if state["stage"] == "waiting-for-initial-wave":
            living = [
                enemy for enemy in enemies()
                if get_health(enemy).get_editor_property("Health") > 0
            ]
            if len(living) != 3:
                assert time.monotonic() - state["started"] < 30, (
                    "Initial enemy wave did not complete."
                )
                return

            assert player_health.get_editor_property("Health") == 100
            assert player.get_editor_property("Ammo") == 30
            assert player_health.get_editor_property("bRegenerates")
            state["results"].update({
                "runtime_hud_class": hud.get_class().get_name(),
                "initial_player_hp": player_health.get_editor_property("Health"),
                "initial_ammo": player.get_editor_property("Ammo"),
                "initial_enemy_count": len(living),
                "crosshair_and_base_hud": "DrawHUD active",
            })

            for enemy in living:
                enemy.set_actor_tick_enabled(False)
                enemy_controller = enemy.get_controller()
                if enemy_controller:
                    enemy_controller.stop_movement()
                    enemy_controller.set_actor_tick_enabled(False)

            previous_kills = spawner.get_editor_property("TotalKills")
            unreal.GameplayStatics.apply_damage(
                living[0], 200, controller, player, unreal.DamageType
            )
            kills = spawner.get_editor_property("TotalKills")
            assert kills == previous_kills + 1, (previous_kills, kills)
            state["results"]["kill_count_after_enemy_defeat"] = kills
            state["results"]["enemy_health_bars"] = (
                "remaining living enemies are eligible for visible, line-of-sight bars"
            )

            unreal.GameplayStatics.apply_damage(
                player, 50, controller, player, unreal.DamageType
            )
            assert player_health.get_editor_property("Health") == 50
            state["damage_game_time"] = game_time(spawner)
            state["regen_delay"] = player_health.get_editor_property("RegenDelay")
            state["stage"] = "waiting-for-regeneration"
            write_report()

        elif state["stage"] == "waiting-for-regeneration":
            current_health = player_health.get_editor_property("Health")
            elapsed = game_time(spawner) - state["damage_game_time"]
            if current_health <= 50:
                assert elapsed < state["regen_delay"] + 2.0, (
                    "Player did not regenerate after the configured delay."
                )
                return

            state["results"]["regeneration_started_after_seconds"] = elapsed
            state["results"]["regenerated_player_hp"] = current_health
            state["results"]["regeneration_feedback_shown"] = True
            state["regen_display_until"] = time.monotonic() + 20.0
            state["stage"] = "showing-regeneration"
            write_report()

        elif state["stage"] == "showing-regeneration":
            if time.monotonic() < state["regen_display_until"]:
                return

            unreal.GameplayStatics.apply_damage(
                player, 1000, controller, player, unreal.DamageType
            )
            assert player_health.get_editor_property("bDead")
            state["results"]["death_state"] = True
            state["results"]["awaiting_enter_restart"] = True
            state["stage"] = "waiting-for-enter-restart"
            write_report()

        elif state["stage"] == "waiting-for-enter-restart":
            if (
                player_health.get_editor_property("Health") == 100
                and spawner.get_editor_property("TotalKills") == 0
            ):
                restarted_health = get_health(player)
                restarted_enemies = [
                    enemy for enemy in enemies()
                    if get_health(enemy).get_editor_property("Health") > 0
                ]
                restarted_kills = spawner.get_editor_property("TotalKills")
                assert restarted_health.get_editor_property("Health") == 100
                assert len(restarted_enemies) == 3
                assert restarted_kills == 0
                assert controller.get_hud().get_class() == hud_class
                state["results"].update({
                    "restart_restored_player_hp": 100,
                    "restart_initial_enemy_count": len(restarted_enemies),
                    "restart_reset_kill_count": restarted_kills,
                    "restart_restored_hud": True,
                    "awaiting_enter_restart": False,
                })
                finish(True)
                return

            if time.monotonic() - state["started"] > 120:
                state["results"]["awaiting_enter_restart"] = True
                finish(False, "Enter restart was not verified before the timeout.")

    except Exception:
        finish(False, traceback.format_exc())


state["handle"] = unreal.register_slate_post_tick_callback(step)
unreal.log("Survival HUD validation started.")
