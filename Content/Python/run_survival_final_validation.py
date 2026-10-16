"""Run final regression checks in disposable PIE worlds, never saving fixtures."""

import builtins
import ctypes
from ctypes import wintypes
import json
import os
import time
import traceback

import unreal

assert not hasattr(builtins, "_survival_final_validation"), "Final validation is running."
assert not unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages(), "Save map edits first."
assert not unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages(), "Save asset edits first."
editor = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
assert not editor.get_game_world(), "Stop PIE before starting final validation."
root = unreal.Paths.project_dir()
output = os.path.join(unreal.Paths.project_saved_dir(), "Automation")
os.makedirs(output, exist_ok=True)
report_path = os.path.join(output, "SurvivalFinal.json")
health_class = unreal.load_class(
    None, "/Game/Shooter/Blueprints/BP_SurvivalHealth.BP_SurvivalHealth_C")
enemy_class = unreal.load_class(
    None, "/Game/Shooter/Blueprints/BP_SurvivalEnemy.BP_SurvivalEnemy_C")
spawner_class = unreal.load_class(
    None, "/Game/Shooter/Blueprints/BP_SurvivalSpawner.BP_SurvivalSpawner_C")
state = {"stage": "starting", "case": 0, "results": {}, "started": time.monotonic()}
builtins._survival_final_validation = state
user32 = ctypes.windll.user32
editor_window = user32.FindWindowW(None, "MCP_Test - Unreal Editor")
assert editor_window, "Unreal Editor window was not found."
performance = unreal.get_default_object(unreal.load_class(
    None, "/Script/UnrealEd.EditorPerformanceSettings"))
background_throttle = performance.get_editor_property("bThrottleCPUWhenNotForeground")
cases = [
    ("enemy_range", "test_survival_enemy_range.py", "_survival_enemy_range",
     "SurvivalEnemyRange.json"),
    ("stairs", "test_survival_stairs.py", "_survival_stair_test", "SurvivalStairs.json"),
    ("enemy_stairs", "test_survival_enemy_stairs.py", "_survival_enemy_stairs",
     "SurvivalEnemyStairs.json"),
    ("enemy_combat", "test_survival_enemy.py", "_survival_enemy_test", "SurvivalEnemy.json"),
    ("enemy_positions", "test_survival_enemy_positions.py", "_survival_enemy_positions",
     "SurvivalEnemyPositions.json"),
    ("rifle", "test_survival_enemy_rifle.py", "_survival_enemy_rifle",
     "SurvivalEnemyRifle.json"),
    ("player_cover", "test_survival_player_cover.py", "_survival_player_cover",
     "SurvivalPlayerCover.json"),
    ("spawner", "test_survival_spawner.py", "_survival_spawner_test", "SurvivalSpawner.json"),
    ("hud", "test_survival_hud.py", "_survival_hud_test", "SurvivalHUD.json"),
]


def write():
    with open(report_path, "w", encoding="utf-8") as target:
        json.dump({k: v for k, v in state.items() if k not in ("handle", "block")},
                  target, indent=2, default=str)


def run_script(name):
    path = os.path.join(root, "Content", "Python", name)
    namespace = {"__name__": "__survival_final_case__"}
    with open(path, encoding="utf-8") as source:
        exec(compile(source.read(), path, "exec"), namespace)


def health(actor):
    return actor.get_component_by_class(health_class)


def enemies(world):
    return unreal.GameplayStatics.get_all_actors_of_class(world, enemy_class)


def key(code):
    focus_window()
    user32.keybd_event(code, 0, 0, 0)
    user32.keybd_event(code, 0, 2, 0)


def fire(held):
    if held:
        focus_window()
    user32.mouse_event(2 if held else 4, 0, 0, 0, 0)


def aim(held):
    if held:
        focus_window()
    user32.mouse_event(8 if held else 16, 0, 0, 0, 0)


def focus_window():
    thread = ctypes.windll.kernel32.GetCurrentThreadId()
    foreground_thread = user32.GetWindowThreadProcessId(user32.GetForegroundWindow(), None)
    attached = thread != foreground_thread and user32.AttachThreadInput(
        thread, foreground_thread, True)
    try:
        user32.SetForegroundWindow(editor_window)
    finally:
        if attached:
            user32.AttachThreadInput(thread, foreground_thread, False)
    assert user32.GetForegroundWindow() == editor_window, "Input requires Unreal foreground focus."


def finish(error=None):
    fire(False)
    aim(False)
    unreal.unregister_slate_post_tick_callback(state["handle"])
    performance.set_editor_property("bThrottleCPUWhenNotForeground", background_throttle)
    if error:
        for _, _, marker, _ in cases:
            child = getattr(builtins, marker, None)
            if child:
                unreal.unregister_slate_post_tick_callback(child["handle"])
                delattr(builtins, marker)
    state["passed"] = error is None
    state["stage"] = "failed" if error else "complete"
    if error:
        state["error"] = error
        unreal.log_error("Survival final validation failed: " + error)
    write()
    builtins._survival_final_report = state
    del builtins._survival_final_validation
    if editor.get_game_world():
        levels.editor_request_end_play()
    unreal.log("Survival final validation " + state["stage"])


