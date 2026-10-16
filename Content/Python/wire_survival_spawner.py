"""Wire and save the Blueprint-based survival enemy spawner."""

import unreal

bp = unreal.load_asset("/Game/Shooter/Blueprints/BP_SurvivalSpawner")
assert bp
pins = unreal.BlueprintGraphPinLibrary


def nodes(kind, count):
    result = {}
    for index in range(count):
        path = bp.get_path_name() + ":EventGraph.K2Node_" + kind + "_" + str(index)
        result[index] = unreal.load_object(None, path)
        assert result[index], path
    return result


functions = nodes("CallFunction", 65)
functions[70] = unreal.load_object(
    None, bp.get_path_name() + ":EventGraph.K2Node_CallFunction_70"
)
assert functions[70]
getters = nodes("VariableGet", 30)
setters = nodes("VariableSet", 20)
branches = nodes("IfThenElse", 11)
events = nodes("Event", 3)
custom_events = nodes("CustomEvent", 3)
casts = nodes("DynamicCast", 1)


def pin(node, name, output=False):
    result = node.find_output_pin(name) if output else node.find_input_pin(name)
    assert result is not None, (node.get_name(), name)
    return result


def link(source, output_name, target, input_name):
    assert pins.try_create_connection(
        pin(source, output_name, True), pin(target, input_name)
    ), (source.get_name(), output_name, target.get_name(), input_name)


def value(node, name, text):
    assert pins.set_pin_value(pin(node, name), str(text)), (
        node.get_name(),
        name,
        text,
    )


def sequence(*items):
    for source, target in zip(items, items[1:]):
        link(source, "then", target, "execute")


for group in (functions, getters, setters, branches, events, custom_events, casts):
    for node in group.values():
        for graph_pin in node.list_all_pins():
            pins.break_pin_links(graph_pin)

f, g, s, b, e, c, cast = (
    functions,
    getters,
    setters,
    branches,
    events,
    custom_events,
    casts[0],
)

# Start the wave on the first tick where the player is alive and available.
link(e[0], "then", s[8], "execute")
link(g[1], "InitialPopulation", s[8], "TargetPopulation")

link(e[2], "then", cast, "execute")
link(f[6], "ReturnValue", cast, "Object")
link(cast, "then", b[1], "execute")
link(f[62], "ReturnValue", b[1], "Condition")
link(f[36], "ReturnValue", f[62], "A")
link(f[61], "ReturnValue", f[62], "B")
link(f[6], "ReturnValue", f[36], "Object")
link(cast, "AsBP Survival Character", g[28], "self")
link(g[28], "HealthComponent", g[29], "self")
link(g[29], "bDead", f[61], "A")
link(g[27], "bInitialWaveStarted", b[2], "Condition")
link(b[1], "then", b[2], "execute")

# Initial population samples each of the three floor elevations once.
link(b[2], "else", s[19], "execute")
value(s[19], "bInitialWaveStarted", "true")
sequence(s[19], s[0], f[32], s[1], f[33], s[2], f[34], s[3])
value(s[0], "PreferredFloor", 0)
value(s[1], "PreferredFloor", 1)
value(s[2], "PreferredFloor", 2)
value(s[3], "PreferredFloor", -1)

# Once the initial wave is started, replenish on the configured cadence.
link(b[2], "then", b[3], "execute")
link(f[38], "ReturnValue", b[3], "Condition")
link(g[2], "AliveCount", f[38], "A")
link(g[3], "TargetPopulation", f[38], "B")
link(b[3], "then", b[4], "execute")
link(f[39], "ReturnValue", b[4], "Condition")
link(f[7], "ReturnValue", f[39], "A")
link(g[10], "NextSpawnTime", f[39], "B")
link(b[4], "then", s[18], "execute")
value(s[18], "PreferredFloor", -1)
link(s[18], "then", f[35], "execute")

