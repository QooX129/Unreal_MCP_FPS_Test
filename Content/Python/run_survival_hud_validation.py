"""Start PIE and launch the bounded survival HUD test on its first game tick."""

import os

import unreal

state = {}


def game_world():
    return unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()


def start_test(_delta):
    if not game_world():
        return
    unreal.unregister_slate_post_tick_callback(state["handle"])
    path = os.path.join(
        unreal.Paths.project_dir(), "Content", "Python", "test_survival_hud.py"
    )
    with open(path, encoding="utf-8") as script:
        exec(compile(script.read(), path, "exec"), globals())


state["handle"] = unreal.register_slate_post_tick_callback(start_test)
unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_request_begin_play()
