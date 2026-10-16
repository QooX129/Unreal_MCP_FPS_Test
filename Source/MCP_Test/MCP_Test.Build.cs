// Copyright Epic Games, Inc. All Rights Reserved.

using UnrealBuildTool;

public class MCP_Test : ModuleRules
{
	public MCP_Test(ReadOnlyTargetRules Target) : base(Target)
	{
		PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;

		PublicDependencyModuleNames.AddRange(new string[] {
			"Core",
			"CoreUObject",
			"Engine",
			"InputCore",
			"EnhancedInput",
			"AIModule",
			"StateTreeModule",
			"GameplayStateTreeModule",
			"UMG",
			"Slate"
		});

		PrivateDependencyModuleNames.AddRange(new string[] { });

		PublicIncludePaths.AddRange(new string[] {
			"MCP_Test",
			"MCP_Test/Variant_Platforming",
			"MCP_Test/Variant_Platforming/Animation",
			"MCP_Test/Variant_Combat",
			"MCP_Test/Variant_Combat/AI",
			"MCP_Test/Variant_Combat/Animation",
			"MCP_Test/Variant_Combat/Gameplay",
			"MCP_Test/Variant_Combat/Interfaces",
			"MCP_Test/Variant_Combat/UI",
			"MCP_Test/Variant_SideScrolling",
			"MCP_Test/Variant_SideScrolling/AI",
			"MCP_Test/Variant_SideScrolling/Gameplay",
			"MCP_Test/Variant_SideScrolling/Interfaces",
			"MCP_Test/Variant_SideScrolling/UI"
		});

		// Uncomment if you are using Slate UI
		// PrivateDependencyModuleNames.AddRange(new string[] { "Slate", "SlateCore" });

		// Uncomment if you are using online features
		// PrivateDependencyModuleNames.Add("OnlineSubsystem");

		// To include OnlineSubsystemSteam, add it to the plugins section in your uproject file with the Enabled attribute set to true
	}
}
