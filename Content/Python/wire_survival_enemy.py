"""Wire saved Blueprint enemy logic; Python is editor tooling only."""

import unreal

PINS = unreal.BlueprintGraphPinLibrary
bp = unreal.load_asset("/Game/Shooter/Blueprints/BP_SurvivalEnemy")


def nodes(kind, count):
    result = {}
    for i in range(count):
        path = bp.get_path_name() + ":EventGraph.K2Node_" + kind + "_" + str(i)
        result[i] = unreal.load_object(None, path)
        assert result[i], path
    return result


def pin(n, name, output=False):
    p = n.find_output_pin(name) if output else n.find_input_pin(name)
    assert p is not None, (n.get_name(), name)
    return p


def link(a, output, b, input_name):
    assert PINS.try_create_connection(pin(a, output, True), pin(b, input_name)), (
        a.get_name(), output, b.get_name(), input_name
    )


def value(n, name, text):
    assert PINS.set_pin_value(pin(n, name), str(text)), (n.get_name(), name, text)


def chain(*items):
    for a, b in zip(items, items[1:]):
        link(a, "then", b, "execute")


f = nodes("CallFunction", 109)
g = nodes("VariableGet", 34)
s = nodes("VariableSet", 27)
b = nodes("IfThenElse", 19)
e = nodes("Event", 4)
c = nodes("CustomEvent", 6)
casts = nodes("DynamicCast", 2)
q = nodes("ExecutionSequence", 2)
self_node = nodes("Self", 1)[0]
for group in (f, g, s, b, e, c, casts, q):
    for n in group.values():
        for p in n.list_all_pins():
            PINS.break_pin_links(p)


def var(index, name, target, input_name):
    link(g[index], name, target, input_name)


def ret(index, target, input_name):
    link(f[index], "ReturnValue", target, input_name)


def binary(index, a, a_pin, z, z_pin):
    names = ("V1", "V2") if index in (7, 47, 65) else (
        ("From", "To") if index in (8, 73) else ("A", "B")
    )
    link(a, a_pin, f[index], names[0])
    link(z, z_pin, f[index], names[1])


# Resolve the player before evaluating any external health or location pins.
chain(e[0], s[0])
ret(3, s[0], "HomeLocation")
chain(e[2], q[0])
link(q[0], "then_0", f[28], "execute")
link(q[0], "then_1", b[0], "execute")
var(2, "bDead", b[0], "Condition")
link(b[0], "else", casts[0], "execute")
ret(0, casts[0], "Object")
chain(casts[0], casts[1], b[1])
ret(1, casts[1], "Object")
link(casts[0], "CastFailed", f[93], "execute")
value(f[93], "InString", "Survival enemy has no AIController; check Auto Possess AI.")
link(casts[1], "CastFailed", s[12], "execute")
link(b[1], "then", s[12], "execute")
chain(s[12], f[59])
value(s[12], "AIState", "Idle")
ret(0, f[59], "self")
var(0, "HealthComponent", g[2], "self")
link(casts[1], "AsBP Survival Character", g[1], "self")
var(1, "HealthComponent", g[4], "self")
var(4, "bDead", b[1], "Condition")
link(casts[1], "AsBP Survival Character", f[4], "self")
ret(3, f[5], "A")
value(f[5], "B", "(X=0,Y=0,Z=60)")
ret(4, f[6], "A")
value(f[6], "B", "(X=0,Y=0,Z=40)")
binary(7, f[3], "ReturnValue", f[4], "ReturnValue")
binary(8, f[5], "ReturnValue", f[6], "ReturnValue")
binary(10, f[9], "ReturnValue", f[8], "ReturnValue")
binary(11, f[7], "ReturnValue", g[3], "SightRange")
binary(12, f[10], "ReturnValue", g[5], "SightDotThreshold")
binary(16, f[11], "ReturnValue", f[12], "ReturnValue")
binary(17, f[16], "ReturnValue", f[15], "ReturnValue")
link(f[13], "OutHit", f[14], "Hit")
binary(15, f[14], "HitActor", f[1], "ReturnValue")
link(b[1], "else", f[13], "execute")
chain(f[13], s[1], b[2])
ret(5, f[13], "Start")
ret(6, f[13], "End")
ret(17, s[1], "bCanSeePlayer")
var(28, "bCanSeePlayer", b[2], "Condition")
chain(b[2], b[3])
var(26, "bHadSight", f[20], "A")
ret(20, b[3], "Condition")
chain(b[3], s[4], s[22], q[1])
value(s[22], "BurstShots", 0)
binary(21, f[2], "ReturnValue", g[7], "ReactionDelay")
ret(21, s[4], "ReactionEndTime")
link(b[3], "else", q[1], "execute")
link(q[1], "then_0", s[2], "execute")
chain(s[2], s[5], s[6], s[10], f[26])
value(s[2], "bHadSight", "true")
binary(22, f[2], "ReturnValue", g[12], "SearchDuration")
ret(22, s[5], "SearchEndTime")
ret(4, s[6], "LastKnownLocation")
var(33, "CharacterMovement", s[10], "self")
value(s[10], "bOrientRotationToMovement", "false")
ret(3, f[24], "Start")
ret(4, f[24], "Target")
ret(24, f[23], "InRot")
link(f[23], "Yaw", f[25], "Yaw")
ret(25, f[26], "NewRotation")
link(q[1], "then_1", f[30], "execute")
link(b[2], "else", s[3], "execute")
chain(s[3], s[23], f[29])
value(s[3], "bHadSight", "false")
var(33, "CharacterMovement", s[23], "self")
value(s[23], "bOrientRotationToMovement", "true")

