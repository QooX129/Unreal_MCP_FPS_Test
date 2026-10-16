"""Validate live spawning, floor coverage, replacement timing, and population ramp."""

import builtins
import json
import os
import time
import traceback
import unreal

assert not hasattr(builtins, "_survival_spawner_test")
world = unreal.EditorLevelLibrary.get_game_world()
assert world
spawner_class = unreal.load_class(
    None, "/Game/Shooter/Blueprints/BP_SurvivalSpawner.BP_SurvivalSpawner_C"
)
enemy_class = unreal.load_class(
    None, "/Game/Shooter/Blueprints/BP_SurvivalEnemy.BP_SurvivalEnemy_C"
)
health_class = unreal.load_class(
    None, "/Game/Shooter/Blueprints/BP_SurvivalHealth.BP_SurvivalHealth_C"
)
spawners = unreal.GameplayStatics.get_all_actors_of_class(world, spawner_class)
assert len(spawners) == 1
spawner = spawners[0]
state = {
    "stage": "initial",
    "started": time.monotonic(),
    "round": 0,
    "results": {},
    "samples": [],
}
builtins._survival_spawner_test = state


def game_time():
    return unreal.SystemLibrary.get_game_time_in_seconds(spawner)


def all_enemies():
    return unreal.GameplayStatics.get_all_actors_of_class(world, enemy_class)


def living_enemies():
    result = []
    for actor in all_enemies():
        health = actor.get_component_by_class(health_class)
        if health and health.get_editor_property("Health") > 0:
            result.append(actor)
    return result


def freeze(actor):
    actor.set_actor_tick_enabled(False)
    controller = actor.get_controller()
    if controller:
        controller.stop_movement()
    actor.character_movement.set_editor_property("max_walk_speed", 0.0)


def freeze_all():
    for actor in living_enemies():
        freeze(actor)


def damage(actor, amount):
    player = unreal.GameplayStatics.get_player_pawn(world, 0)
    pc = unreal.GameplayStatics.get_player_controller(world, 0)
    return unreal.GameplayStatics.apply_damage(
        actor, amount, pc, player, unreal.DamageType
    )


def finish(passed, error=None):
    if state.get("handle"):
        unreal.unregister_slate_post_tick_callback(state["handle"])
    state["results"]["passed"] = passed
    if error:
        state["results"]["error"] = error
        unreal.log_error("Survival spawner test failed: " + error)
    path = os.path.join(
        unreal.Paths.project_saved_dir(), "Automation", "SurvivalSpawner.json"
    )
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as output:
        json.dump({"results": state["results"], "samples": state["samples"]}, output, indent=2)
    builtins._survival_spawner_report = state
    if hasattr(builtins, "_survival_spawner_test"):
        del builtins._survival_spawner_test
    unreal.log("Survival spawner test finished: " + json.dumps(state["results"]))


def kill_population(round_number):
    enemies = living_enemies()
    assert len(enemies) == spawner.get_editor_property("AliveCount")
    assert enemies
    state["round"] = round_number
    state["round_kills"] = len(enemies)
    state["kills_before"] = spawner.get_editor_property("TotalKills")
    target_before = spawner.get_editor_property("TargetPopulation")
    progress_before = spawner.get_editor_property("KillsSinceRamp")
    for actor in enemies:
        freeze(actor)
        damage(actor, 1000)
    state["death_time"] = game_time()
    assert spawner.get_editor_property("AliveCount") == 0
    assert spawner.get_editor_property("TotalKills") == (
        state["kills_before"] + state["round_kills"]
    )
    expected_ramps, expected_progress = divmod(
        progress_before + state["round_kills"],
        spawner.get_editor_property("RampKills"),
    )
    expected_target = target_before + expected_ramps
    assert spawner.get_editor_property("TargetPopulation") == expected_target
    assert spawner.get_editor_property("KillsSinceRamp") == expected_progress
    state["replacement_delay"] = spawner.get_editor_property("ReplacementDelay")
    state["replacement_due"] = spawner.get_editor_property("NextSpawnTime")
    assert abs(
        state["replacement_due"]
        - (state["death_time"] + state["replacement_delay"])
    ) < 0.1
    state["stage"] = "replacement-delay"


