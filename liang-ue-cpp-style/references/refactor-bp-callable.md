# Refactoring BlueprintCallable APIs in a Mature Codebase

Companion to `SKILL.md` §19. Two hard-won defaults that apply any time you change a `UFUNCTION(BlueprintCallable)` signature, demote it, or replace it with something new in a project that has shipped Blueprints.

Consult before planning any phase that touches BP-facing C++ signatures. The 2026-04-14 incident summary at the bottom is the cost of skipping this.

---

## 19.1 Prefer `FGameplayTagContainer` over `UENUM(meta=(Bitflags))` for BP-facing scope/filter parameters

When a function needs a multi-value scope/filter parameter exposed to Blueprint, **default to `FGameplayTagContainer`**. The UE5 BP bitmask UI is poor: when more than one bit is selected the dropdown collapses to `"(Multiple)"`, and designers can't see at a glance which scopes are active. Tag containers give a clean "Add Tag" / searchable UI, are hierarchical, and match the pattern designers already know from GAS.

### DO

```cpp
// In SystemNameGameplayTags.h — declare native tags namespaced consistently
namespace S1GameplayTags
{
    S1_API UE_DECLARE_GAMEPLAY_TAG_EXTERN(Save_Scope_Player);
    S1_API UE_DECLARE_GAMEPLAY_TAG_EXTERN(Save_Scope_Level);
    S1_API UE_DECLARE_GAMEPLAY_TAG_EXTERN(Save_Scope_Setting);
    S1_API UE_DECLARE_GAMEPLAY_TAG_EXTERN(Save_Scope_Progression);
}

// In SystemNameGameplayTags.cpp — define them
UE_DEFINE_GAMEPLAY_TAG_COMMENT(Save_Scope_Player, "Save.Scope.Player", "Player attributes, equipment, skills, etc.");
// ... etc

// In SubsystemHeader.h — accept FGameplayTagContainer
UFUNCTION(BlueprintCallable, Category = "Save Game", meta = (HidePin = "playerCharacter"))
void WriteSaveGame(const FGameplayTagContainer& scopeTags, APlayerCharacter* playerCharacter = nullptr, FName newPlayerStartTag = NAME_None);

// In SubsystemImpl.cpp — dispatch via HasTag
const bool bWantsPlayer = scopeTags.HasTag(S1GameplayTags::Save_Scope_Player);
const bool bWantsLevel  = scopeTags.HasTag(S1GameplayTags::Save_Scope_Level);
// ...
if (scopeTags.IsEmpty())
{
    UE_LOG(LogSave, Warning, TEXT("WriteSaveGame called with empty scope, no-op"));
    return;
}
```

### DO NOT

```cpp
// BAD — BP UI collapses to "(Multiple)" and is unreadable
UENUM(BlueprintType, meta = (Bitflags, UseEnumValuesAsMaskValuesInEditor = "true"))
enum class ESaveScope : uint8
{
    None        = 0  UMETA(Hidden),
    Player      = 1 << 0,
    Level       = 1 << 1,
    // ...
};
ENUM_CLASS_FLAGS(ESaveScope);

UFUNCTION(BlueprintCallable, meta = (Bitmask, BitmaskEnum = "/Script/MyModule.ESaveScope"))
void WriteSaveGame(UPARAM(meta = (Bitmask, BitmaskEnum = "/Script/MyModule.ESaveScope")) int32 scopeFlags, ...);
```

### When `UENUM(Bitflags)` IS acceptable

- The function is C++-only (no `UFUNCTION(BlueprintCallable)` wrapper)
- Performance is genuinely measurable at a high call rate (saves, settings menus, etc. are NOT — `HasTag` is a hash lookup and disappears in profiles)
- The project has no GAS / native tag infrastructure (rare in modern UE5 projects)

Naming convention: `<System>.Scope.<Concept>` or `<System>.Filter.<Concept>` — keep the second segment generic so sibling APIs in the same system can reuse the tag set.

### MANDATORY: `meta=(AutoCreateRefTerm="<param>")` on `const T&` BP params

Any `UFUNCTION(BlueprintCallable)` that takes a struct (FGameplayTagContainer, FGameplayTag, FVector, FTransform, FString, etc.) by `const T&` MUST set `meta=(AutoCreateRefTerm="<paramName>")`. Without it, BP forces designers to wire a `Make Literal <Type>` node into the pin or they get this compile error:

```
The current value of the '<Pin>' pin is invalid: '<Pin>' in action '<Func>' must
have an input wired into it ("by ref" params expect a valid input to operate on).
```

