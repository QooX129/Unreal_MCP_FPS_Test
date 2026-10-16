import unreal

hud_class = unreal.load_class(None, "/Script/MCP_Test.SurvivalCombatHUD")
assert hud_class, "SurvivalCombatHUD native class was not loaded."

game_mode = unreal.load_asset("/Game/Shooter/Blueprints/BP_SurvivalGameMode")
assert game_mode
unreal.BlueprintEditorLibrary.compile_blueprint(game_mode)
assert game_mode.status == unreal.BlueprintStatus.BS_UP_TO_DATE

game_mode_cdo = unreal.get_default_object(game_mode.generated_class())
game_mode_cdo.set_editor_property("hud_class", hud_class)
assert game_mode_cdo.get_editor_property("hud_class") == hud_class
assert unreal.EditorAssetLibrary.save_loaded_asset(game_mode, only_if_is_dirty=False)
unreal.log("Configured BP_SurvivalGameMode to use SurvivalCombatHUD.")
