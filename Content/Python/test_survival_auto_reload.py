"""Observe real PIE fire/reload input; call state['finish'] after releasing input."""

import builtins
import json
import os
import time
import unreal

assert not hasattr(builtins, "_survival_auto_reload_test")
world = unreal.EditorLevelLibrary.get_game_world()
assert world
pawn = unreal.GameplayStatics.get_player_pawn(world, 0)
pawn.set_editor_property("Ammo", 0)
state = {"started": time.monotonic(), "samples": [], "last": None}
builtins._survival_auto_reload_test = state


def finish():
    unreal.unregister_slate_post_tick_callback(state["handle"])
    path = os.path.join(unreal.Paths.project_saved_dir(), "Automation", "SurvivalAutoReloadRaw.json")
    with open(path, "w", encoding="utf-8") as output:
        json.dump(state["samples"], output, indent=2)
    builtins._survival_auto_reload_samples = state["samples"]
    del builtins._survival_auto_reload_test
    print("Auto-reload observation saved: " + path)


def tick(delta):
    if not unreal.SystemLibrary.is_valid(pawn):
        unreal.log_error("Auto-reload observation aborted: PIE stopped.")
        unreal.unregister_slate_post_tick_callback(state["handle"])
        del builtins._survival_auto_reload_test
        return
    value = {
        "time": unreal.SystemLibrary.get_game_time_in_seconds(pawn),
        "ammo": pawn.get_editor_property("Ammo"),
        "shots": pawn.get_editor_property("ShotsFired"),
        "reloading": pawn.get_editor_property("bReloading"),
        "reload_end": pawn.get_editor_property("ReloadEndTime"),
    }
    key = (value["ammo"], value["shots"], value["reloading"], value["reload_end"])
    if key != state["last"]:
        state["samples"].append(value)
        state["last"] = key
    if time.monotonic() - state["started"] > 60:
        finish()


state["finish"] = finish
state["handle"] = unreal.register_slate_post_tick_callback(tick)
print("Observer started with zero ammo and no fire input; bounded to 60 seconds.")
