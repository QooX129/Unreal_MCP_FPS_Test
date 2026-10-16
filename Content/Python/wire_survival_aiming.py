"""Wire the native Blueprint nodes created for Part 2 using UE graph-pin APIs.

The game runs saved Blueprint bytecode, not editor Python. AimOrigin uses the
right hand until Part 3 supplies the rifle muzzle. Tracing from the hand keeps
nearby cover relevant even when the shoulder camera can see around it.
"""

import json
import unreal

ROOT = "/Game/Shooter/Blueprints/"
pins = unreal.BlueprintGraphPinLibrary


def node(bp, kind, index):
    path = ROOT + bp + "." + bp + ":EventGraph.K2Node_" + kind + "_" + str(index)
    value = unreal.load_object(None, path)
    assert value, path
    return value


def pin(node_value, name, output=False):
    value = node_value.find_output_pin(name) if output else node_value.find_input_pin(name)
    assert value is not None, (node_value.get_name(), name)
    return value


def link(source, source_pin, target, target_pin):
    assert pins.try_create_connection(
        pin(source, source_pin, True), pin(target, target_pin)
    ), (source.get_name(), source_pin, target.get_name(), target_pin)


def literal(node_value, name, value):
    assert pins.set_pin_value(pin(node_value, name), str(value)), (
        node_value.get_name(), name, value
    )


bp_name = "BP_SurvivalCharacter"
bp = unreal.load_asset(ROOT + bp_name)
f = {i: node(bp_name, "CallFunction", i) for i in range(23) if i not in (17, 18, 19)}
g = {i: node(bp_name, "VariableGet", i) for i in range(6)}
s = {i: node(bp_name, "VariableSet", i) for i in range(8)}
tick = node(bp_name, "Event", 2)
literal(f[1], "Key", "RightMouseButton")
link(f[0], "ReturnValue", f[1], "self")
link(f[1], "ReturnValue", s[0], "bIsAiming")
link(f[1], "ReturnValue", s[1], "bUseControllerRotationYaw")
link(f[1], "ReturnValue", f[2], "A")
link(f[2], "ReturnValue", s[2], "bOrientRotationToMovement")
link(g[2], "CharacterMovement", s[2], "self")
link(g[2], "CharacterMovement", s[4], "self")

for select, a, b in ((3, 220, 380), (5, 65, 90), (8, 250, 500)):
    literal(f[select], "A", a)
    literal(f[select], "B", b)
    link(f[1], "ReturnValue", f[select], "bPickA")
link(f[8], "ReturnValue", s[4], "MaxWalkSpeed")
link(g[0], "CameraBoom", g[4], "self")
link(g[0], "CameraBoom", s[3], "self")
link(g[4], "TargetArmLength", f[4], "Current")
link(f[3], "ReturnValue", f[4], "Target")
link(f[4], "ReturnValue", s[3], "TargetArmLength")
link(g[1], "FollowCamera", g[5], "self")
link(g[1], "FollowCamera", f[6], "self")
link(g[5], "FieldOfView", f[7], "Current")
link(f[5], "ReturnValue", f[7], "Target")
link(f[7], "ReturnValue", f[6], "InFieldOfView")
for i in (4, 7):
    link(tick, "DeltaSeconds", f[i], "DeltaTime")
    literal(f[i], "InterpSpeed", 12)

link(g[1], "FollowCamera", f[9], "self")
link(g[1], "FollowCamera", f[10], "self")
link(f[10], "ReturnValue", f[11], "A")
literal(f[11], "B", 20000)
link(f[9], "ReturnValue", f[12], "A")
link(f[11], "ReturnValue", f[12], "B")
link(f[9], "ReturnValue", f[14], "Start")
link(f[12], "ReturnValue", f[14], "End")
link(f[14], "OutHit", f[13], "Hit")
link(f[13], "ImpactPoint", f[15], "A")
link(f[12], "ReturnValue", f[15], "B")
link(f[14], "ReturnValue", f[15], "bPickA")
link(f[15], "ReturnValue", s[5], "CameraAimPoint")
link(g[3], "Mesh", f[16], "self")
literal(f[16], "InSocketName", "hand_r")
link(f[16], "ReturnValue", s[6], "AimOrigin")
link(f[16], "ReturnValue", f[20], "Start")
link(f[15], "ReturnValue", f[20], "End")
link(f[20], "OutHit", f[21], "Hit")
link(f[21], "ImpactPoint", f[22], "A")
link(f[15], "ReturnValue", f[22], "B")
link(f[20], "ReturnValue", f[22], "bPickA")
link(f[22], "ReturnValue", s[7], "AimPoint")
for trace in (14, 20):
    literal(f[trace], "TraceChannel", "TraceTypeQuery1")
    literal(f[trace], "bIgnoreSelf", "true")
    literal(f[trace], "bTraceComplex", "true")
    literal(f[trace], "DrawDebugType", "None")

