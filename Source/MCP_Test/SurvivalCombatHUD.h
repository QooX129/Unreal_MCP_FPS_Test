// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/HUD.h"
#include "SurvivalCombatHUD.generated.h"

UCLASS()
class MCP_TEST_API ASurvivalCombatHUD : public AHUD
{
	GENERATED_BODY()

public:
	virtual void BeginPlay() override;
	virtual void DrawHUD() override;

private:
	void RestartCurrentLevel();

	bool bHasSeenPlayer = false;
	bool bHasPreviousHealth = false;
	float PreviousHealth = 0.0f;
	float NextEnemyBarRefreshTime = 0.0f;
	TWeakObjectPtr<AActor> CachedSpawner;
	TArray<TWeakObjectPtr<AActor>> VisibleEnemies;
};