# Choose the requested floor for the initial wave or a random floor afterward.
value(f[11], "Min", 0)
value(f[11], "Max", 2)
link(g[20], "PreferredFloor", f[49], "A")
value(f[49], "B", 0)
link(f[11], "ReturnValue", f[13], "A")
link(g[20], "PreferredFloor", f[13], "B")
link(f[49], "ReturnValue", f[13], "bPickA")

link(f[13], "ReturnValue", f[10], "A")
value(f[10], "B", 0)
link(f[13], "ReturnValue", f[50], "A")
value(f[50], "B", 2)

# Floor seeds share the editable arena center, but keep vertical levels separate.
link(g[21], "SpawnOrigin", f[55], "InVec")
link(f[55], "X", f[21], "X")
link(f[55], "Y", f[21], "Y")
value(f[21], "Z", -435)
link(f[55], "X", f[54], "X")
link(f[55], "Y", f[54], "Y")
value(f[54], "Z", 5)
value(f[58], "X", 2250)
value(f[58], "Y", 1380)
value(f[58], "Z", 425)
link(f[21], "ReturnValue", f[14], "A")
link(f[54], "ReturnValue", f[14], "B")
link(f[10], "ReturnValue", f[14], "bPickA")
link(f[58], "ReturnValue", f[17], "A")
link(f[14], "ReturnValue", f[17], "B")
link(f[50], "ReturnValue", f[17], "bPickA")

# Sample reachable navigation points and reject candidates from other floors.
link(f[17], "ReturnValue", f[20], "Origin")
link(g[15], "SpawnRadius", f[20], "Radius")
link(f[17], "ReturnValue", f[57], "InVec")
link(f[20], "RandomLocation", f[16], "InVec")
link(f[57], "Z", f[25], "A")
value(f[25], "B", 50)
link(f[57], "Z", f[27], "A")
value(f[27], "B", 50)
link(f[16], "Z", f[37], "A")
link(f[25], "ReturnValue", f[37], "B")
link(f[16], "Z", f[42], "A")
link(f[27], "ReturnValue", f[42], "B")
link(f[37], "ReturnValue", f[43], "A")
link(f[42], "ReturnValue", f[43], "B")

# Keep spawns away from the player and prefer locations outside the camera view.
link(f[6], "ReturnValue", f[47], "self")
link(f[47], "ReturnValue", f[4], "V1")
link(f[20], "RandomLocation", f[4], "V2")
link(f[4], "ReturnValue", f[23], "A")
link(g[14], "MinimumSpawnDistance", f[23], "B")
link(f[43], "ReturnValue", f[44], "A")
link(f[23], "ReturnValue", f[44], "B")

link(f[8], "ReturnValue", f[9], "self")
link(f[8], "ReturnValue", f[12], "self")
link(f[12], "ReturnValue", f[3], "InRot")
link(f[9], "ReturnValue", f[19], "From")
link(f[20], "RandomLocation", f[19], "To")
link(f[3], "ReturnValue", f[15], "A")
link(f[19], "ReturnValue", f[15], "B")
link(f[15], "ReturnValue", f[48], "A")
link(g[16], "OffscreenDot", f[48], "B")
link(g[13], "SpawnAttempts", f[41], "A")
link(g[12], "MaxAttemptsBeforeVisible", f[41], "B")
link(f[48], "ReturnValue", f[40], "A")
link(f[41], "ReturnValue", f[40], "B")
link(f[44], "ReturnValue", f[46], "A")
link(g[20], "PreferredFloor", f[28], "A")
value(f[28], "B", 0)
link(f[40], "ReturnValue", f[70], "A")
link(f[28], "ReturnValue", f[70], "B")
link(f[70], "ReturnValue", f[46], "B")

