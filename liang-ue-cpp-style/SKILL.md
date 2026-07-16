---
name: liang-ue-cpp-style
description: UE5.5+ C++ coding conventions. Reference when writing or reviewing C++ code for Unreal Engine projects.
---

# UE5 C++ Style Guide

Authoritative reference for writing new C++ code in UE5.5+ projects. All rules derive from the modern-layer spawner/spline codebase (Phases 1–7). When in doubt, match these conventions — not the older Combat/GAS files.

Encoding: **UTF-8**. Indentation: **tabs only** (never spaces). Brace style: **Allman** (see section 8).

## Workflow

When answering UE5 C++ style questions:
1. Apply all rules from this SKILL.md directly — these are authoritative style instructions
2. If a personal wiki exists at `F:/AI/liang-wiki/`, scan `wiki/index.md` for C++ style-related entries for project-specific patterns and decisions
3. This skill is nearly 100% instructions (not knowledge), so wiki supplements rather than replaces
4. A distilled code-block contract for the quest-family planners/executors is mirrored at `~/.pi/agent/skills/liang-skills/liang-quest-core/references/code-style/ue-cpp.md` — when editing §4, §5, §9, §10, or §11 here, update the mirror in the same pass.

---

## 1. File Layout

**Header files:**

```cpp
// Optional file-top block comment (filename + one-line description)

#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"   // UE engine base class header
#include "S1/Spawners/S1SomeClass.h"     // Project headers use S1/ prefix
#include "S1MyComponent.generated.h"     // ALWAYS last include
```

**Source files:**

```cpp
#include "S1MyComponent.h"               // Own header FIRST, no blank line before it

#include "Engine/World.h"                // UE engine headers
#include "S1/Spawners/S1Dependency.h"    // Project headers last
```

---

## 2. Forward Declarations

One class per line. `class` keyword. No tab-column alignment.

```cpp
// CORRECT
class AS1SplineActor;
class US1SpawnPatternData;
class USplineMovementPattern;

// WRONG (legacy tab-alignment — DO NOT COPY)
class	AS1SplineActor;
class	USplineComponent;
```

---

## 3. Naming Conventions

| Kind | Convention | Example |
|------|-----------|---------|
| Classes | PascalCase with UE prefix | `US1ActorSpawnerComponent`, `AS1SplineActor` |
| Structs | `F` prefix + PascalCase | `FSpawnPoolEntry`, `FSplineMovementState` |
| Enums | `E` prefix + PascalCase values | `ESplineMovementState::Moving` |
| Functions | PascalCase | `InitCycles()`, `SelectSpline()` |
| UPROPERTY members | PascalCase | `SpawnPatternData`, `Weight` |
| Boolean members | `b` prefix + PascalCase | `bIsAutoStart`, `bAutoDestroyIfFinished` |
| Local variables | PascalCase | `TotalWeight`, `ResolvedClass` |
| Function parameters | PascalCase | `SplineFollowData`, `DeltaTime` |
| Static free functions | PascalCase | `SelectFromPool` |
| Log categories | `S1Log` + Domain | `S1LogActorSpawner` |
| Integer fields/counters | `int32` always | `int32 SequentialIndex = 0;` |

**Legacy DO NOT COPY:** lower-camelCase parameters (`deltaSeconds`, `spawnCycleData`) and `int` instead of `int32`.

---

## 4. Class / Struct Layout

Section order is fixed. Full canonical UCLASS template, marker-block edge cases (multi-base, `#if WITH_EDITOR` splits), and the public-vs-protected base-class virtuals reference live in [`references/class-layout-template.md`](references/class-layout-template.md). Consult it when starting a new class. The rules below are authoritative; the reference is the worked example.

**Override visibility must match the base class.** A `public virtual` in the base stays `public` on the override; `protected virtual` stays `protected`. Demoting visibility on an override is a Liskov Substitution violation — it doesn't actually hide the function (callers reach it through any base pointer/reference, the access check is on the static type) and it confuses readers who expect the override to mirror the contract they read in the base header. Most UE engine virtuals are public; `APlayerController::SetupInputComponent`, `APawn::SetupPlayerInputComponent`, and `APlayerController::PlayerTick` are protected. When in doubt, open the base-class header — never guess; the defining base may be several levels up.

```cpp
// WRONG — base is public virtual, override silently demoted to protected
protected:
	virtual void BeginPlay() override;
```

**Override blocks MUST use `//~ Begin/End <DefiningBase> Interfaces` markers.** Three rules:

