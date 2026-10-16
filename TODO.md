# Atrium Survival Shooter - TODO

Last updated: 2026-10-16

## Workflow

- Implement the main parts below in order.
- Validate each part, then pause for the user's check.
- Mark a part complete only after explicit user approval.
- Do not start the next part until the current part is approved.
- Keep this document updated as implementation and approvals progress.

**Current state: All eight parts are complete and user approved.**
Final playtest approval received on 2026-10-16.

## Project scope

Single-player third-person survival shooter, using editable Blueprints where
practical. Greybox weapons, characters, and effects are acceptable. Multiplayer,
finished art, and polished weapon animations are out of scope for this prototype.

- Gameplay map: [Lvl_AtriumSurvival](Content/Shooter/Maps/Lvl_AtriumSurvival.umap)
  (`/Game/Shooter/Maps/Lvl_AtriumSurvival`)
- Preserved architectural map:
  [Lvl_ConcreteAtrium](Content/Greybox/Lvl_ConcreteAtrium.umap)
- Gameplay Blueprints: [Shooter Blueprints](Content/Shooter/Blueprints/)

## Progress summary

| Part | Main task | Status |
| --- | --- | --- |
| 1 | Expand the gameplay arena | Complete - user approved |
| 2 | Player camera and aiming | Complete - user approved |
| 3 | Automatic rifle and shooting | Complete - user approved |
| 4 | Health, regeneration, and death | Complete - user approved |
| 5 | Enemy perception and combat | Complete - user approved |
| 6 | Random survival spawning | Complete - user approved |
| 7 | Complete combat HUD | Complete - user approved |
| 8 | End-to-end playtest and finalization | Complete - user approved |

## Main tasks

### 1. Expand the gameplay arena

- [x] Create a separate gameplay copy; preserve the architectural original.
- [x] Extend the right-hand gallery into an approximately 60 x 40 m arena.
- [x] Connect lower, main, and upper floors with two stair routes.
- [x] Add gallery openings, cover, firing positions, and flank routes.
- [x] Configure collision, navigation, and the existing third-person character.
- [x] Validate: all four stair flights passed actual character movement tests;
      ten navigation checks passed, including after saving and reloading.
- [x] User approval received.

### 2. Player camera and aiming

- [x] Create separate Survival Character, HUD, and GameMode Blueprints.
- [x] Preserve the existing third-person movement and original character defaults.
- [x] Add right-shoulder camera and centered crosshair.
- [x] Hold right mouse to aim; release to restore normal movement and view.
- [x] Smoothly interpolate camera distance and field of view.
- [x] Face the aim direction while aiming.
- [x] Trace from the camera to the crosshair target, then from the right hand
      toward that target to respect nearby cover.
- [x] Validate pressed/released input transitions, centered crosshair, and
      hand-origin obstruction against low cover in Play in Editor.
- [x] User approval received on 2026-10-15.

Current tuning:

| Setting | Normal | Aiming |
| --- | --- | --- |
| Camera arm length | 380 cm | 220 cm |
| Field of view | 90 degrees | 65 degrees |
| Movement speed | 500 cm/s | 250 cm/s |
| Character facing | Movement direction | Controller aim direction |

Shoulder offset: `(0, 65, 65)` cm. Aim trace range: 200 m.
Part 3 has replaced the temporary right-hand aim origin with the rifle muzzle.
A separate hand-to-muzzle guard prevents the barrel firing through nearby cover.

**User check:** press Play in the gameplay map, test WASD and mouse look, then
hold/release right mouse. Check camera height, shoulder offset, zoom, movement
speed, and the crosshair.

- [Normal-view preview](Saved/Screenshots/WindowsEditor/SurvivalAiming_Part2_Hip.png)
- [Aiming preview](Saved/Screenshots/WindowsEditor/SurvivalAiming_Part2_Aim.png)

### 3. Automatic rifle and shooting