# Chest-to-muzzle guard and a separate center trace prevent shooting through cover.
var(31, "EnemyMuzzle", f[27], "self")
var(32, "EnemyFlash", f[28], "self")
binary(87, f[2], "ReturnValue", g[21], "LastShotTime")
ret(87, f[88], "A")
value(f[88], "B", 0.12)
ret(88, f[28], "bNewVisibility")
chain(c[1], f[49], f[50], b[4])
ret(3, f[51], "A")
value(f[51], "B", "(X=0,Y=0,Z=30)")
ret(51, f[49], "Start")
ret(27, f[49], "End")
ret(27, f[50], "Start")
ret(6, f[50], "End")
link(f[50], "OutHit", f[52], "Hit")
binary(53, f[52], "HitActor", f[1], "ReturnValue")
ret(49, f[54], "A")
binary(48, f[7], "ReturnValue", g[6], "FireRange")
binary(55, f[54], "ReturnValue", f[53], "ReturnValue")
binary(56, f[55], "ReturnValue", f[48], "ReturnValue")
ret(56, b[4], "Condition")
chain(b[4], s[8], f[35], b[5])
value(s[8], "AIState", "Attack")
ret(0, f[35], "self")
binary(57, f[2], "ReturnValue", g[19], "ReactionEndTime")
binary(60, f[2], "ReturnValue", g[18], "NextShotTime")
binary(58, f[57], "ReturnValue", f[60], "ReturnValue")
ret(58, b[5], "Condition")
chain(b[5], f[33])
link(b[4], "else", f[31], "execute")

# Patrol/search use only home or the last observed location, never a hidden pawn.
chain(c[0], s[7], b[6])
binary(43, f[2], "ReturnValue", g[20], "SearchEndTime")
ret(43, f[44], "bPickA")
value(f[44], "A", "Search")
value(f[44], "B", "Patrol")
ret(44, s[7], "AIState")
binary(41, f[2], "ReturnValue", g[17], "NextMoveTime")
ret(41, b[6], "Condition")
chain(b[6], b[12])
binary(47, f[3], "ReturnValue", g[23], "LastKnownLocation")
ret(47, f[99], "A")
value(f[99], "B", 150)
binary(96, f[43], "ReturnValue", f[99], "ReturnValue")
ret(96, b[12], "Condition")
chain(b[12], s[14], f[32])
var(23, "LastKnownLocation", s[14], "MoveGoal")
link(b[12], "else", f[100], "execute")
binary(45, g[23], "LastKnownLocation", g[22], "HomeLocation")
ret(43, f[45], "bPickA")
binary(46, g[14], "SearchRadius", g[13], "PatrolRadius")
ret(43, f[46], "bPickA")
ret(45, f[38], "Origin")
ret(46, f[38], "Radius")
link(f[38], "RandomLocation", f[100], "Location")
ret(38, f[102], "InBool")
ret(102, f[100], "Success")