def validate_initial_wave():
    player = unreal.GameplayStatics.get_player_pawn(world, 0)
    pc = unreal.GameplayStatics.get_player_controller(world, 0)
    assert player and pc
    player_health = player.get_component_by_class(health_class)
    assert player_health and not player_health.get_editor_property("bDead")
    player_health.set_editor_property("bRegenerates", False)

    enemies = living_enemies()
    assert len(enemies) == 3
    assert spawner.get_editor_property("AliveCount") == 3
    assert spawner.get_editor_property("TargetPopulation") == 3
    camera = unreal.GameplayStatics.get_player_camera_manager(world, 0)
    camera_location = camera.get_camera_location()
    camera_forward = unreal.MathLibrary.get_forward_vector(camera.get_camera_rotation())
    player_location = player.get_actor_location()
    floor_centers = (-347.0, 93.0, 513.0)
    matched = set()
    dots = []
    for actor in enemies:
        freeze(actor)
        location = actor.get_actor_location()
        floor_index = min(range(3), key=lambda index: abs(location.z - floor_centers[index]))
        assert abs(location.z - floor_centers[floor_index]) <= 50, location
        matched.add(floor_index)
        nav_location = unreal.Vector(location.x, location.y, location.z - 88.0)
        distance = unreal.MathLibrary.vector_distance(player_location, nav_location)
        assert distance >= 1200.0, distance
        direction = unreal.MathLibrary.get_direction_unit_vector(
            camera_location, location
        )
        dots.append(unreal.MathLibrary.dot_vector_vector(camera_forward, direction))
        health = actor.get_component_by_class(health_class)
        assert health.get_editor_property("Health") == 100
    assert matched == {0, 1, 2}, matched
    state["results"].update(
        initial_population=3,
        initial_floor_count=3,
        minimum_spawn_distance_cm=1200,
        initial_view_dots=dots,
    )
    kill_population(1)


def step():
    t = game_time()
    freeze_all()
    living = living_enemies()
    current_alive = spawner.get_editor_property("AliveCount")
    target = spawner.get_editor_property("TargetPopulation")
    total_kills = spawner.get_editor_property("TotalKills")
    state["samples"].append({
        "time": t,
        "stage": state["stage"],
        "living": len(living),
        "alive_count": current_alive,
        "target": target,
        "kills": total_kills,
        "attempts": spawner.get_editor_property("SpawnAttempts"),
    })
    assert len(living) == current_alive, (len(living), current_alive)
    assert 0 <= current_alive <= target
    assert target >= 3
    assert len(all_enemies()) == len(living), "Dead enemies should be removed immediately."

    if state["stage"] == "initial":
        if current_alive == 3:
            validate_initial_wave()
        elif t > 15:
            raise AssertionError(("Initial wave did not reach 3", current_alive))
    elif state["stage"] == "replacement-delay":
        elapsed = t - state["death_time"]
        assert current_alive == 0
        if elapsed < state["replacement_delay"] - 0.1:
            assert not living, ("Replacement spawned too early", elapsed)
        if elapsed >= state["replacement_delay"] - 0.1:
            state["stage"] = "replacement-wave"
    elif state["stage"] == "replacement-wave":
        if living and "first_replacement_time" not in state:
            state["first_replacement_time"] = t
            elapsed = t - state["death_time"]
            assert state["replacement_delay"] <= elapsed <= (
                state["replacement_delay"] + 7.0
            ), elapsed
        if current_alive == target:
            elapsed = state["first_replacement_time"] - state["death_time"]
            state["results"]["replacement_first_spawn_seconds"].append(elapsed)
            if target <= 6:
                kill_population(state["round"] + 1)
                state.pop("first_replacement_time", None)
            else:
                assert current_alive == target and len(living) == target
                state["uncapped_target"] = target
                state["population_since"] = t
                state["stage"] = "uncapped-population"
    elif state["stage"] == "uncapped-population":
        assert target == state["uncapped_target"]
        assert current_alive == target and len(living) == target
        if t - state["population_since"] >= 1.5:
            state["results"]["population_beyond_previous_limit"] = current_alive
            player = unreal.GameplayStatics.get_player_pawn(world, 0)
            player_health = player.get_component_by_class(health_class)
            damage(player, 1000)
            assert player_health.get_editor_property("bDead")
            victim = living[0]
            damage(victim, 1000)
            state["dead_player_alive_count"] = spawner.get_editor_property("AliveCount")
            state["dead_player_spawn_count"] = len(living_enemies())
            state["death_time"] = game_time()
            state["stage"] = "dead-player"
    elif state["stage"] == "dead-player":
        assert current_alive == state["dead_player_alive_count"]
        assert len(living) == state["dead_player_spawn_count"]
        if t - state["death_time"] >= 5.5:
            state["results"]["no_replacement_after_player_death_seconds"] = (
                t - state["death_time"]
            )
            state["stage"] = "restart-ready"
            state["results"]["awaiting_enter_restart"] = True
            finish(True)


def tick(delta):
    if state["stage"] == "restart-ready":
        return
    try:
        assert time.monotonic() - state["started"] < 150, "Spawner test timed out."
        step()
    except Exception:
        finish(False, traceback.format_exc())


state["results"]["replacement_first_spawn_seconds"] = []
state["handle"] = unreal.register_slate_post_tick_callback(tick)
print("Survival spawner PIE validation started.")
