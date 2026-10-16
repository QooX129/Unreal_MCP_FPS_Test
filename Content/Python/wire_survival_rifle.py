"""Wire Part 3 native Blueprint nodes. Run only after their initial creation."""

import unreal

ROOT = "/Game/Shooter/Blueprints/"
PINS = unreal.BlueprintGraphPinLibrary


def node(bp, kind, index):
    path = ROOT + bp + "." + bp + ":EventGraph.K2Node_" + kind + "_" + str(index)
    value = unreal.load_object(None, path)
    assert value, path
    return value


def pin(value, name, output=False):
    result = value.find_output_pin(name) if output else value.find_input_pin(name)
    assert result is not None, (value.get_name(), name)
    return result


def link(source, source_pin, target, target_pin):
    assert PINS.try_create_connection(
        pin(source, source_pin, True), pin(target, target_pin)
    ), (source.get_name(), source_pin, target.get_name(), target_pin)


def literal(value, name, text):
    assert PINS.set_pin_value(pin(value, name), str(text)), (value.get_name(), name, text)


def chain(*values):
    for left, right in zip(values, values[1:]):
        link(left, "then", right, "execute")


name = "BP_SurvivalCharacter"
bp = unreal.load_asset(ROOT + name)
f = {i: node(name, "CallFunction", i) for i in range(51) if i not in (17, 18, 19, 49)}
f.update({i: node(name, "CallFunction", i) for i in range(55, 65)})
g = {i: node(name, "VariableGet", i) for i in range(13) if i not in (9, 10)}
g[9] = node(name, "VariableGet", 13)
g[10] = node(name, "VariableGet", 14)
s = {i: node(name, "VariableSet", i) for i in range(15) if i not in (12, 13)}
s[12] = node(name, "VariableSet", 15)
s[13] = node(name, "VariableSet", 16)
b = {i: node(name, "IfThenElse", i) for i in range(5)}
q = {i: node(name, "ExecutionSequence", i) for i in range(2)}
self_node = node(name, "Self", 0)
last_shot = node(name, "VariableGet", 15)
flash = node(name, "VariableGet", 16)
set_last_shot = node(name, "VariableSet", 17)
tick = node(name, "Event", 2)

# Keep the greybox weapon in the right hand, but rotate its barrel toward aim.
link(g[6], "RifleRoot", f[23], "self")
link(f[16], "ReturnValue", f[23], "NewLocation")
link(f[16], "ReturnValue", f[24], "Start")
link(f[15], "ReturnValue", f[24], "Target")
link(f[24], "ReturnValue", f[23], "NewRotation")
literal(f[23], "bTeleport", "true")
link(g[7], "RifleMuzzle", f[25], "self")
PINS.break_pin_links(pin(s[6], "AimOrigin"))
PINS.break_pin_links(pin(f[20], "Start"))
link(f[25], "ReturnValue", s[6], "AimOrigin")
link(f[25], "ReturnValue", f[20], "Start")
link(f[25], "ReturnValue", f[50], "From")
link(f[15], "ReturnValue", f[50], "To")
link(f[50], "ReturnValue", f[55], "A")
literal(f[55], "B", 10)
link(f[15], "ReturnValue", f[56], "A")
link(f[55], "ReturnValue", f[56], "B")
PINS.break_pin_links(pin(f[20], "End"))
link(f[56], "ReturnValue", f[20], "End")

# A second short trace prevents a protruding barrel firing through nearby cover.
link(f[16], "ReturnValue", f[47], "Start")
link(f[25], "ReturnValue", f[47], "End")
for i in (20, 47):
    literal(f[i], "TraceChannel", "TraceTypeQuery1")
    literal(f[i], "bTraceComplex", "true")
    literal(f[i], "bIgnoreSelf", "true")
    literal(f[i], "DrawDebugType", "None")
PINS.break_pin_links(pin(s[5], "then", True))
PINS.break_pin_links(pin(s[6], "then", True))
chain(s[5], f[23], f[61], s[6], f[47], f[20], s[7], q[0])
link(flash, "RifleFlash", f[61], "self")
link(last_shot, "LastShotTime", f[59], "A")
literal(f[59], "B", .055)
link(f[26], "ReturnValue", f[60], "A")
link(f[59], "ReturnValue", f[60], "B")
link(f[60], "ReturnValue", f[61], "bNewVisibility")

