"""Assert original Part 3 measurements and the empty-fire auto-reload follow-up."""

import json
import os
import unreal

directory = os.path.join(unreal.Paths.project_saved_dir(), "Automation")
with open(os.path.join(directory, "SurvivalRifleRaw.json"), encoding="utf-8") as source:
    raw = json.load(source)
samples = raw["samples"]


def phase(name):
    values = [s for s in samples if s["phase"] == name]
    assert values, name
    return values


magazine = phase("magazine")
shots = {}
for sample in magazine:
    if sample["shots"] > 0:
        shots.setdefault(sample["shots"], sample["time"])
assert sorted(shots) == list(range(1, 31)), shots
interval = (shots[30] - shots[1]) / 29
assert abs(interval - 1 / 6) < .01, interval
assert magazine[0]["ammo"] == 30 and magazine[-1]["ammo"] == 0
assert any(s["last_damage"] == 20 for s in magazine)
assert all(s["last_damage"] in (0, 20) for s in samples)
assert any(s["aiming"] and abs(s["camera_fov"] - 65) < .1
           and s["walk_speed"] == 250 for s in magazine)
assert any(s["flash_visible"] for s in magazine)
assert not magazine[-1]["flash_visible"]

reload = next(s for s in samples if s["reloading"])
complete = next(s for s in samples
                if s["time"] > reload["time"] and not s["reloading"])
reload_seconds = complete["time"] - reload["time"]
assert 2 <= reload_seconds < 2.1, reload_seconds
assert reload["reload_end"] == reload["time"] + 2
assert all(s["shots"] == reload["shots"] for s in samples if s["reloading"])
assert complete["shots"] == reload["shots"] + 1 and complete["ammo"] == 29
assert reload["time"] - shots[30] > 1, "Need an empty-held-input observation period."
full = phase("full-magazine-reload")
assert all(s["ammo"] == 30 and not s["reloading"] for s in full)

for name in ("cover-blocking", "protruding-barrel"):
    values = phase(name)
    assert values[-1]["shots"] - values[0]["shots"] >= 5
    assert all(s["last_damage"] == 0 for s in values), name
assert all(s["last_damage"] == 20 for s in phase("uncovered-control"))

idle = phase("release-idle-confirm")
assert idle[0]["ammo"] > 0
assert raw["final"]["shots"] == idle[0]["shots"]
assert raw["final"]["time"] - idle[0]["time"] >= 1
assert idle[0]["camera_fov"] == 90 and idle[0]["walk_speed"] == 500
normal_ammo = [s["ammo"] for s in samples
               if s["phase"] not in ("release-nonempty", "release-idle-confirm")]
assert all(0 <= ammo <= 30 for ammo in normal_ammo)

with open(os.path.join(directory, "SurvivalAutoReloadRaw.json"), encoding="utf-8") as source:
    auto_samples = json.load(source)
assert auto_samples[0]["ammo"] == 0 and not auto_samples[0]["reloading"]
reload_durations = []
for index, start in enumerate(auto_samples):
    if not start["reloading"] or (index > 0 and auto_samples[index - 1]["reloading"]):
        continue
    end = next((s for s in auto_samples[index + 1:] if not s["reloading"]), None)
    if end is None:
        continue
    assert start["ammo"] == 0
    assert start["reload_end"] == start["time"] + 2
    duration = end["time"] - start["time"]
    assert 2 <= duration < 2.15
    during = [s for s in auto_samples if start["time"] <= s["time"] < end["time"]]
    assert all(s["shots"] == start["shots"] and s["reload_end"] == start["reload_end"]
               for s in during)
    assert end["shots"] == start["shots"] + 1 and end["ammo"] == 29
    reload_durations.append(duration)
assert len(reload_durations) >= 2
assert all(0 <= s["ammo"] <= 30 for s in auto_samples)

assert unreal.EditorLevelLibrary.get_game_world() is None, "Finish PIE before final validation."
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
assert len(actors) == 925
assert not any(a.get_actor_label().startswith("TEMP_Rifle") for a in actors)
for name in ("BP_SurvivalCharacter", "BP_SurvivalHUD", "BP_SurvivalGameMode"):
    blueprint = unreal.load_asset("/Game/Shooter/Blueprints/" + name)
    assert blueprint.status == unreal.BlueprintStatus.BS_UP_TO_DATE
character = unreal.load_asset("/Game/Shooter/Blueprints/BP_SurvivalCharacter")
defaults = unreal.get_default_object(character.generated_class())
assert defaults.get_editor_property("Ammo") == 30
assert not defaults.get_editor_property("bReloading")
assert defaults.get_editor_property("ShotsFired") == 0
assert isinstance(defaults.get_editor_property("NextShotTime"), float)
assert isinstance(defaults.get_editor_property("ReloadEndTime"), float)

report = {
    "passed": True,
    "shots_per_second_measured": 1 / interval,
    "mean_shot_interval_seconds": interval,
    "first_magazine_shots": 30,
    "empty_magazine_blocks_firing": True,
    "point_damage_received": 20,
    "reload_seconds_measured": reload_seconds,
    "firing_blocked_during_reload": True,
    "refill": "30; held fire immediately consumes one round on completion",
    "full_magazine_reload_rejected": True,
    "cover_blocks_damage": True,
    "protruding_barrel_guard_blocks_damage": True,
    "uncovered_positive_control_damage": 20,
    "release_stops_firing_with_ammunition_remaining": True,
    "aim_and_normal_camera_movement_preserved": True,
    "muzzle_flash_visibility_toggles": True,
    "blueprints_compiled": True,
    "default_ammo": 30,
    "temporary_test_actors_removed": True,
    "saved_map_actor_count": 925,
    "auto_reload_when_firing_empty": True,
    "auto_reload_durations_seconds": reload_durations,
    "notes": [
        "The release test temporarily used 300 runtime rounds to avoid MCP latency exhausting 30.",
        "The HUD screenshot uses a synthetic 17-round reloading state; timing is measured separately.",
        "Tracer and impact markers are development debug visuals; muzzle flash is an emissive mesh.",
        "Temporary target and cover actors were removed before saving/reloading the gameplay map.",
        "User approval is still pending; health and enemy gameplay are separate milestones.",
        "Original rifle measurements precede auto reload; separate follow-up validates the new behavior.",
    ],
}
path = os.path.join(directory, "SurvivalRifle.json")
with open(path, "w", encoding="utf-8") as output:
    json.dump(report, output, indent=2)
print(json.dumps(report))