DO:
```cpp
UFUNCTION(BlueprintCallable, Category = "Save Game",
          meta = (HidePin = "playerCharacter", AutoCreateRefTerm = "scopeTags"))
void WriteSaveGame(const FGameplayTagContainer& scopeTags,
                   APlayerCharacter* playerCharacter = nullptr,
                   FName newPlayerStartTag = NAME_None);
```

DO NOT:
```cpp
// BAD — BP designer hits "must have an input wired into it" compile error
UFUNCTION(BlueprintCallable, meta = (HidePin = "playerCharacter"))
void WriteSaveGame(const FGameplayTagContainer& scopeTags, ...);
```

For multiple by-ref params, comma-separate them: `meta=(AutoCreateRefTerm="scopeTags,filterTags,sourceTransform")`.

The C++ overhead is zero — `AutoCreateRefTerm` only affects the BP node generation, not the C++ signature.

---

## 19.2 Use `UE_DEPRECATED` + `meta=(DeprecatedFunction)` soft deprecation when refactoring BP-callable functions

When refactoring or replacing an existing `UFUNCTION(BlueprintCallable)`, **soft-deprecate the old function instead of hard-removing it**. The soft-deprecated function still works, existing BP graphs still compile, and the BP compiler emits a yellow warning that nudges migration over time.

### DO

```cpp
// In header:
UE_DEPRECATED(5.5, "Use WriteSaveGame with a Save.Scope.Player tag instead.")
UFUNCTION(BlueprintCallable, Category = "Save Game",
          meta = (HidePin = "playerCharacter",
                  DeprecatedFunction,
                  DeprecationMessage = "Use WriteSaveGame with a Save.Scope.Player tag instead."))
void WritePlayerSaveData(APlayerCharacter* playerCharacter = nullptr, FName newPlayerStartTag = NAME_None);

// In .cpp — wrap the function definition AND any internal call site to suppress
// the deprecation warning that the compiler would otherwise emit against the deprecated header decl:
PRAGMA_DISABLE_DEPRECATION_WARNINGS
void US1SaveGameSubsystem::WritePlayerSaveData(APlayerCharacter* playerCharacter, FName newPlayerStartTag)
{
    if (!IsSaveGameEnabled())
    {
        return;
    }
    CollectPlayerSaveData(newPlayerStartTag, playerCharacter);
    SetTimerToSaveGame();
}
PRAGMA_ENABLE_DEPRECATION_WARNINGS

// And inside the new dispatcher that legitimately owns the implementation path:
PRAGMA_DISABLE_DEPRECATION_WARNINGS
if (bWantsPlayer)
{
    WritePlayerSaveData(playerCharacter, newPlayerStartTag);
}
// ... other internal calls
PRAGMA_ENABLE_DEPRECATION_WARNINGS
```

### DO NOT

```cpp
// BAD — hard removal in a mature BP-heavy codebase = same-day editor fire drill.
// The planner can't see which BP graphs reference the old function; they will turn red.
protected:
    void WritePlayerSaveData(APlayerCharacter* playerCharacter = nullptr, FName newPlayerStartTag = NAME_None);
    // ... was BlueprintCallable yesterday, now demoted with no migration window
```

### When hard removal IS acceptable

- The function was never `BlueprintCallable` (no BP graphs can reference it)
- The codebase is brand new / no shipped Blueprints touch the function
- Reference Viewer (in-editor) AND `grep -r` confirm zero callers in C++ AND BP

### Soft → hard transition

Plan it explicitly: schedule a future cleanup phase (e.g. `84.2-finalize-deprecation`) that hard-removes the deprecated functions only after a Reference Viewer pass confirms zero BP callers. Never lump the hard removal into the same phase that introduces the new API.

Always include a short BP migration checklist in the plan SUMMARY, but treat it as advisory, not blocking — the user should be able to ship without doing the editor work the same day.

---

## Cost of being wrong — real S1 incident, 2026-04-14

Phase 84.1 hard-removed the old `WriteSaveGame()` overload and demoted the four modular `Write*` helpers to protected. Within minutes of opening the editor, the user reported red BP nodes everywhere and a `(Multiple)` bitmask dropdown. A full follow-up cycle was needed to:

1. Switch the API to `FGameplayTagContainer`
2. Re-promote the modular helpers with `UE_DEPRECATED + DeprecatedFunction`

Both lessons would have cost zero to apply at planning time.