def spawn_block(world):
    actor = next(a for a in unreal.GameplayStatics.get_all_actors_of_class(
        world, unreal.StaticMeshActor) if a.get_actor_label() == "Upper_Cover_00")
    actor.static_mesh_component.set_mobility(unreal.ComponentMobility.MOVABLE)
    actor.set_actor_label("TEMP_EnemyMuzzleBlock")
    actor.static_mesh_component.set_static_mesh(unreal.load_asset("/Engine/BasicShapes/Cube"))
    actor.set_actor_location(unreal.Vector(2070, 2200, 117.5), False, True)
    actor.set_actor_scale3d(unreal.Vector(.1, 2, .35))
    actor.set_actor_enable_collision(False)
    return actor


def rifle_followup(world, player, pc):
    """Exercise manual reload and empty-held-fire reload through real input."""
    t = unreal.SystemLibrary.get_game_time_in_seconds(player)
    phase = state["input_stage"]
    ammo = player.get_editor_property("Ammo")
    shots = player.get_editor_property("ShotsFired")
    reloading = player.get_editor_property("bReloading")
    if phase == "finished":
        assert ammo == 25
        key(0x52)
        state["reload_started"] = t
        state["input_stage"] = "manual-reload"
        return False
    if phase == "manual-reload":
        elapsed = t - state["reload_started"]
        if elapsed < .15:
            return False
        if reloading:
            assert shots == 5 and ammo == 25
            return False
        assert 1.9 <= elapsed <= 2.25, elapsed
        assert ammo == 30
        state["results"]["manual_reload_seconds"] = elapsed
        state["input_stage"] = "full-magazine"
        state["shot_times"] = []
        state["previous_shots"] = shots
        fire(True)
        return False
    if phase == "full-magazine":
        if shots != state["previous_shots"]:
            assert shots == state["previous_shots"] + 1
            state["shot_times"].append(player.get_editor_property("LastShotTime"))
            state["previous_shots"] = shots
        if reloading and "auto_reload_started" not in state:
            assert ammo == 0 and shots == 35, (ammo, shots)
            state["auto_reload_started"] = t
        if "auto_reload_started" in state:
            if reloading:
                assert shots == 35 and ammo == 0
            elif shots >= 36:
                fire(False)
                elapsed = t - state["auto_reload_started"]
                assert 1.9 <= elapsed <= 2.25, elapsed
                assert shots == 36 and ammo == 29
                intervals = [b - a for a, b in zip(
                    state["shot_times"][:29], state["shot_times"][1:30])]
                assert len(intervals) == 29 and all(.14 < v < .21 for v in intervals), intervals
                state["results"].update(
                    empty_held_fire_reload_seconds=elapsed,
                    automatic_fire_mean_interval=sum(intervals) / len(intervals),
                    full_magazine_exactly_30_shots=True,
                    held_fire_resumed_after_reload=True)
                return True
        return False
    return True


def begin_case(world):
    name, script, marker, report = cases[state["case"]]
    player = unreal.GameplayStatics.get_player_pawn(world, 0)
    pc = unreal.GameplayStatics.get_player_controller(world, 0)
    assert health(player).get_editor_property("Health") == 100
    assert player.get_editor_property("Ammo") == 30
    assert pc.get_hud().get_class().get_name() == "SurvivalCombatHUD"
    spawner = unreal.GameplayStatics.get_all_actors_of_class(world, spawner_class)[0]
    population = enemies(world)
    assert len(population) == 3
    if name not in ("spawner", "hud"):
        spawner.set_actor_tick_enabled(False)
        if name == "stairs":
            for enemy in population:
                enemy.set_actor_tick_enabled(False)
                enemy.get_controller().stop_movement()
                enemy.get_controller().set_actor_tick_enabled(False)
        else:
            for enemy in population[1:]:
                enemy.destroy_actor()
            population[0].set_actor_label("TEMP_EnemyValidation")
        if name == "enemy_positions":
            state["block"] = spawn_block(world)
    old = os.path.join(output, report)
    if os.path.exists(old):
        os.remove(old)
    state["case_started"] = time.monotonic()
    state["stage"] = "running-" + name
    state.pop("restart_sent", None)
    if name == "player_cover":
        focus_window()
    run_script(script)
    if name == "rifle":
        focus_window()
        bounds = wintypes.RECT()
        assert user32.GetWindowRect(editor_window, ctypes.byref(bounds))
        user32.SetCursorPos(bounds.left + 700, bounds.top + 350)
        unreal.WidgetLibrary.set_input_mode_game_only(pc)
        unreal.WidgetLibrary.set_focus_to_game_viewport()
        state["input_stage"] = "capture"
        state["input_since"] = time.monotonic()
        aim(True)
    write()