# Sample both pure navigation outputs in one call to avoid resampling the result.
chain(c[2], s[9], b[7])
value(s[9], "AIState", "Position")
ret(41, b[7], "Condition")
chain(b[7], f[101])
ret(3, f[39], "Origin")
var(15, "PositionRadius", f[39], "Radius")
link(f[39], "RandomLocation", f[101], "Location")
ret(39, f[103], "InBool")
ret(103, f[101], "Success")
chain(c[5], b[13], s[17], b[14])
link(c[5], "Success", f[104], "A")
value(f[104], "B", 0)
ret(104, b[13], "Condition")
link(c[5], "Location", s[17], "CandidatePosition")
var(28, "bCanSeePlayer", b[14], "Condition")
link(b[13], "else", s[24], "execute")
link(b[14], "else", s[13], "execute")
chain(s[13], f[32])
var(25, "CandidatePosition", s[13], "MoveGoal")
chain(b[14], f[61], f[68], b[18])
var(25, "CandidatePosition", f[62], "A")
value(f[62], "B", "(X=0,Y=0,Z=120)")
ret(62, f[61], "Start")
ret(6, f[61], "End")
link(f[61], "OutHit", f[63], "Hit")
binary(64, f[63], "HitActor", f[1], "ReturnValue")
binary(65, g[25], "CandidatePosition", f[4], "ReturnValue")
binary(66, f[65], "ReturnValue", g[6], "FireRange")
binary(67, f[64], "ReturnValue", f[66], "ReturnValue")
ret(3, f[68], "PathStart")
var(25, "CandidatePosition", f[68], "PathEnd")
link(self_node, "self", f[68], "PathfindingContext")
ret(68, f[105], "Object")
ret(105, b[18], "Condition")
chain(b[18], b[8])
ret(68, f[69], "self")
ret(68, f[71], "self")
ret(69, f[72], "A")
binary(70, f[71], "ReturnValue", f[72], "ReturnValue")
binary(98, f[70], "ReturnValue", f[67], "ReturnValue")
ret(98, b[8], "Condition")
chain(b[8], s[15], f[32])
var(25, "CandidatePosition", s[15], "MoveGoal")
link(b[8], "else", s[14], "execute")
link(b[18], "else", s[14], "execute")

# All movement rejects partial paths, is throttled, and reports rejected requests.
chain(c[4], s[16], f[40], b[10])
binary(42, f[2], "ReturnValue", g[16], "MoveInterval")
ret(42, s[16], "NextMoveTime")
link(casts[0], "AsAIController", f[40], "self")
var(24, "MoveGoal", f[40], "Dest")
value(f[40], "AcceptanceRadius", 80)
for name, text in (
    ("bUsePathfinding", "true"), ("bProjectDestinationToNavigation", "true"),
    ("bStopOnOverlap", "true"), ("bAllowPartialPath", "false")
):
    value(f[40], name, text)
ret(40, f[94], "A")
value(f[94], "B", 0)
ret(94, b[10], "Condition")
chain(b[10], s[24], s[25], s[26], f[92])
ret(42, s[26], "NextMoveTime")
var(30, "MoveFailures", f[91], "A")
value(f[91], "B", 1)
ret(91, s[24], "MoveFailures")
value(s[25], "AIState", "NavigationFailed")
value(f[92], "InString", "Survival enemy navigation failed; retrying after MoveInterval.")

# Slow three-shot bursts. Timings use old BurstShots before updating the counter.
chain(c[3], s[20], s[18], s[19], s[21], f[77], f[89], b[11])
var(29, "BurstShots", f[81], "A")
value(f[81], "B", 1)
ret(81, f[83], "A")
value(f[83], "B", 3)
ret(83, f[85], "bPickA")
binary(85, g[10], "BurstPause", g[9], "ShotInterval")
binary(86, f[2], "ReturnValue", f[85], "ReturnValue")
ret(86, s[20], "NextShotTime")
ret(83, f[84], "bPickA")
value(f[84], "A", 0)
ret(81, f[84], "B")
ret(84, s[18], "BurstShots")
var(27, "ShotsFired", f[82], "A")
value(f[82], "B", 1)
ret(82, s[19], "ShotsFired")
ret(2, s[21], "LastShotTime")
binary(73, f[27], "ReturnValue", f[6], "ReturnValue")
ret(73, f[74], "ConeDir")
var(11, "SpreadDegrees", f[74], "ConeHalfAngleInDegrees")
ret(74, f[75], "A")
var(6, "FireRange", f[75], "B")
binary(76, f[27], "ReturnValue", f[75], "ReturnValue")
ret(27, f[77], "Start")
ret(76, f[77], "End")
link(f[77], "OutHit", f[78], "Hit")
binary(79, f[78], "ImpactPoint", f[78], "TraceEnd")
ret(77, f[79], "bPickA")
link(f[78], "TraceStart", f[89], "LineStart")
ret(79, f[89], "LineEnd")
value(f[89], "LineColor", "(R=1,G=0.25,B=0.05,A=1)")
value(f[89], "Duration", 0.12)
value(f[89], "Thickness", 2)
binary(90, f[78], "HitActor", f[1], "ReturnValue")
ret(90, b[11], "Condition")
chain(b[11], f[80])
link(f[78], "HitActor", f[80], "DamagedActor")
var(8, "EnemyDamage", f[80], "BaseDamage")
link(f[78], "TraceStart", f[108], "From")
link(f[78], "TraceEnd", f[108], "To")
ret(108, f[80], "HitFromDirection")
link(f[77], "OutHit", f[80], "HitInfo")
ret(0, f[80], "EventInstigator")
link(self_node, "self", f[80], "DamageCauser")
value(f[80], "DamageTypeClass", "/Script/Engine.DamageType")