link(f[0], "ReturnValue", f[27], "self")
link(f[0], "ReturnValue", f[28], "self")
literal(f[27], "Key", "LeftMouseButton")
literal(f[28], "Key", "R")
link(g[11], "bReloading", f[33], "A")
link(f[26], "ReturnValue", f[29], "A")
link(g[10], "ReloadEndTime", f[29], "B")
link(f[26], "ReturnValue", f[30], "A")
link(g[9], "NextShotTime", f[30], "B")
link(g[8], "Ammo", f[31], "A")
literal(f[31], "B", 0)
link(g[8], "Ammo", f[32], "A")
literal(f[32], "B", 30)

# Complete a reload before processing this frame's new input and firing.
link(q[0], "then_0", b[0], "execute")
link(g[11], "bReloading", f[34], "A")
link(f[29], "ReturnValue", f[34], "B")
link(f[34], "ReturnValue", b[0], "Condition")
chain(b[0], s[8], s[11])
literal(s[8], "Ammo", 30)
literal(s[11], "bReloading", "false")
link(q[0], "then_1", q[1], "execute")
link(q[1], "then_0", b[1], "execute")
link(g[8], "Ammo", f[62], "A")
literal(f[62], "B", 0)
link(f[27], "ReturnValue", f[63], "A")
link(f[62], "ReturnValue", f[63], "B")
link(f[28], "ReturnValue", f[64], "A")
link(f[63], "ReturnValue", f[64], "B")
PINS.break_pin_links(pin(f[35], "A"))
link(f[64], "ReturnValue", f[35], "A")
link(f[32], "ReturnValue", f[35], "B")
link(f[35], "ReturnValue", f[36], "A")
link(f[33], "ReturnValue", f[36], "B")
link(f[36], "ReturnValue", b[1], "Condition")
link(f[26], "ReturnValue", f[41], "A")
literal(f[41], "B", 2)
link(f[41], "ReturnValue", s[13], "ReloadEndTime")
literal(s[10], "bReloading", "true")
chain(b[1], s[13], s[10])

link(q[1], "then_1", b[2], "execute")
for dest, left, right in ((37, 27, 31), (38, 30, 33), (39, 37, 38)):
    link(f[left], "ReturnValue", f[dest], "A")
    link(f[right], "ReturnValue", f[dest], "B")
link(f[39], "ReturnValue", b[2], "Condition")
# Preserve the held-fire cadence without accumulating one-frame delays.
link(f[26], "ReturnValue", f[57], "A")
link(tick, "DeltaSeconds", f[57], "B")
link(g[9], "NextShotTime", f[58], "A")
link(f[57], "ReturnValue", f[58], "B")
link(f[58], "ReturnValue", f[40], "A")
literal(f[40], "B", 1 / 6)
link(f[40], "ReturnValue", s[12], "NextShotTime")
link(g[8], "Ammo", f[42], "A")
literal(f[42], "B", 1)
link(f[42], "ReturnValue", s[9], "Ammo")
link(g[12], "ShotsFired", f[43], "A")
literal(f[43], "B", 1)
link(f[43], "ReturnValue", s[14], "ShotsFired")
PINS.break_pin_links(pin(s[14], "then", True))
link(f[26], "ReturnValue", set_last_shot, "LastShotTime")
chain(b[2], s[12], s[9], s[14], set_last_shot, b[4])

