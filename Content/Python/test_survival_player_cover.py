"""PIE-only real-rifle test: protruding muzzle blocked, then clear shot restored."""

import builtins
import ctypes
import json
import os
import time
import traceback

import unreal

assert not hasattr(builtins, "_survival_player_cover")
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
player = unreal.GameplayStatics.get_player_pawn(world, 0)
pc = unreal.GameplayStatics.get_player_controller(world, 0)
enemy_class = unreal.load_class(
    None, "/Game/Shooter/Blueprints/BP_SurvivalEnemy.BP_SurvivalEnemy_C")
health_class = unreal.load_class(
    None, "/Game/Shooter/Blueprints/BP_SurvivalHealth.BP_SurvivalHealth_C")
enemy, = unreal.GameplayStatics.get_all_actors_of_class(world, enemy_class)
enemy.set_actor_tick_enabled(False)
enemy.get_controller().stop_movement()
enemy.get_controller().set_actor_tick_enabled(False)
enemy.character_movement.stop_movement_immediately()
enemy.set_actor_location(unreal.Vector(2600, 2265, 93), False, True)
player.set_actor_location(unreal.Vector(2000, 2200, 93), False, True)
player.set_actor_rotation(unreal.Rotator(), False)
pc.set_control_rotation(unreal.Rotator())
block = next(a for a in unreal.GameplayStatics.get_all_actors_of_class(
    world, unreal.StaticMeshActor) if a.get_actor_label() == "Upper_Cover_00")
block.static_mesh_component.set_mobility(unreal.ComponentMobility.MOVABLE)
block.set_actor_scale3d(unreal.Vector(.1, 2, .35))
block.set_actor_location(unreal.Vector(2070, 2200, 117.5), False, True)
block.set_actor_enable_collision(False)
state = {"stage": "capture", "started": time.monotonic(), "results": {}}
builtins._survival_player_cover = state
user32 = ctypes.windll.user32
unreal.WidgetLibrary.set_input_mode_game_only(pc)
unreal.WidgetLibrary.set_focus_to_game_viewport()
user32.mouse_event(8, 0, 0, 0, 0)


def finish(error=None):
    user32.mouse_event(4, 0, 0, 0, 0)
    user32.mouse_event(16, 0, 0, 0, 0)
    block.set_actor_enable_collision(False)
    unreal.unregister_slate_post_tick_callback(state["handle"])
    state["results"]["passed"] = error is None
    if error:
        state["results"]["error"] = error
        unreal.log_error("Player cover regression failed: " + error)
    path = os.path.join(unreal.Paths.project_saved_dir(), "Automation",
                        "SurvivalPlayerCover.json")
    with open(path, "w", encoding="utf-8") as output:
        json.dump(state["results"], output, indent=2)
    del builtins._survival_player_cover


def tick(_delta):
    try:
        eh = enemy.get_component_by_class(health_class)
        shots = player.get_editor_property("ShotsFired")
        assert time.monotonic() - state["started"] < 15, (
            "Cover test timed out.", state["stage"], shots,
            eh.get_editor_property("Health"))
        if state["stage"] == "capture":
            if time.monotonic() - state["started"] >= .15:
                user32.mouse_event(16, 0, 0, 0, 0)
                state["stage"] = "settling"
            return
        if state["stage"] == "settling":
            if time.monotonic() - state["started"] < .5:
                return
            mesh = player.get_component_by_class(unreal.SkeletalMeshComponent)
            hand = mesh.get_socket_location("hand_r")
            muzzle = player.get_editor_property("AimOrigin")
            center = (hand + muzzle) * .5
            block.set_actor_location(center, False, True)
            block.set_actor_enable_collision(True)
            assert min(hand.x, muzzle.x) < center.x < max(hand.x, muzzle.x)
            state["results"]["guard_between_hand_and_muzzle"] = True
            state["stage"] = "blocked"
            unreal.WidgetLibrary.set_input_mode_game_only(pc)
            unreal.WidgetLibrary.set_focus_to_game_viewport()
            user32.mouse_event(2, 0, 0, 0, 0)
        elif state["stage"] == "blocked" and shots >= 3:
            assert eh.get_editor_property("Health") == 100, "Rifle damaged through cover."
            state["results"]["blocked_shots"] = shots
            block.set_actor_enable_collision(False)
            state["stage"] = "clear"
        elif state["stage"] == "clear" and eh.get_editor_property("Health") < 100:
            assert eh.get_editor_property("Health") == 80
            state["results"]["clear_shot_damage"] = 20
            finish()
    except Exception:
        finish(traceback.format_exc())


state["handle"] = unreal.register_slate_post_tick_callback(tick)
