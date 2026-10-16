"""Notify the survival spawner exactly once when an enemy dies."""

import unreal

bp = unreal.load_asset("/Game/Shooter/Blueprints/BP_SurvivalEnemy")
assert bp
pins = unreal.BlueprintGraphPinLibrary


def node(kind, index):
    path = bp.get_path_name() + ":EventGraph.K2Node_" + kind + "_" + str(index)
    result = unreal.load_object(None, path)
    assert result, path
    return result


def pin(target, name, output=False):
    result = target.find_output_pin(name) if output else target.find_input_pin(name)
    assert result is not None, (target.get_name(), name)
    return result


def link(source, output_name, target, input_name):
    assert pins.try_create_connection(
        pin(source, output_name, True), pin(target, input_name)
    ), (source.get_name(), output_name, target.get_name(), input_name)


def value(target, name, text):
    assert pins.set_pin_value(pin(target, name), str(text)), (
        target.get_name(),
        name,
        text,
    )


damage_dead = node("IfThenElse", 9)
reported_guard = node("IfThenElse", 19)
reported_get = node("VariableGet", 34)
reported_set = node("VariableSet", 27)
not_reported = node("CallFunction", 110)
find_spawner = node("CallFunction", 109)
report_death = node("CallFunction", 111)
missing_spawner_log = node("CallFunction", 112)
spawner_cast = node("DynamicCast", 2)
finish_death = node("VariableSet", 11)

# Preserve the existing death cleanup while adding an exactly-once report.
pins.break_pin_links(pin(damage_dead, "then", True))
link(damage_dead, "then", reported_guard, "execute")
link(reported_get, "bDeathReported", not_reported, "A")
link(not_reported, "ReturnValue", reported_guard, "Condition")
link(reported_guard, "then", reported_set, "execute")
value(reported_set, "bDeathReported", "true")
link(reported_set, "then", find_spawner, "execute")
value(
    find_spawner,
    "ActorClass",
    "BP_SurvivalSpawner_C'/Game/Shooter/Blueprints/BP_SurvivalSpawner.BP_SurvivalSpawner_C'",
)
link(find_spawner, "then", spawner_cast, "execute")
link(find_spawner, "ReturnValue", spawner_cast, "Object")
link(spawner_cast, "then", report_death, "execute")
link(spawner_cast, "AsBP Survival Spawner", report_death, "self")
link(report_death, "then", finish_death, "execute")
link(reported_guard, "else", finish_death, "execute")
link(spawner_cast, "CastFailed", missing_spawner_log, "execute")
value(missing_spawner_log, "InString", "Survival enemy died but BP_SurvivalSpawner was not found.")
value(missing_spawner_log, "bPrintToLog", "true")
value(missing_spawner_log, "bPrintToScreen", "false")
link(missing_spawner_log, "then", finish_death, "execute")

lib = unreal.BlueprintEditorLibrary
lib.compile_blueprint(bp)
assert bp.status == unreal.BlueprintStatus.BS_UP_TO_DATE, bp.status
unreal.get_default_object(bp.generated_class()).set_editor_property(
    "bDeathReported", False
)
assert unreal.EditorAssetLibrary.save_loaded_asset(bp, only_if_is_dirty=False)
print("Compiled and saved the exactly-once enemy death callback.")