1. **Name the *defining* base** — the class that originally declares the virtual, not the immediate parent. If `UFlowNode_ChoiceOption : USoEDialogueFlowNode` overrides `ExecuteInput` (declared on `UFlowNodeBase` three levels up), the marker says `UFlowNodeBase Interfaces` — pointing at the contract source saves the reader an IDE round-trip up the chain every time the file is read.
2. **Always plural "Interfaces"** — even when the block contains a single override. Plural-everywhere is consistent and reads as "the contract" regardless of count.
3. **One marker block per defining base** — multi-interface classes write two separate marker blocks. Each contiguous group split by an access specifier or `#if` boundary also gets its own marker pair, even when the contract is the same. (See `references/class-layout-template.md` for the `#if WITH_EDITOR` split example.)

**Repeat the access specifier per logical group.** Each logical group of declarations gets its own access-specifier line, even when the level doesn't change. The repeated specifier is the section label; the blank line between groups is the section break. Canonical top-to-bottom order:

1. `public:` — Constructor
2. `public:` — Runtime overrides (one marker block per defining base)
3. `public:` — Public API (`UFUNCTION(BlueprintCallable)` and friends)
4. `protected:` — Internal helpers (if any)
5. `public:` or `protected:` — Configurable `UPROPERTY` data (visibility depends on role, below)
6. `private:` — Private state and non-`UPROPERTY` runtime fields
7. `#if WITH_EDITOR` / `#if WITH_EDITORONLY_DATA` — Editor-gated members go LAST, regardless of which contract they override

**UPROPERTY visibility depends on the class's role.** Two cases:

- `public:` for **data-carrier classes** — `UDataAsset` subclasses, Flow nodes, plain `BlueprintType` UCLASSes whose purpose is to hold author-facing data. Nothing to encapsulate; owning systems read the fields directly. See [`Project_SoE/SoE/Source/SoE/Public/Dialogue/Nodes/FlowNode_ChoiceOption.h`](Project_SoE/SoE/Source/SoE/Public/Dialogue/Nodes/FlowNode_ChoiceOption.h) for a real example.
- `protected:` for **components, actors, and subsystems** with internal lifecycle state. UPROPERTYs are exposed to the editor for tuning but not for runtime reads from arbitrary callers.

Heuristic: if the class would be just as valid as a `USTRUCT` (data, not behavior), use `public:`. Otherwise `protected:`.

**Editor-only blocks come last.** All `#if WITH_EDITOR` and `#if WITH_EDITORONLY_DATA` regions go at the bottom of the class body, after every runtime member. Even when an editor-only override (e.g., `GetNodeDescription`) belongs to the same base contract as runtime overrides at the top of the class, place it in the editor-only block at the bottom — conditional-compilation status trumps base-class grouping.

Struct layout: GENERATED_BODY then public members. Simple data structs need no access specifier.

---

## 5. UPROPERTY / UFUNCTION Formatting

**No inner spaces inside macro parentheses.** Category unquoted for single-word, quoted for sub-categories.

```cpp
UPROPERTY(EditAnywhere, Category = Spawn)
bool bIsAutoStart = true;

UPROPERTY(EditAnywhere, Category = "Spawn|Spline")
TArray<TSoftObjectPtr<AS1SplineActor>> SplineActors;

UPROPERTY(EditAnywhere, BlueprintReadOnly, meta = (ClampMin = "0.0"))
float Weight = 1.f;
```

**Long meta — break to next line with one tab indent:**

```cpp
UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spline Movement|Ground Conformance",
	meta = (ClampMin = "0.0", EditCondition = "bUseGroundConformance"))
float GroundTraceDistance = 1000.f;
```

**Legacy DO NOT COPY:**

```cpp
UPROPERTY( EditAnywhere, Category = "Tweaks" )   // spaces inside parens — OLD style
```

---

## 6. Function Signatures and Bodies

```cpp
// Header: declarations only — no body in header (except trivial getters)
void Init(const FSplineFollowData& SplineFollowData, bool bIsAutoPlay);
virtual void BeginPlay() override;

// Header: trivial inline getters only (single return statement, no side effects)
bool IsEnabled() const { return bIsEnabled; }

// Source: constructors ALWAYS in .cpp — never inline in header
US1MyComponent::US1MyComponent()
{
	PrimaryComponentTick.bCanEverTick = false;
}

// Source: always Allman
void US1MyComponent::Init(const FSplineFollowData& SplineFollowData, bool bIsAutoPlay)
{
	// body
}
```

Pass non-trivial types by `const&`. Pass scalars and booleans by value.

---

