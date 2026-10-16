"""Wire the shared health component's existing native Blueprint nodes."""

import unreal

ROOT = "/Game/Shooter/Blueprints/"
PINS = unreal.BlueprintGraphPinLibrary


def node(bp, kind, index):
    path = bp.get_path_name() + ":EventGraph.K2Node_" + kind + "_" + str(index)
    result = unreal.load_object(None, path)
    assert result, path
    return result


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


def save(bp):
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    assert bp.status == unreal.BlueprintStatus.BS_UP_TO_DATE, (bp.get_name(), bp.status)
    if bp.get_name() == "BP_SurvivalHealth":
        unreal.get_default_object(bp.generated_class()).set_editor_property(
            "EnemyCorpseLifetime", 0.01
        )
    assert unreal.EditorAssetLibrary.save_loaded_asset(bp, only_if_is_dirty=False)


bp = unreal.load_asset(ROOT + "BP_SurvivalHealth")
f = {i: node(bp, "CallFunction", i) for i in (*range(30), 31)}
g = {i: node(bp, "VariableGet", i) for i in range(10)}
s = {i: node(bp, "VariableSet", i) for i in range(5)}
b = {i: node(bp, "IfThenElse", i) for i in range(5)}
sequence = node(bp, "ExecutionSequence", 0)
tick_sequence = node(bp, "ExecutionSequence", 1)
cast = node(bp, "DynamicCast", 0)
begin = node(bp, "Event", 2)
tick = node(bp, "Event", 3)
damage = node(bp, "CustomEvent", 0)

chain(begin, s[0])
link(g[1], "MaxHealth", s[0], "Health")
link(g[6], "bDead", f[2], "A")
link(damage, "Damage", f[3], "A")
literal(f[3], "B", 0)
link(f[2], "ReturnValue", f[4], "A")
link(f[3], "ReturnValue", f[4], "B")
link(f[4], "ReturnValue", b[0], "Condition")
chain(damage, b[0], s[1], s[3], b[1])
link(g[0], "Health", f[5], "A")
link(damage, "Damage", f[5], "B")
link(f[5], "ReturnValue", f[6], "Value")
literal(f[6], "Min", 0)
link(g[1], "MaxHealth", f[6], "Max")
link(f[6], "ReturnValue", s[1], "Health")
link(f[1], "ReturnValue", s[3], "LastDamageTime")
link(g[0], "Health", f[7], "A")
literal(f[7], "B", 0)
link(f[7], "ReturnValue", b[1], "Condition")
chain(b[1], s[4], f[15], f[16], sequence)
literal(s[4], "bDead", "true")
for index, key in ((15, "bEnabled"), (16, "bNewActorEnableCollision")):
    link(f[0], "ReturnValue", f[index], "self")
    literal(f[index], key, "false")

# Character motion stops immediately, including when killed mid-jump.
link(sequence, "then_0", cast, "execute")
link(f[0], "ReturnValue", cast, "Object")
link(cast, "AsCharacter", g[8], "self")
link(g[8], "CharacterMovement", f[24], "self")
link(g[8], "CharacterMovement", f[25], "self")
chain(cast, f[24], f[25])
link(sequence, "then_1", b[3], "execute")
link(f[0], "ReturnValue", f[18], "A")
link(f[17], "ReturnValue", f[18], "B")
link(f[18], "ReturnValue", b[3], "Condition")
chain(b[3], f[20], f[21], f[23])
link(f[0], "ReturnValue", f[20], "self")
link(f[22], "ReturnValue", f[20], "PlayerController")
for index in (21, 23):
    link(f[22], "ReturnValue", f[index], "self")
    literal(f[index], "bNewMoveInput" if index == 21 else "bNewLookInput", "true")
link(b[3], "else", f[19], "execute")
link(f[0], "ReturnValue", f[19], "self")
link(g[5], "EnemyCorpseLifetime", f[19], "InLifespan")

