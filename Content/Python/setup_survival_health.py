"""Attach the reusable health component to the player and a test-only receiver."""

import unreal

ROOT = "/Game/Shooter/Blueprints/"
sub = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
lib = unreal.SubobjectDataBlueprintFunctionLibrary
health = unreal.load_asset(ROOT + "BP_SurvivalHealth")
assert health.status == unreal.BlueprintStatus.BS_UP_TO_DATE

for path, regenerates in (
    (ROOT + "BP_SurvivalCharacter", True),
    ("/Game/Shooter/Tests/BP_RifleTestTarget", False),
):
    bp = unreal.load_asset(path)
    handles = sub.k2_gather_subobject_data_for_blueprint(bp)
    templates = [
        lib.get_object_for_blueprint(sub.k2_find_subobject_data_from_handle(h), bp)
        for h in handles
    ]
    component = next((c for c in templates if c and c.get_name() == "HealthComponent_GEN_VARIABLE"), None)
    if not component:
        handle, error = sub.add_new_subobject(unreal.AddNewSubobjectParams(
            parent_handle=handles[0], new_class=health.generated_class(), blueprint_context=bp
        ))
        assert not str(error), str(error)
        assert sub.rename_subobject(handle, "HealthComponent")
        component = lib.get_object_for_blueprint(sub.k2_find_subobject_data_from_handle(handle), bp)
    component.modify()
    component.set_editor_property("bRegenerates", regenerates)
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    assert bp.status == unreal.BlueprintStatus.BS_UP_TO_DATE
    assert unreal.EditorAssetLibrary.save_loaded_asset(bp, only_if_is_dirty=False)
    print(path, "HealthComponent attached, regenerates:", regenerates)