# Spawn only after nav, floor, clearance, distance, and view checks pass.
link(c[2], "then", b[5], "execute")
link(f[20], "ReturnValue", b[5], "Condition")
link(b[5], "then", b[6], "execute")
link(f[46], "ReturnValue", b[6], "Condition")
link(b[6], "then", f[0], "execute")
value(
    f[0],
    "ActorClass",
    "BP_SurvivalEnemy_C'/Game/Shooter/Blueprints/BP_SurvivalEnemy.BP_SurvivalEnemy_C'",
)
value(f[0], "CollisionHandlingOverride", "AdjustIfPossibleButDontSpawnIfColliding")
link(f[20], "RandomLocation", f[22], "A")
value(f[22], "B", "(X=0,Y=0,Z=88)")
link(f[22], "ReturnValue", f[24], "Location")
link(f[24], "ReturnValue", f[0], "SpawnTransform")
link(f[0], "ReturnValue", f[64], "Object")
link(f[0], "then", b[7], "execute")
link(f[64], "ReturnValue", b[7], "Condition")
link(b[7], "then", f[1], "execute")
link(f[0], "ReturnValue", f[1], "Actor")
link(f[24], "ReturnValue", f[1], "SpawnTransform")

# Successful spawns update the living population and throttle subsequent spawns.
link(f[1], "then", s[6], "execute")
link(g[4], "AliveCount", f[59], "A")
value(f[59], "B", 1)
link(f[59], "ReturnValue", s[6], "AliveCount")
value(s[11], "SpawnAttempts", 0)
sequence(s[6], s[11], s[5])
link(g[18], "SpawnInterval", f[56], "B")
link(f[7], "ReturnValue", f[56], "A")
link(f[56], "ReturnValue", s[5], "NextSpawnTime")

# Failed nav, candidate, or collision checks count toward bounded visible fallback.
link(b[5], "else", s[7], "execute")
link(b[6], "else", s[7], "execute")
link(b[7], "else", s[7], "execute")
link(g[13], "SpawnAttempts", f[53], "A")
value(f[53], "B", 1)
link(f[53], "ReturnValue", s[7], "SpawnAttempts")

# Enemy deaths schedule replacement and ramp the target every three kills.
link(c[0], "then", s[13], "execute")
link(g[0], "AliveCount", f[29], "A")
value(f[29], "B", 1)
link(f[29], "ReturnValue", s[13], "AliveCount")
link(g[9], "TotalKills", f[30], "A")
value(f[30], "B", 1)
link(g[22], "KillsSinceRamp", f[31], "A")
value(f[31], "B", 1)
sequence(s[13], s[17], s[16], b[8])
link(f[30], "ReturnValue", s[17], "TotalKills")
link(f[31], "ReturnValue", s[16], "KillsSinceRamp")
link(s[16], "Output_Get", f[51], "A")
link(g[11], "RampKills", f[51], "B")
link(f[51], "ReturnValue", b[8], "Condition")
link(b[8], "then", s[15], "execute")
value(s[15], "KillsSinceRamp", 0)
link(s[15], "then", s[12], "execute")
link(g[24], "TargetPopulation", f[52], "A")
value(f[52], "B", 1)
link(f[52], "ReturnValue", s[12], "TargetPopulation")
link(s[12], "then", s[14], "execute")
link(b[8], "else", s[14], "execute")
link(f[7], "ReturnValue", f[60], "A")
link(g[17], "ReplacementDelay", f[60], "B")
link(f[60], "ReturnValue", s[14], "NextSpawnTime")

lib = unreal.BlueprintEditorLibrary
lib.compile_blueprint(bp)
assert bp.status == unreal.BlueprintStatus.BS_UP_TO_DATE, bp.status
cdo = unreal.get_default_object(bp.generated_class())
cdo.set_editor_property("SpawnOrigin", unreal.Vector(2250, 3000, 5))
cdo.set_editor_property("bInitialWaveStarted", False)
cdo.set_actor_tick_interval(0.5)
assert unreal.EditorAssetLibrary.save_loaded_asset(bp, only_if_is_dirty=False)
print("Compiled and saved BP_SurvivalSpawner with uncapped population growth.")