- [x] Add a hand-following greybox rifle with a separate muzzle component.
- [x] Hold left mouse for automatic hitscan fire toward the crosshair.
- [x] Use the rifle muzzle for the obstruction trace; nearby cover blocks shots.
- [x] Add a hand-to-muzzle guard against firing from a protruding barrel.
- [x] Set 20 damage per shot and 6 shots per second.
- [x] Add a 30-round magazine with unlimited reserve ammunition.
- [x] Press R to reload; initial reload duration is 2 seconds.
- [x] Automatically start the same reload when holding/pressing fire at 0 ammo.
      Holding fire resumes shooting after reload; no input at 0 ammo stays idle.
- [x] Add emissive muzzle flash, prototype tracer/impact markers, and ammo display.
- [x] Validate firing, obstruction, fire rate, magazine limit, and reloading.
- [x] Save/reload the gameplay map, verify a fresh PIE start, and remove test actors.
- [x] User approval received on 2026-10-15.

Validation results:

- A full magazine fires exactly 30 shots before reloading; ammunition never goes
  negative. Updated empty-fire behavior automatically reloads instead of staying
  empty while fire is held.
- Mean interval: 0.16645 seconds, or approximately 6.008 shots per second.
- A Blueprint test receiver received exactly 20 point damage.
- Reload measured 2.007 seconds. Holding fire during reload caused no shots
  until completion, then firing resumed with the refilled magazine.
- Pressing R with a full magazine did not start a reload.
- Normal cover blocked damage. A low wall between the hand and muzzle also
  blocked damage even with the muzzle protruding beyond it and the camera
  seeing the target. Removing cover restored damage.
- Releasing left mouse stopped firing with ammunition remaining. This test
  temporarily extended runtime ammunition to avoid MCP latency exhausting the
  magazine; saved/default ammunition remains 30.
- Right-mouse aiming, normal camera/movement, and flash visibility passed checks.
- Fresh PIE after saving/reloading started at 30 rounds, not reloading, with
  no test targets. Gameplay map remains 925 actors.
- Auto-reload follow-up: three successive held-fire reloads measured
  2.000-2.002 seconds, without resetting the reload deadline or firing during
  reload. Firing resumed after each refill; manual R reload still refilled a
  partial magazine to 30.

Prototype presentation: the rifle follows the existing right-hand animation
and rotates toward the crosshair; a raised two-handed rifle pose and reload
animation are not implemented. Tracers and impact markers use development debug
drawing, not shipping VFX. Muzzle flash is an emissive mesh. There is no shot
audio yet. Health and death handling were added in Part 4; enemy AI and visual
damage reactions are not present yet.

**User check:** open the gameplay map and press Play. Hold left mouse, release
it, hold fire through an empty magazine to check automatic reload, and press R
with a partial magazine. Try firing while reloading and around cover;
also verify right-mouse aiming still feels correct. Check the ammo/reloading text
and the greybox rifle/flash. No enemies are expected yet.

- [Ready preview](Saved/Screenshots/WindowsEditor/SurvivalRifle_Part3_Ready.png)
- [Reload HUD preview](Saved/Screenshots/WindowsEditor/SurvivalRifle_Part3_ReloadHUD.png)
  (synthetic 17-round reload state for visual inspection; timing tested separately).
- [Rifle validation report](Saved/Automation/SurvivalRifle.json)

### 4. Health, regeneration, and death

- [x] Add a shared Blueprint health component; player and enemy defaults are 100 HP.
- [x] Player regenerates 10 HP/s after 5 seconds without taking damage.
- [x] Enemies do not regenerate by default.
- [x] Death disables owner tick/collision and character movement; dead enemies
      disappear immediately.
- [x] Player death stops combat, aiming, and reload; a death overlay offers
      **Press ENTER to Restart**.
- [x] Falling out of the arena sets HP to 0 and shows the same death screen.
      Native Kill Z pawn destruction also shows 0 HP and allows Enter to restart.
- [x] Add a basic HP counter; the complete combat HUD remains Part 7.
- [x] Expose maximum HP, regeneration enable/delay/rate, death cleanup timing,
      and fall Z.