def next_case():
    state["case"] += 1
    if state["case"] == len(cases):
        levels.editor_request_end_play()
        state["stage"] = "final-persistence"
    else:
        levels.editor_request_end_play()
        state["stage"] = "between-worlds"
    write()


def tick(_delta):
    try:
        assert time.monotonic() - state["started"] < 600, "Final validation exceeded 10 minutes."
        world = editor.get_game_world()
        if state["stage"] == "between-worlds":
            if not world:
                levels.editor_request_begin_play()
                state["stage"] = "waiting-world"
            return
        if state["stage"] == "final-persistence":
            if world:
                return
            assert not unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()
            assert not unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()
            assert levels.load_level("/Game/Shooter/Maps/Lvl_AtriumSurvival")
            run_script("validate_survival_arena.py")
            actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
            assert not any(a.get_actor_label().startswith("TEMP_") for a in actors)
            state["results"]["saved_map_reloaded_without_fixtures"] = True
            finish()
            return
        if not world:
            return
        if state["stage"] == "waiting-world":
            if len(enemies(world)) == 3:
                begin_case(world)
            return
        name, script, marker, report = cases[state["case"]]
        assert time.monotonic() - state["case_started"] < 180, name + " timed out."
        player = unreal.GameplayStatics.get_player_pawn(world, 0)
        pc = unreal.GameplayStatics.get_player_controller(world, 0)
        if name == "rifle":
            elapsed = time.monotonic() - state["input_since"]
            if state["input_stage"] == "capture" and elapsed > .15:
                aim(False)
                state["input_stage"] = "capture-release"
                state["input_since"] = time.monotonic()
            elif state["input_stage"] == "capture-release" and elapsed > .15:
                aim(True)
                state["input_stage"] = "aim-on"
                state["input_since"] = time.monotonic()
            elif state["input_stage"] == "aim-on" and elapsed > .6:
                assert player.get_editor_property("bIsAiming")
                assert abs(pc.player_camera_manager.get_fov_angle() - 65) < 2
                aim(False)
                state["input_stage"] = "aim-off"
                state["input_since"] = time.monotonic()
            elif state["input_stage"] == "aim-off" and elapsed > .6:
                assert not player.get_editor_property("bIsAiming")
                assert abs(pc.player_camera_manager.get_fov_angle() - 90) < 2
                state["results"]["real_rmb_aim_65_and_release_90"] = True
                pc.set_control_rotation(unreal.Rotator())
                player.set_actor_rotation(unreal.Rotator(), False)
                state["input_stage"] = "rifle-settle"
                state["input_since"] = time.monotonic()
            elif state["input_stage"] == "rifle-settle" and elapsed > .2:
                fire(True)
                state["input_stage"] = "firing"
            elif state["input_stage"] == "firing" and player.get_editor_property("Ammo") <= 25:
                fire(False)
                state["input_stage"] = "finished"
        if hasattr(builtins, marker):
            if name == "hud":
                child = getattr(builtins, marker)
                if child["stage"] == "waiting-for-enter-restart" and not state.get("restart_sent"):
                    unreal.WidgetLibrary.set_input_mode_game_only(pc)
                    unreal.WidgetLibrary.set_focus_to_game_viewport()
                    key(0x0D)
                    state["restart_sent"] = True
            return
        path = os.path.join(output, report)
        assert os.path.exists(path), name + " did not produce a report."
        with open(path, encoding="utf-8") as source:
            data = json.load(source)
        if isinstance(data, list):
            assert len(data) == 4 and all(r["passed"] for r in data), data
        else:
            result = data.get("results", data) if isinstance(data.get("results"), dict) else data
            assert result.get("passed"), result
        if name == "rifle" and not rifle_followup(world, player, pc):
            return
        if name == "spawner":
            if not state.get("restart_sent"):
                assert health(player).get_editor_property("bDead")
                unreal.WidgetLibrary.set_input_mode_game_only(pc)
                unreal.WidgetLibrary.set_focus_to_game_viewport()
                key(0x0D)
                state["restart_sent"] = True
                return
            if health(player).get_editor_property("bDead") or len(enemies(world)) != 3:
                return
            assert health(player).get_editor_property("Health") == 100
            assert player.get_editor_property("Ammo") == 30
            spawner = unreal.GameplayStatics.get_all_actors_of_class(world, spawner_class)[0]
            assert spawner.get_editor_property("TotalKills") == 0
            state["results"]["restart_after_population_ramp"] = True
        if name == "hud":
            assert data.get("awaiting_enter_restart") is False, data
        state["results"][name] = {"passed": True, "report": report}
        next_case()
    except Exception:
        finish(traceback.format_exc())


assert levels.load_level("/Game/Shooter/Maps/Lvl_AtriumSurvival")
run_script("validate_survival_arena.py")
state["results"]["saved_arena_navigation"] = True
state["handle"] = unreal.register_slate_post_tick_callback(tick)
performance.set_editor_property("bThrottleCPUWhenNotForeground", False)
state["stage"] = "waiting-world"
write()
levels.editor_request_begin_play()
unreal.log("Survival final validation started.")
