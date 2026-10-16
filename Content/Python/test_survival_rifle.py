"""Bounded PIE observation. Input is injected separately through control_editor.

Place a temporary BP_RifleTestTarget before PIE, then remove it before saving.
Results remain available in builtins._survival_rifle_report after observation.
"""

import builtins
import json
import os
import time
import unreal

assert not hasattr(builtins, "_survival_rifle_test"), "Rifle observer already running."
world = unreal.EditorLevelLibrary.get_game_world()
assert world
pawn = unreal.GameplayStatics.get_player_pawn(world, 0)
pc = unreal.GameplayStatics.get_player_controller(world, 0)
assert pawn and pc
targets = unreal.GameplayStatics.get_all_actors_of_class(
    world,
    unreal.load_class(None, "/Game/Shooter/Tests/BP_RifleTestTarget.BP_RifleTestTarget_C"),
)
assert len(targets) == 1, "Place exactly one temporary rifle test target before PIE."
target = targets[0]
assert target and target.get_world() == world
target.set_actor_scale3d(unreal.Vector(.6, 3, 3))
health_class = unreal.load_class(None, "/Game/Shooter/Blueprints/BP_SurvivalHealth.BP_SurvivalHealth_C")
health = target.get_component_by_class(health_class)
if health:
    # Keep the test receiver alive for sustained-fire measurements, only in PIE.
    health.set_editor_property("MaxHealth", 100000)
    health.set_editor_property("Health", 100000)
state = {
    "started": time.monotonic(), "samples": [], "target": target,
    "last": None, "duration": 240, "phase": "magazine",
}
builtins._survival_rifle_test = state


def sample():
    return {
        "time": unreal.SystemLibrary.get_game_time_in_seconds(pawn),
        "phase": state["phase"],
        "ammo": pawn.get_editor_property("Ammo"),
        "shots": pawn.get_editor_property("ShotsFired"),
        "reloading": pawn.get_editor_property("bReloading"),
        "reload_end": pawn.get_editor_property("ReloadEndTime"),
        "last_damage": target.get_editor_property("LastDamage"),
        "aiming": pawn.get_editor_property("bIsAiming"),
        "camera_fov": pawn.follow_camera.field_of_view,
        "walk_speed": pawn.character_movement.max_walk_speed,
        "flash_visible": next(
            c for c in pawn.get_components_by_class(unreal.StaticMeshComponent)
            if c.get_name() == "RifleFlash"
        ).is_visible(),
        "aim_origin": list(pawn.get_editor_property("AimOrigin").to_tuple()),
        "aim_point": list(pawn.get_editor_property("AimPoint").to_tuple()),
    }


def finish():
    unreal.unregister_slate_post_tick_callback(state["handle"])
    report = {"samples": state["samples"], "final": sample()}
    path = os.path.join(unreal.Paths.project_saved_dir(), "Automation", "SurvivalRifleRaw.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as output:
        json.dump(report, output, indent=2)
    builtins._survival_rifle_report = report
    del builtins._survival_rifle_test
    unreal.log("Rifle observation finished: " + path)


def tick(delta):
    if not unreal.SystemLibrary.is_valid(pawn):
        unreal.log_error("Rifle observer aborted because PIE stopped.")
        unreal.unregister_slate_post_tick_callback(state["handle"])
        del builtins._survival_rifle_test
        return
    value = sample()
    key = (value["phase"], value["ammo"], value["shots"], value["reloading"],
           value["last_damage"], value["aiming"], value["flash_visible"])
    if key != state["last"]:
        state["samples"].append(value)
        state["last"] = key
    if time.monotonic() - state["started"] >= state["duration"]:
        finish()


state["finish"] = finish
state["handle"] = unreal.register_slate_post_tick_callback(tick)
print("Rifle observer active for at most 240 seconds. LMB/R inputs can now be tested.")