- [x] Validate health limits, damage, regeneration delay, death, and restart.
- [x] Remove temporary fixtures; save/reload gameplay assets and verify fresh PIE.
- [x] User approval received on 2026-10-16, including fall-death handling.

Implementation:

- Shared component:
  [BP_SurvivalHealth](Content/Shooter/Blueprints/BP_SurvivalHealth.uasset).
- The player enables regeneration on its `HealthComponent`. The component
  defaults to no regeneration for future enemies.
- Owners forward Unreal's `AnyDamage` event to the component's
  `TakeHealthDamage`. Point damage from the rifle also reaches this event.
- Positive damage subtracts HP and resets the regeneration delay. HP stays
  between 0 and maximum; nonpositive damage does not heal or reset the delay.
- Dead owners ignore subsequent damage and cannot regenerate. Dead enemies
  disappear on the next frame; player input is disabled while the HUD still
  reads Enter to reload the current gameplay map.
- `EnemyCorpseLifetime` defaults to 0.01 seconds to remove defeated enemies
  without a visible corpse delay.
- `FallDeathZ` defaults to -900 cm, safely below the lower floor (-440 cm) and
  above the existing engine Kill Z (-1200 cm). Crossing it applies lethal damage
  through the normal health/death path. Native world-bound checks stay enabled.
- The HUD remembers whether it has seen the player. If native Kill Z removes
  the pawn before health can tick (for example, a teleport far below the map),
  it displays 0 HP and the death/restart overlay without requiring a valid pawn.
- Enemy AI is not implemented yet. Part 5 must attach the same component, forward
  damage, and check `bDead` before any controller/timer-driven AI work.

Validation results:

- Both player and non-player test receiver started at 100 HP.
- Fractional damage was preserved. Subsequent damage restarted the full delay.
- Player regeneration began after 5.005 seconds at exactly 10 HP/s, capped at 100.
- The non-player receiver remained at 80 HP throughout the regeneration test.
- Five actual 20-damage rifle hits defeated the 100-HP receiver.
- Dead non-player receiver stopped ticking/colliding and was removed on the
  next frame. Repeated damage did not extend its cleanup time.
- Real held W/LMB did not move or fire the dead player; no regeneration occurred
  after death. Death also cancelled an active automatic reload and hid the flash.
- Enter restarted the level, restoring 100 HP, 30 ammunition, movement, collision,
  input, and the test encounter's initial state.
- Temporary test actors were removed. Saved/reloaded gameplay map remains 925
  actors; fresh PIE starts alive at 100 HP/30 rounds with no fixtures.
- Actual gravity-driven fall from outside geometry at Z -800 triggered death at
  approximately Z -901, with HP 0, input/combat stopped, and Enter restart working.
- A teleport to Z -5000 exercised native Kill Z destruction: the pawn was gone,
  but 0 HP, the death overlay, and Enter restart still worked. Both restart paths
  restored 100 HP and 30 rounds. Existing Kill Z remains -1200.

**User check:** press Play and check the HP counter and existing movement,
aiming, and shooting. Falling out of the map should show 0 HP and the death
screen; Enter restarts from that screen. There are no enemies yet. Damage/death tests
used a temporary fixture; a live damage demonstration can be run for review.
Enemies disappear immediately rather than using ragdoll/death art.

- [Healthy-player preview](Saved/Screenshots/WindowsEditor/SurvivalHealth_Part4_Ready.png)
- [Death/restart preview](Saved/Screenshots/WindowsEditor/SurvivalHealth_Part4_Death.png)
- [Fall death preview](Saved/Screenshots/WindowsEditor/SurvivalHealth_Part4_FallDeath.png)
- [Native Kill Z fallback](Saved/Screenshots/WindowsEditor/SurvivalHealth_Part4_KillZFallback.png)
- [Health test report](Saved/Automation/SurvivalHealth.json)
- [Fall death report](Saved/Automation/SurvivalFallDeath.json)

### 5. Enemy perception and combat

- [x] Add greybox humanoid enemies with rifles and shared 100-HP health.
- [x] Implement patrol, detection, pursuit, firing-position selection, and search.
- [x] Detect using range, field of view, and unobstructed line of sight.
- [x] Navigate all floors and stairs.
- [x] Fire slow bursts with forgiving spread, 10 damage per hit, and an initial
      1-second reaction delay.
