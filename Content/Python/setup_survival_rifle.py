"""Create collision-free greybox rifle components on the Survival character."""

import unreal

bp = unreal.load_asset("/Game/Shooter/Blueprints/BP_SurvivalCharacter")
sub = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
lib = unreal.SubobjectDataBlueprintFunctionLibrary
handles = sub.k2_gather_subobject_data_for_blueprint(bp)
mesh_handle = next(
    h for h in handles
    if lib.get_object(sub.k2_find_subobject_data_from_handle(h)).get_name() == "CharacterMesh0"
)


def component(name, cls, parent):
    for handle in sub.k2_gather_subobject_data_for_blueprint(bp):
        data = sub.k2_find_subobject_data_from_handle(handle)
        obj = lib.get_object_for_blueprint(data, bp)
        if obj and obj.get_name() == name + "_GEN_VARIABLE":
            return handle, obj
    handle, error = sub.add_new_subobject(unreal.AddNewSubobjectParams(
        parent_handle=parent, new_class=cls, blueprint_context=bp
    ))
    assert not str(error), str(error)
    assert sub.rename_subobject(handle, name)
    data = sub.k2_find_subobject_data_from_handle(handle)
    obj = lib.get_object_for_blueprint(data, bp)
    assert obj, name
    return handle, obj


rifle_handle, rifle = component("RifleRoot", unreal.SceneComponent, mesh_handle)
rifle.set_editor_property("relative_location", unreal.Vector())
cube = unreal.load_asset("/Engine/BasicShapes/Cube")
dark = unreal.load_asset("/Game/Greybox/ConcreteAtrium/Materials/M_RecessCharcoal")
metal = unreal.load_asset("/Game/Greybox/ConcreteAtrium/Materials/M_JointGrey")
for name, loc, scale, mat in (
    ("RifleReceiver", (12, 0, 0), (.38, .075, .10), dark),
    ("RifleBarrel", (42, 0, 1), (.34, .035, .035), metal),
    ("RifleStock", (-16, 0, 0), (.22, .065, .12), dark),
    ("RifleMagazine", (10, 0, -10), (.10, .06, .16), metal),
    ("RifleSight", (20, 0, 8), (.10, .04, .05), metal),
):
    _, part = component(name, unreal.StaticMeshComponent, rifle_handle)
    part.set_static_mesh(cube)
    part.set_material(0, mat)
    part.set_editor_property("relative_location", unreal.Vector(*loc))
    part.set_editor_property("relative_scale3d", unreal.Vector(*scale))
    part.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    part.set_editor_property("cast_shadow", True)
_, muzzle = component("RifleMuzzle", unreal.SceneComponent, rifle_handle)
muzzle.set_editor_property("relative_location", unreal.Vector(61, 0, 1))
material_path = "/Game/Shooter/Materials/M_RifleFlash"
flash_material = unreal.load_asset(material_path)
if not flash_material:
    flash_material = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        "M_RifleFlash", "/Game/Shooter/Materials", unreal.Material, unreal.MaterialFactoryNew()
    )
    flash_material.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    color = unreal.MaterialEditingLibrary.create_material_expression(
        flash_material, unreal.MaterialExpressionConstant3Vector
    )
    color.set_editor_property("constant", unreal.LinearColor(18, 6, .5, 1))
    assert unreal.MaterialEditingLibrary.connect_material_property(
        color, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR
    )
    unreal.MaterialEditingLibrary.recompile_material(flash_material)
    assert unreal.EditorAssetLibrary.save_loaded_asset(flash_material, only_if_is_dirty=False)
_, flash = component("RifleFlash", unreal.StaticMeshComponent, rifle_handle)
flash.set_static_mesh(unreal.load_asset("/Engine/BasicShapes/Sphere"))
flash.set_material(0, flash_material)
flash.set_editor_property("relative_location", unreal.Vector(63, 0, 1))
flash.set_editor_property("relative_scale3d", unreal.Vector(.12, .065, .065))
flash.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
flash.set_editor_property("cast_shadow", False)
flash.set_visibility(False)
if "LastShotTime" not in [str(n) for n in unreal.BlueprintEditorLibrary.list_member_variable_names(bp)]:
    time_node = unreal.load_object(None, bp.get_path_name() + ":EventGraph.K2Node_CallFunction_26")
    assert unreal.BlueprintEditorLibrary.add_member_variable(
        bp, "LastShotTime",
        unreal.BlueprintGraphPinLibrary.get_pin_type(time_node.find_output_pin("ReturnValue"))
    )
unreal.BlueprintEditorLibrary.compile_blueprint(bp)
assert bp.status == unreal.BlueprintStatus.BS_UP_TO_DATE
cdo = unreal.get_default_object(bp.generated_class())
cdo.set_editor_property("Ammo", 30)
cdo.set_editor_property("LastShotTime", -100)
assert unreal.EditorAssetLibrary.save_loaded_asset(bp, only_if_is_dirty=False)
print("Rifle components ready: hand-following root, five mesh parts, muzzle and flash.")