## 7. Static Free Functions

Use for pure algorithms with no `this` dependency. Place before the first member function in the `.cpp` with a banner and doc comment.

```cpp
// ---------------------------------------------------------------------------
// Weighted Random Pool Selection
// ---------------------------------------------------------------------------

/**
 * Selects a random actor class weighted by each entry's Weight field.
 * Returns nullptr if pool is empty, all entries disabled, or total weight is zero.
 */
static TSubclassOf<AActor> SelectFromPool(const TArray<FSpawnPoolEntry>& Pool)
{
	float TotalWeight = 0.f;
	for (const FSpawnPoolEntry& Entry : Pool)
	{
		if (Entry.bEnabled) { TotalWeight += Entry.Weight; }
	}

	if (TotalWeight <= 0.f) { return nullptr; }

	float Roll = FMath::FRandRange(0.f, TotalWeight);
	for (const FSpawnPoolEntry& Entry : Pool)
	{
		if (!Entry.bEnabled) { continue; }
		Roll -= Entry.Weight;
		if (Roll <= 0.f) { return Entry.ActorClass.Get(); }
	}
	return nullptr;
}
```

---

## 8. File-Scoped Constants and Namespaces

File-scoped constants (colors, column IDs, magic numbers) go in a **named private namespace** — never bare `static const`, and never an anonymous namespace. UE5 Unity builds merge multiple `.cpp` files into a single translation unit, so anonymous namespace symbols from different files collide.

**Naming pattern:** `FileName_Private` (drop the file extension and class prefix).

**Contents are indented one tab level** inside the namespace.

**Always `#undef LOCTEXT_NAMESPACE`** at the bottom of every `.cpp` that defines it — Unity builds leak the macro into subsequent files otherwise.

```cpp
// CORRECT — named private namespace, indented, Unity-build safe
#define LOCTEXT_NAMESPACE "SS1MoveBlueprintAuditTab"

namespace MoveBlueprintAuditTab_Private
{
	const FLinearColor RowEvenColor(0.0f, 0.0f, 0.0f, 0.0f);
	const FLinearColor RowOddColor(1.0f, 1.0f, 1.0f, 0.04f);

	const FName Col_AssetName("AssetName");
	const FName Col_AssetPath("AssetPath");
} // namespace MoveBlueprintAuditTab_Private

// ... class implementations using MoveBlueprintAuditTab_Private::RowEvenColor ...

#undef LOCTEXT_NAMESPACE

// WRONG — static const at file scope (C idiom, not modern C++)
static const FLinearColor RowEvenColor(0.0f, 0.0f, 0.0f, 0.0f);

// WRONG — anonymous namespace (collides under Unity builds)
namespace
{
	const FLinearColor RowEvenColor(0.0f, 0.0f, 0.0f, 0.0f);
}
```

---

## 9. Brace Style (Allman — MANDATORY)

Opening brace always on its own line. No exceptions for functions, if/else, for, while, switch.

```cpp
// CORRECT
void MyFunction()
{
	if (Condition)
	{
		DoSomething();
	}
	else
	{
		DoOther();
	}
}

// WRONG (K&R / Egyptian — DO NOT COPY)
void MyFunction() {
	if (Condition) {
```

**One exception — aggregate initialization uses inline `{}`:**

```cpp
MovementState = FSplineMovementState{};    // reset to defaults — OK
```

---

## 10. Early Return Guards

Validate preconditions at the top of a function. Actual logic follows flat, without deep nesting.

```cpp
void US1MyComponent::DoWork()
{
	if (!StreamHandle.IsValid() || !StreamHandle->HasLoadCompleted())
	{
		return;
	}

	if (!ensureMsgf(SomeData != nullptr, TEXT("%s: SomeData is null"), *GetOwner()->GetName()))
	{
		return;
	}

	// actual logic — no deep nesting
	ProcessData(*SomeData);
}
```

Use `ensureMsgf` for programmer-error soft asserts. Use `UE_LOG` + return for runtime misconfigurations.

---

## 11. Initialization

In-class initializers are preferred for all data members — UPROPERTY and non-UPROPERTY alike.

```cpp
UPROPERTY(EditAnywhere, Category = Spawn)
bool bIsAutoStart = true;

// Non-UPROPERTY fields MUST also have initializers — UE does not zero them
bool bIsRegistered = false;
int32 SequentialIndex = 0;
```

Constructor initializer list for non-trivial initialization:

```cpp
US1ActorSpawnerComponent::US1ActorSpawnerComponent()
	: bIsEnabled(true)
	, bIsRegisteredInSubsystem(false)
{
	PrimaryComponentTick.bCanEverTick = false;
}
```

Struct reset: `MovementState = FSplineMovementState{};`

---

## 12. Conditional Compilation

```cpp
// Editor-only code (IsDataValid, validation overrides)
#if WITH_EDITOR
	virtual EDataValidationResult IsDataValid(FDataValidationContext& Context) const override;
#endif

// Editor data + shipping-strip (DebugDraw functions and debug properties)
#if WITH_EDITORONLY_DATA
	void DebugDraw() const;
	void DebugDrawGroundTrace(const FVector& Start, const FVector& End) const;
#endif

// Gameplay debug in non-shipping builds (PIE debug draw)
#if ENABLE_DRAW_DEBUG
	void DrawDebugSpline();
#endif
```

All `DebugDraw*` and `DrawDebug*` helpers go inside `WITH_EDITORONLY_DATA` unless they need to run in non-editor dev builds (use `ENABLE_DRAW_DEBUG` then).

---

## 13. Soft References and Async Loading

```cpp
TSoftClassPtr<AActor> ActorClass;                 // async-loadable class ref
TSoftObjectPtr<AS1SplineActor> SplineActor;       // async-loadable object ref
TObjectPtr<USplineMovementPattern> Pattern;       // hard ref for owned/Instanced UObjects
```

Async load pattern — batch in `InitCycles`/`BeginPlay`, gate on completion:

```cpp
TArray<FSoftObjectPath> AssetsToLoad;
AssetsToLoad.Add(Entry.ActorClass.ToSoftObjectPath());
StreamHandle = US1AssetManager::GetStreamableManager().RequestAsyncLoad(AssetsToLoad);

// Gate execution on load completion
if (!StreamHandle.IsValid() || !StreamHandle->HasLoadCompleted())
{
	return;
}
TSubclassOf<AActor> Class = Entry.ActorClass.Get();
```

**Never call `LoadSynchronous()` at spawn time** — it hitches the game thread.

---

## 14. Container Iteration

**Range-for over `TArray<TObjectPtr<T>>`:** Always use a raw pointer, never `const TObjectPtr<T>&`. `TObjectPtr` is pointer-sized — iterating by const ref adds unnecessary indirection.

```cpp
// CORRECT — raw pointer, idiomatic UE5
for (US1SpawnNode* Child : Children)
{
	if (Child)
	{
		Child->Start(Context);
	}
}

// WRONG — const ref to TObjectPtr is unnecessary indirection
for (const TObjectPtr<US1SpawnNode>& Child : Children)
{
	if (Child)
	{
		Child->Start(Context);
	}
}
```

**Range-for over `TArray<FStruct>`:** Use `const&` for read-only, `&` for mutation — standard C++ value semantics.

```cpp
for (const FSpawnPoolEntry& Entry : Pool)    // read-only
for (FSpawnedActorData& Request : Requests)  // mutation
```

**Range-for over `TArray<TSoftObjectPtr<T>>`:** Use `const TSoftObjectPtr<T>&` — soft pointers contain a path string, not pointer-sized.

```cpp
for (const TSoftObjectPtr<AS1SplineActor>& Soft : SplineActors)
```

---

## 15. Logging

```cpp
UE_LOG(S1LogActorSpawner, Warning, TEXT("%s: Spawn pool is empty or all entries disabled"),
	*GetOwner()->GetName());

S1_LOG_ERROR(S1LogActorSpawner, 10.f, TEXT("StreamHandle not valid — cannot spawn"));
```

Always include `*GetOwner()->GetName()` or equivalent actor context in log messages.

---

## 16. Comments and Documentation

```cpp
/** Doc comment for properties and functions — JavaDoc style.
 *  Soft pointers for level-streaming compatibility. */
UPROPERTY(EditAnywhere, Category = "Spawn|Spline")
TArray<TSoftObjectPtr<AS1SplineActor>> SplineActors;

// Inline explanation for non-obvious logic
SpawnCycleHandle.SpawnCountRemain = (SpawnPatternData->CycleCount == 0) ? -1 : SpawnPatternData->CycleCount;

//~ Begin UActorComponent Interfaces    // section markers for interface implementations
virtual void BeginPlay() override;
//~ End UActorComponent Interfaces

// ---------------------------------------------------------------------------
// Section Name                         // banner comments for .cpp major sections
// ---------------------------------------------------------------------------
```

Do not right-pad member declarations with tabs to align `//` comments — that is legacy style.

---

## 17. Line Length