# Catch falls above the engine Kill Z so normal health/death handling runs first.
PINS.break_pin_links(pin(tick, "then", True))
chain(tick, tick_sequence)
link(tick_sequence, "then_0", b[4], "execute")
link(f[0], "ReturnValue", f[26], "self")
link(f[26], "ReturnValue", f[27], "InVec")
link(f[27], "Z", f[28], "A")
link(g[9], "FallDeathZ", f[28], "B")
link(f[28], "ReturnValue", f[29], "A")
link(f[2], "ReturnValue", f[29], "B")
link(f[29], "ReturnValue", b[4], "Condition")
chain(b[4], f[31])
link(f[0], "ReturnValue", f[31], "DamagedActor")
link(g[0], "Health", f[31], "BaseDamage")
link(f[0], "ReturnValue", f[31], "DamageCauser")
literal(f[31], "DamageTypeClass", "/Script/Engine.DamageType")
link(tick_sequence, "then_1", b[2], "execute")
chain(b[2], s[2])
link(g[2], "LastDamageTime", f[9], "A")
link(g[3], "RegenDelay", f[9], "B")
link(f[1], "ReturnValue", f[8], "A")
link(f[9], "ReturnValue", f[8], "B")
link(g[7], "bRegenerates", f[10], "A")
link(f[2], "ReturnValue", f[10], "B")
link(f[10], "ReturnValue", f[11], "A")
link(f[8], "ReturnValue", f[11], "B")
link(f[11], "ReturnValue", b[2], "Condition")
link(g[4], "RegenRate", f[12], "A")
link(tick, "DeltaSeconds", f[12], "B")
link(g[0], "Health", f[13], "A")
link(f[12], "ReturnValue", f[13], "B")
link(f[13], "ReturnValue", f[14], "Value")
literal(f[14], "Min", 0)
link(g[1], "MaxHealth", f[14], "Max")
link(f[14], "ReturnValue", s[2], "Health")