- [x] Stop shooting when walls block the shot, including a protruding muzzle.
- [x] Search the last known position instead of tracking through walls.
- [x] Validate perception, movement, firing, sight loss, and enemy death.
- [x] Save three fixed review enemies, one per floor; remove temporary fixtures.
- [x] Validate Enter restart restores the encounter after normal/native Kill Z death.
- [x] User approval received.

Runtime uses editable saved Blueprints:
[Enemy](Content/Shooter/Blueprints/BP_SurvivalEnemy.uasset) and
[AI controller](Content/Shooter/Blueprints/BP_SurvivalEnemyController.uasset).
The pawn handles perception/state logic; the native AI controller follows paths.
No runtime Python, C++, Behavior Tree, random spawning, or replacement system
was added in this milestone.

Current tuning:

| Setting | Value |
| --- | --- |
| Sight range / full vision cone | 20000 cm (200 m) / 120 degrees |
| Firing range / bullet trace reach | 20000 cm (200 m), matching player aim range |
| Reaction delay | 0.5 seconds, reapplied on reacquisition |
| Burst | 3 shots; configured 0.45-second interval, 2-second pause |
| Spread / damage | 5-degree cone half-angle / 10 per actual hit |
| Movement / decision tick | 220 cm/s / 0.1 second |
| Last-known-position search | 8 seconds, then return to home-area patrol |
| Patrol / local search / firing-position radius | 900 / 400 / 650 cm |
| Move-request interval / enemy removal | 2 seconds / immediate |

Original Part 5 validation results (before the later range/tuning changes):

- Players behind the enemy and beyond sight range were not detected.
- Initial reaction measured 1.001 seconds; reacquisition measured 1.097 seconds.
  At the 10-Hz decision tick, observed in-burst intervals were 0.496-0.504 seconds;
  pauses were 2.001-2.099 seconds. Each recorded damaging enemy hit dealt 10 HP.
- A solid wall blocked detection and damage. While hidden, the stored last
  observed location did not follow the player; search expired back to patrol.
- Low cover allowed eye-level vision but blocked the chest-to-muzzle guard,
  even with the barrel protruding beyond it. The enemy navigated approximately
  193 cm to a clear firing position before shooting.
- An out-of-range enemy pursued approximately 407 cm, then fired at a distance
  of 1393 cm, within the original 1400-cm firing range. The pursuit regression
  now explicitly uses a PIE-only 1400-cm fixture range to retain this check.
- Actual native AI path following climbed all four stair flights: both routes,
  lower-to-main and main-to-upper, approximately 5.77 seconds per flight.
  All requests disallowed partial paths. Failed navigation requests are logged,
  counted, and retried only after the movement interval.
- Enemies remained at 80 HP after test damage, with no regeneration.
  Five real player-rifle hits dealt 20 HP each, defeated a fresh 100-HP enemy,
  and left 25 rounds. Dead enemies disappear immediately.
- Enemy death stopped movement/tick/fire. Player death and native pawn destruction
  stopped enemy firing safely, without dereferencing a missing pawn.
- Survival character capsules now block Visibility so sight and both rifles can
  hit humanoids. The original third-person template defaults were not changed.
- Fixed a restart-input edge case exposed by combat: the HUD explicitly enables
  its own input on BeginPlay, independent of the disabled/destroyed player pawn.
  Actual Enter input restored 100 player HP, 30 rounds, and all three enemies
  after both normal death and native Kill Z destruction.
- The gameplay map has 928 saved actors: the prior 925 plus three fixed enemies.
  No temporary validation actors remain; the architectural original is untouched.
- Final fresh PIE after compilation/save confirmed all three 100-HP enemies,
  player 100 HP/30 rounds, collision, and independent HUD input. Real RMB aiming,
  LMB rifle fire, and normal camera/speed restoration still passed.