link(f[47], "ReturnValue", f[48], "A")
link(f[48], "ReturnValue", b[4], "Condition")
chain(b[4], f[45], b[3])
link(f[20], "ReturnValue", b[3], "Condition")
chain(b[3], f[44], f[46])
link(f[21], "HitActor", f[44], "DamagedActor")
link(f[20], "OutHit", f[44], "HitInfo")
link(f[0], "ReturnValue", f[44], "EventInstigator")
link(self_node, "self", f[44], "DamageCauser")
link(f[50], "ReturnValue", f[44], "HitFromDirection")
literal(f[44], "BaseDamage", 20)
literal(f[44], "DamageTypeClass", "/Script/Engine.DamageType")
link(f[25], "ReturnValue", f[45], "LineStart")
link(f[22], "ReturnValue", f[45], "LineEnd")
literal(f[45], "LineColor", "(R=1,G=0.72,B=0.2,A=1)")
literal(f[45], "Duration", .065)
literal(f[45], "Thickness", 1.3)
link(f[21], "ImpactPoint", f[46], "Center")
literal(f[46], "Radius", 7)
literal(f[46], "Segments", 8)
literal(f[46], "LineColor", "(R=1,G=0.65,B=0.1,A=1)")
literal(f[46], "Duration", .18)
literal(f[46], "Thickness", 1.7)

for i in sorted(index for index in f if index >= 23):
    f[i].set_node_pos(unreal.IntPoint(4200 + ((i - 23) % 7) * 340,
                                    ((i - 23) // 7) * 380))
for i in range(5):
    b[i].set_node_pos(unreal.IntPoint(4200 + i * 480, -400))
for i in range(8, 15):
    s[i].set_node_pos(unreal.IntPoint(4200 + (i - 8) * 320, -750))
for i in range(6, 13):
    g[i].set_node_pos(unreal.IntPoint(4200 + (i - 6) * 320, 1800))
q[0].set_node_pos(unreal.IntPoint(3900, -450))
q[1].set_node_pos(unreal.IntPoint(3900, -150))
set_last_shot.set_node_pos(unreal.IntPoint(6600, -750))
last_shot.set_node_pos(unreal.IntPoint(6600, 1800))
flash.set_node_pos(unreal.IntPoint(6900, 1800))
unreal.BlueprintEditorLibrary.compile_blueprint(bp)
assert bp.status == unreal.BlueprintStatus.BS_UP_TO_DATE, bp.status
cdo = unreal.get_default_object(bp.generated_class())
assert isinstance(cdo.get_editor_property("NextShotTime"), float)
assert isinstance(cdo.get_editor_property("ReloadEndTime"), float)
cdo.set_editor_property("Ammo", 30)
cdo.set_editor_property("LastShotTime", -100)
assert unreal.EditorAssetLibrary.save_loaded_asset(bp, only_if_is_dirty=False)

name = "BP_SurvivalHUD"
hud = unreal.load_asset(ROOT + name)
h = {i: node(name, "CallFunction", i) for i in (1, 16, 17, 18, 19, 20, 21)}
cast = node(name, "DynamicCast", 0)
ammo = node(name, "VariableGet", 0)
reload = node(name, "VariableGet", 1)
link(h[16], "ReturnValue", cast, "Object")
chain(h[1], cast, h[21])
link(cast, "AsBP Survival Character", ammo, "self")
link(cast, "AsBP Survival Character", reload, "self")
link(ammo, "Ammo", h[17], "InInt")
link(h[17], "ReturnValue", h[18], "A")
literal(h[18], "B", " / 30  |  Unlimited reserve")
link(reload, "bReloading", h[19], "bPickA")
literal(h[19], "A", "   RELOADING...")
literal(h[19], "B", "   LMB: Fire   RMB: Aim   R: Reload")
link(h[18], "ReturnValue", h[20], "A")
link(h[19], "ReturnValue", h[20], "B")
link(h[20], "ReturnValue", h[21], "Text")
literal(h[21], "ScreenX", 35)
literal(h[21], "ScreenY", 45)
literal(h[21], "Scale", 1.5)
literal(h[21], "TextColor", "(R=1,G=1,B=1,A=1)")
for i in range(16, 22):
    h[i].set_node_pos(unreal.IntPoint((i - 16) * 320, 1100))
cast.set_node_pos(unreal.IntPoint(0, 750))
ammo.set_node_pos(unreal.IntPoint(320, 750))
reload.set_node_pos(unreal.IntPoint(640, 750))
unreal.BlueprintEditorLibrary.compile_blueprint(hud)
assert hud.status == unreal.BlueprintStatus.BS_UP_TO_DATE, hud.status
assert unreal.EditorAssetLibrary.save_loaded_asset(hud, only_if_is_dirty=False)
print("Rifle and ammo HUD compiled and saved. PIE validation still required.")