Hard limit: **140 characters**. Never wrap lines shorter than 140 chars across multiple lines.

- Function calls that fit within 140 chars stay on **one line** — do not split arguments across lines for "readability"
- If a line exceeds 140 chars, break after `(` or `,` and indent continuation with one tab
- Lambda bodies follow Allman brace rules but the `BindLambda([Captures]()` opening stays on one line

```cpp
// GOOD — fits in 140 chars, one line
NiagaraComp->DetachFromComponent(FDetachmentTransformRules::KeepWorldTransform);
World->GetTimerManager().SetTimer(TimerHandle, TimerDelegate, MaxPersistLifetime, false);

// BAD — unnecessary wrapping of a short call
NiagaraComp->DetachFromComponent(
	FDetachmentTransformRules::KeepWorldTransform);
```

---

## 18. Anti-Patterns (DO NOT COPY)

These exist in older files (CombatComponent, pre-Phase-1 spawners). Never replicate in new code.

| Pattern | Why Wrong | Use Instead |
|---------|----------|-------------|
| `UPROPERTY( EditAnywhere )` — inner spaces | Legacy formatting | `UPROPERTY(EditAnywhere)` |
| Tab-column-aligned type columns in class bodies | Breaks on font change | One declaration per line, no padding |
| Lower-camelCase parameters (`deltaSeconds`) | Inconsistent with modern layer | PascalCase (`DeltaSeconds`) |
| `int` instead of `int32` | Platform-dependent size | `int32` always |
| `LoadSynchronous()` at spawn time | Game thread hitch | `RequestAsyncLoad` + `HasLoadCompleted` gate |
| `DuplicateObject` per spawn for pattern instances | GC pressure per-spawn | Shared immutable pattern + per-instance state struct |
| Missing in-class initializers for non-UPROPERTY fields | Uninitialized memory bugs | Always provide `= value` for every plain data member |
| `DebugDraw*` without `#if WITH_EDITORONLY_DATA` | Debug code ships | Wrap all debug helpers in `WITH_EDITORONLY_DATA` |
| `static const` at file scope for constants | C idiom, not modern C++; also unsafe under Unity builds | Named private namespace `FileName_Private` |
| Anonymous namespace (`namespace { }`) for file-scoped constants | Unity builds merge `.cpp` files into one TU — symbols collide | Named private namespace `FileName_Private` |
| Missing `#undef LOCTEXT_NAMESPACE` at end of `.cpp` | Unity builds leak the macro into subsequent files in the TU | Always `#undef LOCTEXT_NAMESPACE` at file bottom |
| `class\tMyClass;` (tab in forward declaration) | Alignment anti-pattern | `class MyClass;` — single space |
| `Array.Num() > 0 && Array[0]` for first-element access | Redundant, harder to read | `Array.IsValidIndex(0)` — single bounds check |
| `for (const TObjectPtr<T>& X : Array)` | Unnecessary indirection — TObjectPtr is pointer-sized | `for (T* X : Array)` — raw pointer iteration |
| Inline constructor body in header | Constructors belong in .cpp for consistent linkage and compilation | Move constructor to .cpp — even single-assignment constructors |
| `TArray<const T*>` or `TArray<T*>` in UFUNCTION return type | UHT cannot expose raw/const pointers in Blueprint containers — causes "Inappropriate keyword 'const'" | Return `TArray<T>` by value for UFUNCTION accessors |
| `AddLambda` / `AddWeakLambda` on dynamic multicast delegates | `DECLARE_DYNAMIC_MULTICAST_DELEGATE` only supports `AddDynamic` with a `UFUNCTION` — lambda binding won't compile | Use `AddDynamic` + `UFUNCTION`, or skip binding if alternative cleanup exists (e.g., `SetAutoDestroy` + safety timer) |
| `UPROPERTY() TMap<UClass*, TArray<TObjectPtr<T>>>` | UHT cannot use nested containers (`TArray<TObjectPtr<>>`) as a TMap value type with UPROPERTY — compile error: "The type 'TArray<TObjectPtr<T>>' can not be used as a value in a TMap" | Wrap the inner array in a USTRUCT with `GENERATED_BODY()` and `UPROPERTY()`, then use `TMap<TObjectPtr<UClass>, FMyFreeList>` |
| Override visibility differs from the base virtual (either direction — `public` base demoted to `protected`, OR `protected` base widened to `public`) | Demotion: LSP violation; doesn't actually hide the function (still reachable through any base pointer/reference). Widening: gratuitous API exposure (e.g. `APlayerController::SetupInputComponent` is `protected` because gameplay code is meant to call `EnableInput`/`Possess`, not the input setup directly). Both are flagged by Rider/ReSharper and confuse readers who expect the override to mirror the base contract | Match parent visibility exactly — `public` stays `public`, `protected` stays `protected`. When in doubt, open the base-class header |
| Compiler emits C4263/C4264/C4266 from `Source/SoE/**` (subclass declaration shadows or partially hides a base virtual) | Silently *hides* the base virtual instead of overriding it. Engine and Blueprint calls (the `SetActive` BP node, tick activation, `OnComponentActivated` events, replication awareness) bypass the subclass version. `liang-loop-verifier` surfaces these warnings via grep-and-fix during `/liang-workflow-loop`, so the executor sees them in the same iteration as any compile errors | Apply the default-fix heuristic: if the original code carried `override` → fix as proper override (signature match + `override` keyword + `Super::` call); else → rename to a domain verb (`SetSeeking(bool)`, `BeginSeek()`, `Set<Thing>Enabled(bool)`). For component activation specifically, prefer `Activate(bool bReset)` / `Deactivate()` over `SetActive(bool, bool)`. See the **"Engine-virtual shadowing"** detail subsection below |
| `EnhancedInputComponent->BindAction(...)` (or sibling action-binding APIs) called in C++ | Couples input wiring to the compile cycle — designer-mode iteration triggers programmer-mode recompile. SoE is BP-first for input by absolute rule | Override `SetupInputComponent` / `SetupPlayerInputComponent`, cast EIC with null guard, then call the canonical `ReceiveSetupEnhancedInputComponent` BIE. All action→function binding lives in BP. See §20 |