**User check:** open the gameplay map and press Play. There is one orange/brown
review enemy on each floor: main near `(1500, 2200)`, lower near `(2600, 1800)`,
and upper near `(4000, 4700)`. Approach from the front, hide behind walls, move
between floors, and try shooting them. Check the reaction delay, pursuit,
bursts, cover behavior, enemy death, and Enter restart.

These are fixed review placements, not random spawns: defeated enemies do not
return until restart. Random survival spawning remains Part 6. Weapons, flashes,
and humanoid material are greybox placeholders; advanced cover poses, two-handed
rifle aiming, ragdolls, and enemy shot audio are not part of this pass. Enemy
health bars and kill count remain Part 7.

- [Enemy combat preview](Saved/Screenshots/WindowsEditor/SurvivalEnemy_Part5_Ready.png)
- [Perception/combat report](Saved/Automation/SurvivalEnemy.json)
- [Native AI stair report](Saved/Automation/SurvivalEnemyStairs.json)
- [Cover/reposition/pursuit report](Saved/Automation/SurvivalEnemyPositions.json)
- [Player rifle versus enemy report](Saved/Automation/SurvivalEnemyRifle.json)
- [Restart report](Saved/Automation/SurvivalEnemyRestart.json)
- [Final saved-state/input checks](Saved/Automation/SurvivalEnemyFinal.json)

### 6. Random survival spawning

- [x] Spawn 3 enemies initially; grow the target population without a cap.
- [x] Replace defeated enemies after a delay.
- [x] Randomly choose validated reachable spawn locations across all floors.
- [x] Reject walls, voids, occupied ground, and locations too close to the player.
- [x] Prefer locations outside the player's view.
- [x] Validate spawn positions, replacement timing, and uncapped population growth.
- [x] User approval received.

The saved gameplay map now uses one `BP_SurvivalSpawner` instead of the three
fixed Part 5 review enemies. The spawner and enemy death-notification logic are
editable Blueprints; the native editor-Python files below are authoring and test
helpers only.

Current tuning:

| Setting | Value |
| --- | --- |
| Initial / starting target population | 3 enemies, one per floor |
| Saved-map population growth | +1 target per kill, with no maximum |
| Saved-map replacement delay / spawn cadence | 1 / 0.5 seconds |
| Candidate radius / minimum player distance | 1300 / 1200 cm |
| Preferred visibility | Outside view, using a 0.3 camera-forward dot threshold |
| Visible fallback | After 8 failed candidate attempts |

The initial wave deliberately guarantees one reachable enemy on each floor.
Replacement candidates use floor-matched navigation, collision-aware spawning,
and a player-distance check; they prefer off-screen points and fall back to a
visible valid point after repeated failures.

Validation results:

- The bounded PIE test passed. It found exactly three initial enemies, one on
  each floor, at least 1200 cm from the player.
- First replacements arrived 5.18 and 5.01 seconds after two defeats. The map
  actor's configured delay is 1 second; navigation candidate retries and the
  off-screen preference account for the additional time.
- The target reached 12 living enemies, exceeding the former six-enemy cap.
  Defeated enemies disappeared before the next validation tick, and their
  death callbacks still updated the spawner.
- After player death, no replacement appeared during the 5.51-second test
  window. This latest run stopped before checking Enter restart; a separate
  earlier run restored 100 HP, a target/living population of 3, and one enemy
  on each floor.
- The saved editor map contains one spawner and no fixed review or test enemies.

**User check:** open the gameplay map and press Play. Check that the initial
wave covers all three floors, then defeat enemies and observe immediate
disappearance followed by delayed, off-screen-preferring replacements as the
target population grows without a cap. Verify no replacements occur after
player death and press Enter to restart.

- [Spawner validation report](Saved/Automation/SurvivalSpawner.json)

### 7. Complete combat HUD

- [x] Integrate the crosshair, HP, ammunition, kill count, and death overlay.
- [x] Show player HP and a regeneration indicator while HP is increasing.
- [x] Render player HP as a bar; keep ammunition numeric.
- [x] Show magazine ammunition and reload status.
- [x] Show kill count and visible, line-of-sight enemy health bars.
- [x] Anchor enemy health bars just above the head.
- [x] Complete the death screen with Enter restart.
- [x] Validate HUD values, regeneration, enemy kills, and restart state.
- [x] User approval received on 2026-10-16, including HP bars and wall occlusion.