chain(e[3], f[34], b[9], s[11], f[36], f[37])
link(e[3], "Damage", f[34], "Damage")
var(0, "HealthComponent", f[34], "self")
var(2, "bDead", b[9], "Condition")
value(s[11], "AIState", "Dead")
ret(0, f[36], "self")
var(32, "EnemyFlash", f[37], "self")
value(f[37], "bNewVisibility", "false")
for index in (13, 49, 50, 61, 77):
    value(f[index], "TraceChannel", "TraceTypeQuery1")
    value(f[index], "bIgnoreSelf", "true")
    value(f[index], "DrawDebugType", "None")
for index in (92, 93):
    value(f[index], "bPrintToLog", "true")
    value(f[index], "bPrintToScreen", "true")

for group, x0, width, columns in (
    (f, 0, 520, 6), (g, -2400, 380, 4), (s, 3600, 420, 4),
    (b, 5600, 380, 3), (e, -3400, 460, 1),
    (c, -4100, 460, 1), (casts, -4900, 650, 1), (q, -5500, 400, 1),
):
    for i, n in group.items():
        n.set_node_pos(unreal.IntPoint(x0 + (i % columns) * width, (i // columns) * 640))
self_node.set_node_pos(unreal.IntPoint(-2400, -500))

unreal.BlueprintEditorLibrary.compile_blueprint(bp)
assert bp.status == unreal.BlueprintStatus.BS_UP_TO_DATE, bp.status
unreal.get_default_object(bp.generated_class()).capsule_component.set_collision_response_to_channel(
    unreal.CollisionChannel.ECC_VISIBILITY, unreal.CollisionResponseType.ECR_BLOCK)
assert unreal.EditorAssetLibrary.save_loaded_asset(bp, only_if_is_dirty=False)
player_bp = unreal.load_asset("/Game/Shooter/Blueprints/BP_SurvivalCharacter")
unreal.get_default_object(player_bp.generated_class()).capsule_component.set_collision_response_to_channel(
    unreal.CollisionChannel.ECC_VISIBILITY, unreal.CollisionResponseType.ECR_BLOCK)
assert unreal.EditorAssetLibrary.save_loaded_asset(player_bp, only_if_is_dirty=False)
hud_bp = unreal.load_asset("/Game/Shooter/Blueprints/BP_SurvivalHUD")
hud_begin = unreal.load_object(None, hud_bp.get_path_name() + ":EventGraph.K2Node_Event_0")
hud_input = unreal.load_object(None, hud_bp.get_path_name() + ":EventGraph.K2Node_CallFunction_51")
hud_controller = unreal.load_object(None, hud_bp.get_path_name() + ":EventGraph.K2Node_CallFunction_33")
PINS.break_pin_links(pin(hud_input, "execute"))
PINS.break_pin_links(pin(hud_input, "PlayerController"))
chain(hud_begin, hud_input)
link(hud_controller, "ReturnValue", hud_input, "PlayerController")
hud_input.set_node_pos(unreal.IntPoint(350, 0))
unreal.BlueprintEditorLibrary.compile_blueprint(hud_bp)
assert hud_bp.status == unreal.BlueprintStatus.BS_UP_TO_DATE, hud_bp.status
unreal.get_default_object(hud_bp.generated_class()).set_editor_property(
    "auto_receive_input", unreal.AutoReceiveInput.DISABLED)
assert unreal.EditorAssetLibrary.save_loaded_asset(hud_bp, only_if_is_dirty=False)
print("Survival enemy Blueprint wired and saved.")