### TMap with complex value types

UHT only accepts simple scalars, UObject pointers, and USTRUCTs as `TMap` value types when the `TMap` itself is a `UPROPERTY`. Nested containers (`TArray<TObjectPtr<>>`, `TArray<TArray<>>`, etc.) are **not** supported directly.

```cpp
// WRONG — UHT compile error: "cannot be used as a value in a TMap"
UPROPERTY(Transient)
TMap<UClass*, TArray<TObjectPtr<UMoveAction>>> ActionPool;

// CORRECT — wrap the inner container in a USTRUCT
USTRUCT()
struct FMoveActionFreeList
{
	GENERATED_BODY()

	UPROPERTY()
	TArray<TObjectPtr<UMoveAction>> Actions;
};

UPROPERTY(Transient)
TMap<TObjectPtr<UClass>, FMoveActionFreeList> ActionPool;
```

Access the inner array via the struct field:

```cpp
// Acquire
if (FMoveActionFreeList* Entry = ActionPool.Find(ActionClass))
{
	if (Entry->Actions.Num() > 0)
	{
		TObjectPtr<UMoveAction> Acquired = Entry->Actions.Last();
		Entry->Actions.RemoveAt(Entry->Actions.Num() - 1, EAllowShrinking::No);
		return Acquired;
	}
}

// Return
ActionPool.FindOrAdd(Action->GetClass()).Actions.Add(Action);
```

### Engine-virtual shadowing

This subsection focuses on the one prescriptive carve-out the compiler can't teach: which UE virtual is the right hook for component activation. `UActorComponent` exposes `SetActive(bool, bool)`, `Activate(bool)`, and `Deactivate()`. A subclass that declares any of these names with a different signature *hides* the base — name lookup through a base pointer no longer finds the subclass version, and the engine's wiring (Blueprint `SetActive` node, replication awareness, `OnComponentActivated`/`Deactivated` events) bypasses your code. General shadow violations across other engine virtuals are caught reactively by the verifier (see "Detection — verifier-driven" below); this section teaches the activation-specific override choice.

```cpp
// CORRECT — domain verb names the behavior, not the state
void USoEInteractionSeekerComponent::SetSeeking(bool bIn);
void USoEInteractionSeekerComponent::BeginSeek();
void USoEInteractionSeekerComponent::StopSeek();
```

```cpp
// WRONG — single-bool member shadows UActorComponent::SetActive(bool, bool)
void SetActive(bool bIn);   // C4263: does not override base virtual
                            // C4264: hides UActorComponent::SetActive(bool, bool)
```

**Exception — proper override.** When extending an engine virtual *is* what you want:

**Pick the right virtual first.** For component activation, prefer `Activate(bool bReset)` and `Deactivate()` over `SetActive(bool, bool)`. `SetActive` is the public dispatcher — its only job is to route to `Activate` or `Deactivate` based on the bool. Overriding `SetActive` misses every code path that bypasses it:

