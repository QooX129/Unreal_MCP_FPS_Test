"""Match saved enemy sight, attack eligibility, and bullet reach to player aim."""

import unreal

editor = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
assert not editor.get_game_world(), "Stop PIE before changing enemy defaults."
assert not unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages(), "Save map edits first."
assert not unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages(), "Save asset edits first."
root = "/Game/Shooter/Blueprints/"
player = unreal.load_asset(root + "BP_SurvivalCharacter")
enemy = unreal.load_asset(root + "BP_SurvivalEnemy")
range_node = unreal.load_object(
    None, player.get_path_name() + ":EventGraph.K2Node_CallFunction_11")
player_range = float(range_node.find_input_pin("B").get_pin_value())
assert player_range > 0
multiplier = unreal.load_object(
    None, enemy.get_path_name() + ":EventGraph.K2Node_CallFunction_75")
range_get = unreal.load_object(
    None, enemy.get_path_name() + ":EventGraph.K2Node_VariableGet_6")
target = multiplier.find_input_pin("B")
target.break_pin_links()
assert range_get.find_output_pin("FireRange").try_create_connection(target)
unreal.BlueprintEditorLibrary.compile_blueprint(enemy)
defaults = unreal.get_default_object(enemy.generated_class())
for name in ("SightRange", "FireRange"):
    defaults.set_editor_property(name, player_range)
assert unreal.EditorAssetLibrary.save_loaded_asset(enemy, only_if_is_dirty=False)
assert unreal.EditorAssetLibrary.load_blueprint_class(
    root + "BP_SurvivalEnemy") == enemy.generated_class()
print("Saved enemy SightRange/FireRange and dynamic bullet reach:", player_range, "cm")