for i, value in f.items():
    value.set_node_pos(unreal.IntPoint(400 + (i % 7) * 340, 400 + (i // 7) * 320))
for i, value in g.items():
    value.set_node_pos(unreal.IntPoint(i * 300, -400))
for i, value in s.items():
    value.set_node_pos(unreal.IntPoint(400 + i * 340, -50))
for i, value in b.items():
    value.set_node_pos(unreal.IntPoint(400 + i * 500, 1900))
damage.set_node_pos(unreal.IntPoint(0, 650))
sequence.set_node_pos(unreal.IntPoint(2700, 500))
tick_sequence.set_node_pos(unreal.IntPoint(0, 1600))
cast.set_node_pos(unreal.IntPoint(3000, 500))
save(bp)

for path, get_index, call_index in (
    (ROOT + "BP_SurvivalCharacter", 17, 65),
    ("/Game/Shooter/Tests/BP_RifleTestTarget", 0, 0),
):
    receiver = unreal.load_asset(path)
    event = node(receiver, "Event", 4)
    component = node(receiver, "VariableGet", get_index)
    apply = node(receiver, "CallFunction", call_index)
    link(event, "then", apply, "execute")
    link(event, "Damage", apply, "Damage")
    link(component, "HealthComponent", apply, "self")
    component.set_node_pos(unreal.IntPoint(0, 2700))
    apply.set_node_pos(unreal.IntPoint(350, 2400))
    if receiver.get_name() == "BP_SurvivalCharacter":
        dead = node(receiver, "VariableGet", 18)
        branch = node(receiver, "IfThenElse", 5)
        reload = node(receiver, "VariableSet", 18)
        aiming = node(receiver, "VariableSet", 19)
        hide = node(receiver, "CallFunction", 66)
        flash = node(receiver, "VariableGet", 16)
        link(component, "HealthComponent", dead, "self")
        link(dead, "bDead", branch, "Condition")
        chain(apply, branch, reload, aiming, hide)
        literal(reload, "bReloading", "false")
        literal(aiming, "bIsAiming", "false")
        link(flash, "RifleFlash", hide, "self")
        literal(hide, "bNewVisibility", "false")
        for i, value in enumerate((branch, reload, aiming, hide)):
            value.set_node_pos(unreal.IntPoint(700 + i * 300, 2400))
        dead.set_node_pos(unreal.IntPoint(350, 2700))
    save(receiver)

hud = unreal.load_asset(ROOT + "BP_SurvivalHUD")
h = {i: node(hud, "CallFunction", i) for i in (2, 3, 21, *range(22, 38))}
hg = {i: node(hud, "VariableGet", i) for i in range(2, 6)}
cast = node(hud, "DynamicCast", 0)
draw = node(hud, "Event", 3)
dead_branch = node(hud, "IfThenElse", 0)
restart_branch = node(hud, "IfThenElse", 1)
had_pawn = node(hud, "VariableGet", 6)
set_had_pawn = node(hud, "VariableSet", 0)
lost_branch = node(hud, "IfThenElse", 2)
zero_hp = node(hud, "CallFunction", 44)
PINS.break_pin_links(pin(cast, "then", True))
chain(cast, set_had_pawn, h[21])
literal(set_had_pawn, "bHadPlayerPawn", "true")
# Native Kill Z can destroy a pawn before its component ticks (e.g. teleport).
link(cast, "CastFailed", lost_branch, "execute")
link(had_pawn, "bHadPlayerPawn", lost_branch, "Condition")
chain(lost_branch, zero_hp, h[27])
literal(zero_hp, "Text", "HP  0")
literal(zero_hp, "ScreenX", 35)
literal(zero_hp, "ScreenY", 80)
literal(zero_hp, "Scale", 1.7)
literal(zero_hp, "TextColor", "(R=0.8,G=1,B=0.8,A=1)")
link(cast, "AsBP Survival Character", hg[2], "self")
for i in (3, 4, 5):
    link(hg[2], "HealthComponent", hg[i], "self")
link(hg[3], "Health", h[22], "A")
link(hg[4], "MaxHealth", h[23], "A")
link(h[22], "ReturnValue", h[24], "InInt")
literal(h[24], "Prefix", "HP  ")
literal(h[24], "Suffix", " / ")
link(h[24], "ReturnValue", h[25], "AppendTo")
link(h[23], "ReturnValue", h[25], "InInt")
link(h[25], "ReturnValue", h[26], "Text")
literal(h[26], "ScreenX", 35)
literal(h[26], "ScreenY", 80)
literal(h[26], "Scale", 1.7)
literal(h[26], "TextColor", "(R=0.8,G=1,B=0.8,A=1)")
chain(h[21], h[26], dead_branch, h[27], h[28], h[29], restart_branch)
link(hg[5], "bDead", dead_branch, "Condition")
literal(h[27], "RectColor", "(R=0.015,G=0.005,B=0.005,A=0.85)")
literal(h[27], "ScreenX", 0)
literal(h[27], "ScreenY", 0)
link(draw, "SizeX", h[27], "ScreenW")
link(draw, "SizeY", h[27], "ScreenH")
link(h[2], "ReturnValue", h[30], "A")
literal(h[30], "B", 180)
link(h[3], "ReturnValue", h[32], "A")
literal(h[32], "B", 60)
link(h[3], "ReturnValue", h[31], "A")
literal(h[31], "B", 20)
for index, y, text, scale in (
    (28, 32, "YOU DIED", 3.5),
    (29, 31, "Press ENTER to Restart", 1.8),
):
    link(h[30], "ReturnValue", h[index], "ScreenX")
    link(h[y], "ReturnValue", h[index], "ScreenY")
    literal(h[index], "Text", text)
    literal(h[index], "Scale", scale)
    literal(h[index], "TextColor", "(R=1,G=0.9,B=0.85,A=1)")
link(h[33], "ReturnValue", h[34], "self")
literal(h[34], "Key", "Enter")
link(h[34], "ReturnValue", restart_branch, "Condition")
chain(restart_branch, h[35], h[36])
literal(h[35], "bRemovePrefixString", "true")
link(h[35], "ReturnValue", h[37], "InString")
link(h[37], "ReturnValue", h[36], "LevelName")
literal(h[36], "bAbsolute", "true")
for index in range(22, 38):
    h[index].set_node_pos(unreal.IntPoint(((index - 22) % 6) * 340,
                                        1600 + ((index - 22) // 6) * 380))
for i, value in hg.items():
    value.set_node_pos(unreal.IntPoint((i - 2) * 340, 1300))
dead_branch.set_node_pos(unreal.IntPoint(2100, 1600))
restart_branch.set_node_pos(unreal.IntPoint(2100, 2000))
unreal.get_default_object(hud.generated_class()).set_editor_property(
    "auto_receive_input", unreal.AutoReceiveInput.DISABLED)
hud_input = node(hud, "CallFunction", 51)
chain(node(hud, "Event", 0), hud_input)
link(h[33], "ReturnValue", hud_input, "PlayerController")
save(hud)
print("Health, player/test damage forwarding, basic HP display and death/restart HUD compiled and saved.")