- `bAutoActivate = true` initialization (engine sets the component active without ever calling `SetActive`)
- `RegisterComponent` for components that start active
- Replication-driven activation
- Direct `Activate()` / `Deactivate()` calls from gameplay code

Overriding `Activate`/`Deactivate` catches all of those paths, and `OnComponentActivated` / `OnComponentDeactivated` events keep firing automatically because the base dispatcher still runs. Reserve `SetActive` overrides for the rare case where you must gate the dispatcher itself (e.g., reject the call entirely under some condition before any activation work happens). UE's own subclasses (`UMovementComponent`, `UPrimitiveComponent`) follow this pattern.

The override itself MUST:

1. Match the base signature exactly — parameter count, types, AND default arguments.
2. Be marked `override`.
3. Call `Super::<Name>(...)` somewhere in the body unless deliberately replacing behavior.

```cpp
// CORRECT — extend Activate / Deactivate (the canonical extension points)
virtual void Activate(bool bReset = false) override;
virtual void Deactivate() override;

void USoEInteractionSeekerComponent::Activate(bool bReset)
{
    Super::Activate(bReset);
    // domain-specific extension — runs for SetActive(true), bAutoActivate,
    // RegisterComponent, replication-driven activation, all of them
}

void USoEInteractionSeekerComponent::Deactivate()
{
    // domain-specific cleanup
    Super::Deactivate();
}
```

```cpp
// LESS GOOD — overriding SetActive only catches calls that flow through
// the dispatcher; bAutoActivate, RegisterComponent, and replication-driven
// activation paths skip it entirely. Use only when gating the dispatcher
// itself is the actual requirement.
virtual void SetActive(bool bNewActive, bool bReset = false) override;
```

**Default-fix heuristic.** When the verifier surfaces a C4263/C4264/C4266 warning, the executor picks the fix as follows:

- (a) If the original declaration carried the `override` keyword → author intended override; fix the signature to match the base exactly, keep `override`, and add `Super::<Name>(...)` in the body unless deliberately replacing behavior.
- (b) If the original declaration did NOT carry `override` → rename to a domain verb (`SetSeeking`, `BeginSeek`, `Set<Thing>Enabled`, etc.).

This heuristic is mechanical and applies to every shadow warning the verifier surfaces, not just the activation case above. The free-form justification comment requirement on `SetActive` overrides is the one place where prose (rather than the heuristic) is required — author still writes a one-line comment explaining why the dispatcher itself must be gated.

### Detection — verifier-driven

Shadow violations are caught by a `detection-first` / `grep-and-fix` workflow inside `/liang-workflow-loop`. The compiler — not a maintained denylist of engine-virtual names — is the source of truth for which subclass declaration hides which base virtual.

