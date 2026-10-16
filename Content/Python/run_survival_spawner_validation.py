"""Start PIE and launch the bounded spawner validation on its first game tick."""

import os
import unreal

state = {}


def start_test(_delta):
    if not unreal.EditorLevelLibrary.get_game_world():
        return
    unreal.unregister_slate_post_tick_callback(state["handle"])
    path = os.path.join(
        unreal.Paths.project_dir(), "Content", "Python", "test_survival_spawner.py"
    )
    with open(path, encoding="utf-8") as script:
        exec(compile(script.read(), path, "exec"), globals())


state["handle"] = unreal.register_slate_post_tick_callback(start_test)
unreal.get_editor_subsystem(
    unreal.LevelEditorSubsystem
).editor_request_begin_play()
