"""Arrange a PIE-only health-bar review; stop PIE to discard the fixture."""

import unreal

world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
assert world, "Start PIE before running this visual check."
player = unreal.GameplayStatics.get_player_pawn(world, 0)
controller = unreal.GameplayStatics.get_player_controller(world, 0)
assert controller.get_hud().get_class().get_name() == "SurvivalCombatHUD"
enemy_class = unreal.load_class(
    None, "/Game/Shooter/Blueprints/BP_SurvivalEnemy.BP_SurvivalEnemy_C"
)
health_class = unreal.load_class(
    None, "/Game/Shooter/Blueprints/BP_SurvivalHealth.BP_SurvivalHealth_C"
)
enemies = unreal.GameplayStatics.get_all_actors_of_class(world, enemy_class)
assert enemies
for enemy in enemies:
    enemy.set_actor_tick_enabled(False)
    ai = enemy.get_controller()
    if ai:
        ai.stop_movement()
        ai.set_actor_tick_enabled(False)

player.set_actor_location(unreal.Vector(1400, 2200, 95), False, True)
controller.set_control_rotation(unreal.Rotator(-7, 0, 0))
enemy = enemies[0]
enemy.set_actor_location(unreal.Vector(2000, 2200, 95), False, True)
enemy.set_actor_rotation(unreal.Rotator(0, 180, 0), True)
health = player.get_component_by_class(health_class)
assert not health.get_editor_property("bDead"), "Run this check on a fresh PIE player."
unreal.GameplayStatics.apply_damage(player, 50, controller, player, unreal.DamageType)
assert health.get_editor_property("Health") == 50
mesh = enemy.get_component_by_class(unreal.SkeletalMeshComponent)
assert mesh.does_socket_exist("head")
head = mesh.get_socket_location("head")
anchor = head + unreal.Vector(0, 0, 22)
assert anchor.z - head.z == 22
unreal.log("HUD bar review ready: half player HP; enemy head anchor +22 cm.")