- `liang-loop-verifier` greps the captured build output (stdout + stderr) for lines matching `path(line(,col)?): warning C4263|C4264|C4266: …` where `path` matches `Source/SoE` slash-agnostically (UBT mixes `/` and `\` on Windows).
- The scan runs unconditionally — even when `Build.bat` exits 0, and also when it exits non-zero — so a shadow warning co-occurring with a compile error lands in the same `error_detail` and reaches the executor in a single iteration.
- The executor receives raw concatenated UBT lines verbatim (no grouping, no reformatting) and applies the **Default-fix heuristic** above.
- Scope is `Source/SoE/**` exclusively. Engine headers, vendor plugins, generated UHT headers, and first-party plugins (none exist yet) are excluded by the path filter — the agent has no fix path for those.
- No build-config edits are required. The phase that introduced this workflow does not touch `SoE.Build.cs`, `SoEEditor.Build.cs`, any `*.Target.cs`, any PCH, or any `#pragma warning(default:...)` insertion. Detection runs on whatever warnings UBT already emits.

## 19. Refactoring BlueprintCallable APIs in a Mature Codebase

Two hard-won defaults that apply any time you change a `UFUNCTION(BlueprintCallable)` signature, demote it, or replace it with something new in a project with shipped Blueprints. Full code examples, the `AutoCreateRefTerm` mandatory rule, and the 2026-04-14 incident summary live in [`references/refactor-bp-callable.md`](references/refactor-bp-callable.md). Read it before planning any phase that touches BP-facing C++ signatures.

- **19.1 Prefer `FGameplayTagContainer` over `UENUM(meta=(Bitflags))`** for BP-facing scope/filter parameters. The bitmask UI collapses to `"(Multiple)"` and is unreadable; tag containers give a clean "Add Tag" UI and match the GAS pattern designers know. Mandatory companion rule: any `UFUNCTION(BlueprintCallable)` taking `const T&` (struct by reference) MUST set `meta=(AutoCreateRefTerm="<paramName>")` or BP designers hit a "must have an input wired" compile error.
- **19.2 Soft-deprecate via `UE_DEPRECATED` + `meta=(DeprecatedFunction)`** instead of hard-removing a `BlueprintCallable`. Existing BP graphs keep compiling with a yellow warning. Schedule the hard-removal in a separate later phase only after Reference Viewer confirms zero BP callers — never in the same phase that introduces the replacement API.

## 20. Input Binding — BP-First (Mandatory)

**Never call `EnhancedInputComponent::BindAction` (or any sibling action-binding API) in C++.** All action-to-function wiring lives in Blueprint. C++ exists only to (a) push input mapping contexts and (b) dispatch to a canonical BIE so the BP child can wire actions without recompiling.

**Absolute rule, zero exceptions.** Applies to:

- `APlayerController::SetupInputComponent`
- `APawn::SetupPlayerInputComponent` (and `ACharacter` by inheritance)

**Canonical BIE name: `ReceiveSetupEnhancedInputComponent`.** Always this exact name across the project, regardless of class. Matches UE's `Receive*` convention (`ReceiveBeginPlay`, `ReceiveTick`) — designer always knows where to look.

**IMC management stays in C++.** `AddMappingContext` / `RemoveMappingContext` / priority changes are engine plumbing, not action binding. Keep IMC pushing in `BeginPlay` / possession callbacks as usual — the rule is specifically about action→function binding.

```cpp
// CORRECT — C++ does null guards + EIC cast, then hands off to BP via the canonical BIE.
// Live pattern: Project_SoE/SoE/Source/SoE/Private/Core/SoEPlayerController.cpp

// Header
protected:
	UFUNCTION(BlueprintImplementableEvent, Category = "Input")
	void ReceiveSetupEnhancedInputComponent();

// Source
void ASoEPlayerController::SetupInputComponent()
{
	Super::SetupInputComponent();

	UEnhancedInputComponent* EnhancedInputComponent = Cast<UEnhancedInputComponent>(InputComponent);
	if (EnhancedInputComponent == nullptr)
	{
		return;
	}

	ReceiveSetupEnhancedInputComponent();
}
```

```cpp
// WRONG — BindAction in C++ couples input wiring to the compile cycle.
void ASoEPlayerController::SetupInputComponent()
{
	Super::SetupInputComponent();

	UEnhancedInputComponent* EnhancedInputComponent = Cast<UEnhancedInputComponent>(InputComponent);
	if (EnhancedInputComponent == nullptr)
	{
		return;
	}

	// FORBIDDEN — designer-mode iteration now requires programmer-mode recompile.
	EnhancedInputComponent->BindAction(InteractAction, ETriggerEvent::Started, this, &ASoEPlayerController::HandleInteractPressed);
}
```

The BP child overrides `ReceiveSetupEnhancedInputComponent` and either:

1. Drops IA event nodes in the event graph (auto-bound when the IMC is pushed) — preferred
2. Uses BP `BindAction` nodes inside the override — when explicit binding is needed

C++ exposes gameplay actions as `UFUNCTION(BlueprintCallable)` so BP can call them from IA event handlers. The `HandleInteractPressed`-style C++ method becomes a `BlueprintCallable` helper on the responsible class (e.g., `USoEInteractionSeekerComponent`), invoked from the BP graph.

**Forward-looking only.** This rule applies to NEW code. Legacy `BindAction` calls in existing C++ stay untouched — do NOT flag, comment, or propose refactors when encountering them. Migration is incidental, only when a file is being touched for unrelated reasons.

**Deferred — GAS ability activation.** When an Ability System Component is introduced to SoE, the ability-input pattern (`BindAbilityActivationToInputComponent`, `AbilityLocalInputPressed`, etc.) needs explicit guidance. Decide at the point GAS actually lands; the absolute rule above covers Enhanced Input only.

## Personal Knowledge Base

When answering UE5 C++ style questions, check if a personal wiki exists at `F:/AI/liang-wiki/`.
If it does, scan `wiki/index.md` for entries tagged `gamedev` or containing C++ style-related
keywords (cpp, style, coding-conventions). Read relevant pages for personal project
context, gotchas, and coding conventions.
SKILL.md knowledge is primary; wiki adds personal context on top.
If the wiki has no relevant content, proceed with built-in knowledge only.