execution = [tick, s[0], s[1], s[2], s[4], s[3], f[6], f[14], s[5], s[6], f[20], s[7]]
for left, right in zip(execution, execution[1:]):
    link(left, "then", right, "execute")
for i, value in enumerate(execution):
    value.set_node_pos(unreal.IntPoint(i * 300, 0))
for i in f:
    if f[i] not in execution:
        f[i].set_node_pos(unreal.IntPoint((i % 6) * 320, 400 + (i // 6) * 280))
for i, value in enumerate(g.values()):
    value.set_node_pos(unreal.IntPoint(i * 320, -300))
unreal.BlueprintEditorLibrary.compile_blueprint(bp)
assert bp.status == unreal.BlueprintStatus.BS_UP_TO_DATE, bp.status
cdo = unreal.get_default_object(bp.generated_class())
cdo.camera_boom.set_editor_property("target_arm_length", 380)
cdo.camera_boom.set_editor_property("socket_offset", unreal.Vector(0, 65, 65))
cdo.camera_boom.set_editor_property("enable_camera_lag", True)
cdo.camera_boom.set_editor_property("camera_lag_speed", 15)
cdo.camera_boom.set_editor_property("do_collision_test", True)
cdo.follow_camera.set_editor_property("field_of_view", 90)
assert unreal.EditorAssetLibrary.save_loaded_asset(bp, only_if_is_dirty=False)

hud_name = "BP_SurvivalHUD"
hud = unreal.load_asset(ROOT + hud_name)
h = {i: node(hud_name, "CallFunction", i) for i in range(8)}
draw = node(hud_name, "Event", 3)
link(draw, "then", h[0], "execute")
link(h[0], "then", h[1], "execute")
link(draw, "SizeX", h[2], "A")
link(draw, "SizeY", h[3], "A")
literal(h[2], "B", 2)
literal(h[3], "B", 2)
for index, division, amount in ((4, 2, 6), (5, 3, 1), (6, 2, 1), (7, 3, 6)):
    link(h[division], "ReturnValue", h[index], "A")
    literal(h[index], "B", amount)
for target, sx, sy, width, height in ((0, 4, 5, 12, 2), (1, 6, 7, 2, 12)):
    link(h[sx], "ReturnValue", h[target], "ScreenX")
    link(h[sy], "ReturnValue", h[target], "ScreenY")
    literal(h[target], "ScreenW", width)
    literal(h[target], "ScreenH", height)
    literal(h[target], "RectColor", "(R=1,G=1,B=1,A=0.95)")
draw.set_node_pos(unreal.IntPoint(0, 0))
for i in range(8):
    h[i].set_node_pos(unreal.IntPoint((i % 4) * 300, 250 + (i // 4) * 250))
unreal.BlueprintEditorLibrary.compile_blueprint(hud)
assert hud.status == unreal.BlueprintStatus.BS_UP_TO_DATE, hud.status
assert unreal.EditorAssetLibrary.save_loaded_asset(hud, only_if_is_dirty=False)

game_mode = unreal.load_asset(ROOT + "BP_SurvivalGameMode")
unreal.BlueprintEditorLibrary.compile_blueprint(game_mode)
gm_cdo = unreal.get_default_object(game_mode.generated_class())
game_mode.modify()
gm_cdo.modify()
gm_cdo.set_editor_property("default_pawn_class", bp.generated_class())
gm_cdo.set_editor_property("hud_class", hud.generated_class())
assert unreal.EditorAssetLibrary.save_loaded_asset(game_mode, only_if_is_dirty=False)
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
assert world.get_outermost().get_name() == "/Game/Shooter/Maps/Lvl_AtriumSurvival"
world.get_world_settings().set_editor_property("default_game_mode", game_mode.generated_class())
print(json.dumps({
    "character_status": str(bp.status), "hud_status": str(hud.status),
    "runtime": "saved Blueprint bytecode", "aim_input": "hold RightMouseButton",
    "hip_arm_cm": 380, "aim_arm_cm": 220, "hip_fov": 90, "aim_fov": 65,
    "trace_range_cm": 20000, "aim_origin": "hand_r; replaced with rifle muzzle in Part 3",
    "user_approval": "pending",
}))
