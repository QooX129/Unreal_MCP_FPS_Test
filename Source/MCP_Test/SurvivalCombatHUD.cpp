// Copyright Epic Games, Inc. All Rights Reserved.

#include "SurvivalCombatHUD.h"

#include "Components/CapsuleComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/Canvas.h"
#include "Engine/Engine.h"
#include "EngineUtils.h"
#include "Engine/World.h"
#include "GameFramework/Character.h"
#include "GameFramework/PlayerController.h"
#include "InputCoreTypes.h"
#include "Kismet/GameplayStatics.h"
#include "UObject/UnrealType.h"

#if WITH_DEV_AUTOMATION_TESTS
#include "Components/BoxComponent.h"
#include "Misc/AutomationTest.h"
#endif

namespace
{
	UActorComponent* FindNamedComponent(AActor* Actor, const FName Name)
	{
		if (!Actor)
		{
			return nullptr;
		}

		TArray<UActorComponent*> Components;
		Actor->GetComponents(Components);
		for (UActorComponent* Component : Components)
		{
			if (Component && Component->GetFName() == Name)
			{
				return Component;
			}
		}

		return nullptr;
	}

	double ReadNumber(const UObject* Object, const FName PropertyName, const double Fallback = 0.0)
	{
		if (!Object)
		{
			return Fallback;
		}

		const FNumericProperty* Property = CastField<FNumericProperty>(
			Object->GetClass()->FindPropertyByName(PropertyName));
		if (!Property)
		{
			return Fallback;
		}

		const void* Value = Property->ContainerPtrToValuePtr<void>(Object);
		return Property->IsFloatingPoint()
			? Property->GetFloatingPointPropertyValue(Value)
			: static_cast<double>(Property->GetSignedIntPropertyValue(Value));
	}

	bool ReadBoolean(const UObject* Object, const FName PropertyName)
	{
		const FBoolProperty* Property = Object
			? CastField<FBoolProperty>(Object->GetClass()->FindPropertyByName(PropertyName))
			: nullptr;
		return Property && Property->GetPropertyValue_InContainer(Object);
	}

	FLinearColor HealthColor(const double HealthFraction)
	{
		return FMath::Lerp(
			FLinearColor(0.9f, 0.12f, 0.08f, 1.0f),
			FLinearColor(0.2f, 0.85f, 0.28f, 1.0f),
			static_cast<float>(FMath::Clamp(HealthFraction, 0.0, 1.0)));
	}

	FVector EnemyBarWorldPosition(const ACharacter* Enemy)
	{
		const USkeletalMeshComponent* Mesh = Enemy->GetMesh();
		const FName HeadBone(TEXT("head"));
		if (Mesh && Mesh->DoesSocketExist(HeadBone))
		{
			return Mesh->GetSocketLocation(HeadBone) + FVector(0.0, 0.0, 22.0);
		}

		return Enemy->GetActorLocation()
			+ FVector(0.0, 0.0, Enemy->GetCapsuleComponent()->GetScaledCapsuleHalfHeight() + 5.0);
	}

	bool IsEnemyVisible(const APlayerController* Controller, const ACharacter* Enemy)
	{
		FVector ViewLocation;
		FRotator ViewRotation;
		Controller->GetPlayerViewPoint(ViewLocation, ViewRotation);
		FCollisionQueryParams Params(SCENE_QUERY_STAT(SurvivalHUDVisibility), true);
		Params.AddIgnoredActor(Controller->GetPawn());
		Params.AddIgnoredActor(Enemy);
		const USkeletalMeshComponent* Mesh = Enemy->GetMesh();
		const FVector HeadLocation = Mesh && Mesh->DoesSocketExist(TEXT("head"))
			? Mesh->GetSocketLocation(TEXT("head"))
			: Enemy->GetActorLocation()
				+ FVector(0.0, 0.0, Enemy->GetCapsuleComponent()->GetScaledCapsuleHalfHeight() * 0.8);
		return !Enemy->GetWorld()->LineTraceTestByChannel(
				ViewLocation, HeadLocation, ECC_Visibility, Params)
			|| !Enemy->GetWorld()->LineTraceTestByChannel(
				ViewLocation, Enemy->GetActorLocation(), ECC_Visibility, Params);
	}
}