The runtime game mode uses the native `ASurvivalCombatHUD` because Unreal's
Python authoring API can wire the existing Blueprint HUD but cannot safely add
the additional graph nodes these displays require. It preserves the current
canvas-style crosshair and status layout. Enemy-bar candidates are refreshed at
10 Hz; camera-to-head/body visibility is rechecked before each bar is drawn so
walls hide bars immediately.

HUD review changes:

- Player HP uses a proportional colored bar; magazine ammunition stays numeric.
- Enemy bars use the head bone rather than whole-actor bounds, with a small
  clearance above the head and the bar drawn upward to avoid overlap.
- Fixed through-wall bars: the previous visibility query started at the enemy
  instead of the camera. Bars now require an unobstructed camera trace to the
  enemy's head or body; a bar above cover alone does not count as visible.
- Native regression `MCP.Survival.HUD.EnemyBarOcclusion` reproduced the wall bug
  before the fix and passed afterward: unobstructed enemy, full wall, head
  above low cover, restored full cover, and removed obstruction.
- Rebuilt the Editor module successfully and visually checked a half-full
  player bar and nearby enemy bars in PIE. Test placements were PIE-only.
- [Updated health-bar preview](Saved/Screenshots/WindowsEditor/SurvivalHUD_BarsReview.png)
- [PIE visual check](Content/Python/test_survival_hud_bars.py)

Validation results:

- PIE started with `SurvivalCombatHUD`, 100 HP, 30 rounds, and three enemies.
- Defeating an enemy incremented the kill count. Player regeneration began after
  approximately 5 seconds and displayed `REGENERATING`.
- Death showed the restart overlay. Enter restored 100 HP, three initial
  enemies, zero kills, and the combat HUD. The bounded PIE report passed.

**User check:** press Play in the gameplay map. Review the HP/regeneration,
ammunition/reload, kill count, visible-enemy health bars, and death/restart
display. Enemy bars should sit just above enemy heads and disappear behind
walls. Part 7 is approved.

- [HUD regeneration state](Saved/Screenshots/WindowsEditor/SurvivalHUD_Regen.png)
- [HUD reload state](Saved/Screenshots/WindowsEditor/SurvivalHUD_Reload.png)
- [HUD death screen](Saved/Screenshots/WindowsEditor/SurvivalHUD_Death.png)
- [HUD after restart](Saved/Screenshots/WindowsEditor/SurvivalHUD_Restart.png)
- [HUD validation report](Saved/Automation/SurvivalHUD.json)

### 8. End-to-end playtest and finalization

- [x] Test movement, collision, stairs, and navigation on every floor.
- [x] Test camera aiming and muzzle obstruction around cover.
- [x] Test shooting, reload timing, ammunition, and damage.
- [x] Test enemy detection, pursuit, firing, and search.
- [x] Test health, regeneration, enemy death, and player death.
- [x] Test random spawning and uncapped population growth.
- [x] Verify Restart resets the encounter cleanly.
- [x] Save and reload gameplay assets and check persistence.
- [x] Obtain final user playtest approval on 2026-10-16.

Final integrated validation passed in disposable PIE worlds:

- Ten saved-map navigation paths and all four stair flights passed for both
  player movement and native enemy navigation.
- Real right-mouse input changed the camera from 90 to 65 degrees and back.
  Five real rifle hits dealt 20 damage each and removed the defeated enemy.
- Manual reload took 2.03 seconds; holding fire through an empty magazine
  reloaded in 2.00 seconds and resumed shooting. The 30-round magazine fired
  exactly 30 shots at a mean interval of 0.166 seconds.
- Three shots with cover between the hand and muzzle caused no enemy damage;
  removing cover restored a 20-damage hit.
- Enemy perception, reaction, bursts, pursuit, cover/repositioning, search,
  death, and native Kill Z safety checks passed.