void ASurvivalCombatHUD::BeginPlay()
{
	Super::BeginPlay();

	if (PlayerOwner)
	{
		EnableInput(PlayerOwner);
		if (InputComponent)
		{
			InputComponent->BindKey(
				EKeys::Enter, IE_Pressed, this, &ASurvivalCombatHUD::RestartCurrentLevel);
		}
	}
}

void ASurvivalCombatHUD::RestartCurrentLevel()
{
	ACharacter* PlayerCharacter = UGameplayStatics::GetPlayerCharacter(this, 0);
	UActorComponent* HealthComponent = FindNamedComponent(PlayerCharacter, TEXT("HealthComponent"));
	const double Health = ReadNumber(HealthComponent, TEXT("Health"), 1.0);
	const bool bPlayerDead = PlayerCharacter
		? ReadBoolean(HealthComponent, TEXT("bDead")) || Health <= 0.0
		: bHasSeenPlayer;
	if (bPlayerDead)
	{
		const FString LevelName = UGameplayStatics::GetCurrentLevelName(this, true);
		if (LevelName.IsEmpty())
		{
			UE_LOG(LogTemp, Error, TEXT("Cannot restart survival level: current level name is empty."));
			return;
		}
		UGameplayStatics::OpenLevel(this, FName(*LevelName), true);
	}
}

void ASurvivalCombatHUD::DrawHUD()
{
	Super::DrawHUD();
	if (!Canvas || !PlayerOwner)
	{
		return;
	}

	const float ScreenWidth = Canvas->ClipX;
	const float ScreenHeight = Canvas->ClipY;
	const FVector2D Center(ScreenWidth * 0.5f, ScreenHeight * 0.5f);
	const FLinearColor White(1.0f, 1.0f, 1.0f, 0.95f);

	DrawRect(White, Center.X - 6.0f, Center.Y - 1.0f, 12.0f, 2.0f);
	DrawRect(White, Center.X - 1.0f, Center.Y - 6.0f, 2.0f, 12.0f);

	ACharacter* PlayerCharacter = UGameplayStatics::GetPlayerCharacter(this, 0);
	if (PlayerCharacter)
	{
		bHasSeenPlayer = true;
	}

	UActorComponent* PlayerHealth = FindNamedComponent(PlayerCharacter, TEXT("HealthComponent"));
	const double Health = ReadNumber(PlayerHealth, TEXT("Health"));
	const double MaxHealth = FMath::Max(1.0, ReadNumber(PlayerHealth, TEXT("MaxHealth"), 100.0));
	const bool bPlayerDead = !PlayerCharacter
			? bHasSeenPlayer
			: ReadBoolean(PlayerHealth, TEXT("bDead")) || Health <= 0.0;

	if (!bPlayerDead)
	{
		const double HealthFraction = Health / MaxHealth;
		const float PlayerBarX = 70.0f;
		const float PlayerBarY = 84.0f;
		const float PlayerBarWidth = 180.0f;
		const float PlayerBarHeight = 12.0f;
		DrawText(TEXT("HP"), FLinearColor(0.8f, 1.0f, 0.8f, 1.0f),
			35.0f, 80.0f, nullptr, 1.2f);
		DrawRect(FLinearColor(0.02f, 0.02f, 0.025f, 0.88f),
			PlayerBarX, PlayerBarY, PlayerBarWidth, PlayerBarHeight);
		DrawRect(HealthColor(HealthFraction),
			PlayerBarX + 1.0f, PlayerBarY + 1.0f,
			(PlayerBarWidth - 2.0f)
				* static_cast<float>(FMath::Clamp(HealthFraction, 0.0, 1.0)),
			PlayerBarHeight - 2.0f);

		if (bHasPreviousHealth && Health > PreviousHealth + KINDA_SMALL_NUMBER)
		{
			DrawText(
				TEXT("REGENERATING"), FLinearColor(0.35f, 1.0f, 0.5f, 1.0f),
				35.0f, 108.0f, nullptr, 1.0f);
		}
		PreviousHealth = static_cast<float>(Health);
		bHasPreviousHealth = true;

		const double Ammo = ReadNumber(PlayerCharacter, TEXT("Ammo"), -1.0);
		const bool bReloading = ReadBoolean(PlayerCharacter, TEXT("bReloading"));
		if (Ammo >= 0.0)
		{
			const FString AmmoText = bReloading
				? FString::Printf(TEXT("RELOADING...   R: Reload"))
				: FString::Printf(TEXT("AMMO  %d / 30   |   LMB: Fire   RMB: Aim   R: Reload"),
					FMath::RoundToInt(Ammo));
			DrawText(AmmoText, White, 35.0f, 45.0f, nullptr, 1.5f);
		}
	}

	int32 TotalKills = 0;
	if (!CachedSpawner.IsValid() && GetWorld())
	{
		for (TActorIterator<AActor> It(GetWorld()); It; ++It)
		{
			if (It->GetClass()->GetName().Contains(TEXT("BP_SurvivalSpawner")))
			{
				CachedSpawner = *It;
				break;
			}
		}
	}
	TotalKills = FMath::Max(0, FMath::RoundToInt(
		ReadNumber(CachedSpawner.Get(), TEXT("TotalKills"))));
	DrawText(
		FString::Printf(TEXT("KILLS  %d"), TotalKills),
		FLinearColor(1.0f, 0.86f, 0.55f, 1.0f),
		ScreenWidth - 210.0f, 45.0f, nullptr, 1.5f);

	if (GetWorld() && GetWorld()->GetTimeSeconds() >= NextEnemyBarRefreshTime)
	{
		NextEnemyBarRefreshTime = GetWorld()->GetTimeSeconds() + 0.1f;
		VisibleEnemies.Reset();
		for (TActorIterator<ACharacter> It(GetWorld()); It; ++It)
		{
			ACharacter* Enemy = *It;
			if (!Enemy || Enemy == PlayerCharacter
				|| !Enemy->GetClass()->GetName().Contains(TEXT("BP_SurvivalEnemy")))
			{
				continue;
			}

			UActorComponent* EnemyHealth = FindNamedComponent(Enemy, TEXT("HealthComponent"));
			const double EnemyMaxHealth = ReadNumber(EnemyHealth, TEXT("MaxHealth"));
			const double EnemyHP = ReadNumber(EnemyHealth, TEXT("Health"));
			if (ReadBoolean(EnemyHealth, TEXT("bDead"))
				|| EnemyHP <= 0.0 || EnemyMaxHealth <= 0.0)
			{
				continue;
			}

			const FVector BarWorldPosition = EnemyBarWorldPosition(Enemy);
			FVector2D BarScreenPosition;
			if (PlayerOwner->ProjectWorldLocationToScreen(BarWorldPosition, BarScreenPosition)
				&& BarScreenPosition.X >= 0.0 && BarScreenPosition.X <= ScreenWidth
				&& BarScreenPosition.Y >= 0.0 && BarScreenPosition.Y <= ScreenHeight
				&& IsEnemyVisible(PlayerOwner, Enemy))
			{
				VisibleEnemies.Add(Enemy);
			}
		}
	}

	for (const TWeakObjectPtr<AActor>& EnemyPointer : VisibleEnemies)
	{
		AActor* Enemy = EnemyPointer.Get();
		UActorComponent* EnemyHealth = FindNamedComponent(Enemy, TEXT("HealthComponent"));
		const double EnemyMaxHealth = ReadNumber(EnemyHealth, TEXT("MaxHealth"));
		const double EnemyHP = ReadNumber(EnemyHealth, TEXT("Health"));
		ACharacter* EnemyCharacter = Cast<ACharacter>(Enemy);
		if (!EnemyCharacter || ReadBoolean(EnemyHealth, TEXT("bDead"))
			|| EnemyHP <= 0.0 || EnemyMaxHealth <= 0.0
			|| !IsEnemyVisible(PlayerOwner, EnemyCharacter))
		{
			continue;
		}

		FVector2D BarScreenPosition;
		if (!PlayerOwner->ProjectWorldLocationToScreen(
				EnemyBarWorldPosition(EnemyCharacter), BarScreenPosition)
			|| BarScreenPosition.X < 0.0 || BarScreenPosition.X > ScreenWidth
			|| BarScreenPosition.Y < 0.0 || BarScreenPosition.Y > ScreenHeight)
		{
			continue;
		}

		const float BarWidth = 62.0f;
		const float BarHeight = 6.0f;
		const float BarX = BarScreenPosition.X - BarWidth * 0.5f;
		const float BarY = BarScreenPosition.Y - BarHeight - 3.0f;
		const double HealthFraction = EnemyHP / EnemyMaxHealth;
		DrawRect(FLinearColor(0.02f, 0.02f, 0.025f, 0.88f),
			BarX, BarY, BarWidth, BarHeight);
		DrawRect(HealthColor(HealthFraction),
			BarX + 1.0f, BarY + 1.0f,
			(BarWidth - 2.0f) * static_cast<float>(FMath::Clamp(HealthFraction, 0.0, 1.0)),
			BarHeight - 2.0f);
	}

	if (bPlayerDead)
	{
		DrawRect(FLinearColor(0.015f, 0.005f, 0.005f, 0.85f),
			0.0f, 0.0f, ScreenWidth, ScreenHeight);
		DrawText(
			TEXT("YOU DIED"), FLinearColor(1.0f, 0.9f, 0.85f, 1.0f),
			ScreenWidth * 0.5f - 150.0f, ScreenHeight * 0.5f - 60.0f,
			nullptr, 3.5f);
		DrawText(
			TEXT("Press ENTER to Restart"), FLinearColor(1.0f, 0.9f, 0.85f, 1.0f),
			ScreenWidth * 0.5f - 180.0f, ScreenHeight * 0.5f + 20.0f,
			nullptr, 1.8f);
	}
}