- Spawning covered all three floors, respected the 1200 cm minimum distance,
  grew beyond the former six-enemy cap to 12, and stopped after player death.
- Health regeneration began after 5 seconds. Actual Enter input restored
  100 HP, 30 rounds, three enemies, zero kills, and the HUD after both the
  population-ramp test and the HUD death test.
- Reloading the saved gameplay map retained 926 actors, valid navigation,
  and no temporary test fixtures. No map or content packages were dirty.
  The successful run logged no Blueprint runtime errors or other error lines.

The initial input-test failures were viewport mouse-capture issues, not
gameplay failures. The runner now acquires capture with right mouse before
measuring gameplay input. The HUD helper now fails rather than reporting
success if Enter restart is not verified before its timeout.

The runner requires the Windows desktop, Unreal foreground focus, and the
current default docked viewport layout. It moves the pointer into the viewport
and sends real mouse/keyboard input; do not use the desktop during the run.
It temporarily disables editor background CPU throttling and restores the
previous setting on completion or handled failure. It never saves PIE fixtures.
Editor-only validation does not cover packaged builds or sustained-load
performance testing.

**Final user check (approved):** play the saved gameplay map. Walk all floors and stairs;
aim and shoot near cover; check manual and empty-magazine reloads; fight enemies
and review both HP bars; then die and press Enter to confirm a clean restart.
Part 8 was explicitly approved and marked complete on 2026-10-16.

- [Integrated validation runner](Content/Python/run_survival_final_validation.py)
- [Latest integrated report](Saved/Automation/SurvivalFinal.json)
- [Player muzzle-cover regression](Content/Python/test_survival_player_cover.py)
- [Player muzzle-cover report](Saved/Automation/SurvivalPlayerCover.json)

### Post-approval change: equal enemy and player shooting range

Requested on 2026-10-16. Enemy sight and firing range now match the player's
20000-cm (200-m) aim trace. Before this change the saved enemy defaults were
7000 cm, but the actual enemy bullet trace was still hard-coded to 3000 cm.
The bullet trace now reads `FireRange`, so it cannot silently retain the old
shorter reach when the attack range is adjusted.

The existing 120-degree vision cone, 0.5-second saved reaction delay,
5-degree spread, 10-damage hits, burst timing, and wall/muzzle blocking are
unchanged. Greater reach does not guarantee a hit: the existing spread makes
very distant shots less accurate.

The range regression confirmed rejection beyond 200 m, an actual 10-damage
hit at 199 m, and no detection or further shots through a full blocking wall.
Only the disposable range fixture disables spread and suspends the characters
above the arena to make this boundary test deterministic; saved gameplay
settings and map actors are not changed by the test.

The follow-up integrated run passed the range test, player/enemy stairs,
enemy combat and pursuit, real player aiming/rifle/manual and automatic reload,
and player muzzle-cover checks. It then stopped at the spawner test's old
three-enemy assertion: the saved map spawner now has `InitialPopulation=10`,
while the helper assumes 3. Spawn tuning was left untouched. The follow-up
HUD/restart and final reload stages were therefore not reached in that run;
the earlier Part 8 approval remains the record of the original full validation.
No Blueprint runtime errors were logged. The changed enemy Blueprint compiled,
was saved, and has no remaining dirty map or content packages.

- [Apply saved range and graph change](Content/Python/configure_survival_enemy_range.py)
- [Long-range regression](Content/Python/test_survival_enemy_range.py)
- [Long-range test report](Saved/Automation/SurvivalEnemyRange.json)

## Validation scripts and reports

These are editor setup/validation helpers, not runtime Python dependencies:

- [Arena builder](Content/Python/build_survival_arena.py)
- [Arena validation](Content/Python/validate_survival_arena.py)
- [Stair movement test](Content/Python/test_survival_stairs.py)
- [Aiming graph wiring](Content/Python/wire_survival_aiming.py)
  (Part 2 setup only; do not rerun over the Part 3 graph).