#if WITH_DEV_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSurvivalHUDOcclusionTest,
	"MCP.Survival.HUD.EnemyBarOcclusion",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FSurvivalHUDOcclusionTest::RunTest(const FString& Parameters)
{
	UWorld* World = UWorld::CreateWorld(EWorldType::Game, false);
	APlayerController* Controller = World->SpawnActor<APlayerController>();
	Controller->SetInitialLocationAndRotation(FVector(0.0, 0.0, 100.0), FRotator::ZeroRotator);
	ACharacter* Enemy = World->SpawnActor<ACharacter>(FVector(600.0, 0.0, 100.0),
		FRotator::ZeroRotator);
	TestTrue(TEXT("Unobstructed enemy shows its bar"), IsEnemyVisible(Controller, Enemy));

	AActor* Wall = World->SpawnActor<AActor>();
	UBoxComponent* Box = NewObject<UBoxComponent>(Wall);
	Wall->SetRootComponent(Box);
	Box->SetBoxExtent(FVector(25.0, 200.0, 300.0));
	Box->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
	Box->SetCollisionResponseToAllChannels(ECR_Block);
	Box->RegisterComponent();
	Wall->SetActorLocation(FVector(300.0, 0.0, 100.0));
	TestFalse(TEXT("Enemy behind a wall must not show its bar"),
		IsEnemyVisible(Controller, Enemy));

	Box->SetBoxExtent(FVector(25.0, 200.0, 20.0));
	TestTrue(TEXT("Head visible above low cover shows the bar"), IsEnemyVisible(Controller, Enemy));
	Box->SetBoxExtent(FVector(25.0, 200.0, 300.0));
	TestFalse(TEXT("Restoring full cover hides an already-visible enemy bar"),
		IsEnemyVisible(Controller, Enemy));

	Box->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	TestTrue(TEXT("Removing obstruction restores the bar"), IsEnemyVisible(Controller, Enemy));
	World->DestroyWorld(false);
	return true;
}
#endif