- [Rifle component setup](Content/Python/setup_survival_rifle.py)
- [Rifle graph wiring](Content/Python/wire_survival_rifle.py)
- [Bounded rifle observation](Content/Python/test_survival_rifle.py)
- [Bounded auto-reload observation](Content/Python/test_survival_auto_reload.py)
- [Rifle report assertions](Content/Python/validate_survival_rifle_report.py)
- [Health component setup](Content/Python/setup_survival_health.py)
- [Health graph wiring](Content/Python/wire_survival_health.py)
- [Bounded health tests](Content/Python/test_survival_health.py)
- [Enemy component setup](Content/Python/setup_survival_enemy.py)
- [Enemy graph wiring](Content/Python/wire_survival_enemy.py)
- [Fixed enemy placement](Content/Python/place_survival_review_enemies.py)
- [Bounded enemy perception/combat tests](Content/Python/test_survival_enemy.py)
- [Native enemy stair tests](Content/Python/test_survival_enemy_stairs.py)
- [Cover and pursuit tests](Content/Python/test_survival_enemy_positions.py)
- [Player rifle versus enemy test](Content/Python/test_survival_enemy_rifle.py)
- [Random spawner PIE test](Content/Python/test_survival_spawner.py)
- [Spawner PIE test runner](Content/Python/run_survival_spawner_validation.py)
- [HUD game-mode setup](Content/Python/configure_survival_hud.py)
- [HUD PIE validation](Content/Python/test_survival_hud.py)
- [HUD PIE test runner](Content/Python/run_survival_hud_validation.py)

Graph-wiring scripts require the existing native nodes they reference; they are
not standalone project generators. The rifle observer requires one temporary
test target before PIE. Its target Blueprint is under
`/Game/Shooter/Tests/BP_RifleTestTarget`; no test actors remain in the saved map.
The health test requires this fixture labelled `TEMP_HealthValidationTarget`;
it intentionally leaves the PIE player dead for screenshot and restart checks.
The rifle observer temporarily gives its PIE receiver extra HP for sustained-fire
measurements; the receiver's saved/default health remains 100.
Enemy tests require exactly one unsaved enemy labelled `TEMP_EnemyValidation`,
not the three saved review actors. The cover test additionally requires an
unsaved cube labelled `TEMP_EnemyMuzzleBlock`, centered at `(2070, 2200, 117.5)`,
scaled `(0.1, 2, 0.35)`, initially with collision disabled. Use an unsaved test
configuration and reload the saved map afterward. Do not save test-only changes.
The setup/placement helpers are one-time authoring tools, not safe reset buttons.

Recorded test results:

- [Arena navigation report](Saved/Automation/SurvivalArenaValidation.json)
- [Stair movement report](Saved/Automation/SurvivalStairs.json)
- [Aiming report](Saved/Automation/SurvivalAiming.json)
- [Rifle report](Saved/Automation/SurvivalRifle.json)
- [Raw rifle observations](Saved/Automation/SurvivalRifleRaw.json)
  (initial manual-reload behavior, before the auto-reload follow-up).
- [Auto-reload follow-up report](Saved/Automation/SurvivalAutoReload.json)
- [Raw auto-reload observations](Saved/Automation/SurvivalAutoReloadRaw.json)
- [Health, death, and restart report](Saved/Automation/SurvivalHealth.json)
- [Fall death and native Kill Z report](Saved/Automation/SurvivalFallDeath.json)
- [Random survival spawner report](Saved/Automation/SurvivalSpawner.json)
- [HUD validation report](Saved/Automation/SurvivalHUD.json)
- [HUD after restart](Saved/Screenshots/WindowsEditor/SurvivalHUD_Restart.png)
- [HUD reload state](Saved/Screenshots/WindowsEditor/SurvivalHUD_Reload.png)
- [HUD regeneration state](Saved/Screenshots/WindowsEditor/SurvivalHUD_Regen.png)
- [HUD death screen](Saved/Screenshots/WindowsEditor/SurvivalHUD_Death.png)

Reports and preview images are under `Saved` and may be removed by Unreal
cleanup. This TODO file is the persistent progress summary.
