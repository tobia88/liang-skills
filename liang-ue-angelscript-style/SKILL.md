---
name: liang-ue-angelscript-style
description: Generate AngelScript code following Unreal Engine AngelScript coding conventions. Use when creating .as files, writing functions, or checking code style against standard AngelScript patterns.
---

# AngelScript Code Generator & Style Verifier

Generate and verify AngelScript code for Unreal Engine that follows established coding style, patterns, and conventions.

## Core Directive

When generating or reviewing AngelScript (.as) code, you MUST:
1. Read existing similar files from the codebase for context and pattern matching
2. Apply ALL style patterns documented below consistently
3. Follow project-specific architectural patterns (reference project documentation)
4. Generate code that matches the project's established coding style
5. **Verify** generated code against AngelScript language rules (see wiki page [[angelscript-language-reference]])
6. **Compile-check** after writing .as files — check the Unreal Editor log at `Saved/Logs/{Project}.log` for `Angelscript: Error:` lines to verify compilation succeeded. Fix any errors before declaring the code complete.

## AngelScript Language Fundamentals

**These are NOT optional — violating them causes compilation errors.**

### Critical Differences from C++
- **No pointers**: Use `.` (dot) everywhere, never `->` (arrow)
- **No constructors**: Use inline initialization and `default` statements
- **UPROPERTY() defaults**: `EditAnywhere` + `BlueprintReadWrite` (opposite of C++)
- **UFUNCTION() defaults**: `BlueprintCallable` (opposite of C++)
- **RPCs default to reliable** (opposite of C++, add `Unreliable` explicitly)
- **`float` is 64-bit double**: Use `float32` for explicit 32-bit
- **No header/source split**: Everything in a single `.as` file
- **No forward declarations** needed

### Syntax That WILL NOT Compile
```angelscript
// ❌ Actor->GetLocation()           → ✅ Actor.GetActorLocation()
// ❌ FMath::Clamp(...)              → ✅ Math::Clamp(...)
// ❌ UClass::StaticClass()          → ✅ UClass.Get()
// ❌ f"Text {a ? b : c}"           → ✅ Extract ternary first, then f-string
// ❌ UFUNCTION() on struct methods  → ✅ Plain methods only on structs
// ❌ LifeSpanExpired() override     → ✅ System::SetTimer() pattern
```

### Name Simplification (C++ → AngelScript)
- `FMath::` → `Math::`
- `UKismetSystemLibrary::` → `System::`
- `UGameplayStatics::` → `Gameplay::`
- `ReceiveBeginPlay` → `BeginPlay`
- `::StaticClass()` → `.Get()`
- `BP_`, `K2_`, `Received_` prefixes are stripped

### Component Declaration
```angelscript
UPROPERTY(DefaultComponent, RootComponent)
USceneComponent SceneRoot;

UPROPERTY(DefaultComponent, Attach = SceneRoot)
UStaticMeshComponent Mesh;
```

### Default Values (no constructors)
```angelscript
class AMyActor : AActor
{
	UPROPERTY()
	float Speed = 100.0;

	default bReplicates = true;
	default Mesh.bHiddenInGame = true;
}
```

### Delegates and Events
```angelscript
// Single binding
delegate void FMyDelegate(float Value);

// Multicast (event dispatcher)
event void FOnDamaged(float Amount);

// Bound functions MUST be UFUNCTION()
```

### FName Literals
```angelscript
FName MyName = n"MyName";  // Compile-time, no runtime lookup
```

**For complete language reference**, see wiki page [[angelscript-language-reference]]

---

## Comment Separator Patterns

### Major Section Separators
Use for class-level organization (Configuration, Events, Runtime State, Public API, Lifecycle):

```angelscript
// ------------------------------------------------------------
// Section Name
// ------------------------------------------------------------
```

**Rules:**
- Exactly 60 dashes (no more, no less)
- Space after `//`
- Used for: Components, Configuration, Events, Runtime State, Public API, Lifecycle, Event Handlers, Internal Functions

### Sub-Section Separators
Use for grouping related methods within a section (e.g., "Explosion Logic", "Movement Helpers"):

```angelscript
//------------------------------------------------------------
// Subsection Name
//------------------------------------------------------------
```

**Rules:**
- Exactly 60 dashes
- NO space after `//`
- Used for: Method groups, specialized logic sections

## Class Structure & Section Order

Always organize classes in this exact order:

1. **Configuration**
   - UPROPERTY fields (EditAnywhere, Category)
   - Public configuration values

2. **Events**
   - Event delegate declarations (`event void FOnSomething(...)`)

3. **Runtime State**
   - UPROPERTY fields (NotEditable, Transient)
   - Non-UPROPERTY member variables
   - Cached references

4. **Public API**
   - Public methods that external code calls
   - Initialize, Activate/Deactivate methods

5. **Lifecycle**
   - BeginPlay, EndPlay, Tick
   - Blueprint override methods

6. **Event Handlers**
   - Methods with `Handle` prefix
   - Delegate callback implementations

7. **Internal Functions**
   - Private helper methods
   - Calculation/utility functions

8. **Getters/Queries**
   - BlueprintPure methods
   - Boolean queries (Is*, Can*, Has*, Should*)

## Variable Naming Conventions

Apply these prefixes consistently:

| Prefix | Usage | Examples |
|--------|-------|----------|
| `b` | Booleans | `bIsActive`, `bExploded`, `bIsFiring`, `bRequestFire` |
| `Current` | State variables | `CurrentVelocity`, `CurrentGameState`, `CurrentQuat` |
| `Cached` | Cached references | `CachedOwnerPawn`, `CachedCapsule`, `CachedAttributeComponent` |
| `Owner` | Parent references | `OwnerWeaponComponent`, `OwnerMovementComponent`, `OwnerActor` |
| `Active` | Running instances | `ActiveWeapons`, `ActiveAbilities`, `ActiveWaveVolume` |
| `Pending` | Queued operations | `PendingWaveEntry`, `PendingRotationRequest` |

**Other naming rules:**
- No prefix for UPROPERTY fields: `Speed`, `Damage`, `ProjectileLifeSpan`
- PascalCase for local variables: `NewWeapon`, `TargetVelocity`, `SpawnLocation`
- Descriptive over concise: `MaxWalkSpeed` not `MaxSpd`
- No abbreviations unless universally understood

## Method Naming Conventions

| Pattern | Prefix/Format | Examples |
|---------|---------------|----------|
| Event handlers | `Handle` prefix | `HandleOnClick()`, `HandleOnWaveCompleted()` |
| Blueprint events | `BP_` prefix | `BP_PickedUp()`, `BP_OnDamaged()` |
| Boolean queries | `Can`, `Is`, `Has`, `Should` | `CanAddWeapon()`, `IsActivated()`, `HasWeaponAtSlot()` |
| Actions | Verb first | `BeginShoot()`, `EndShoot()`, `UpdateVelocity()` |
| Getters | `Get` prefix | `GetCurrentVelocity()`, `GetGravityMultiplier()` |
| State transitions | Clear verbs | `TransitionToState()`, `EnterState()`, `ExitState()` |

## Code Structure Patterns

### Key Principles

- **Early returns over nested ifs** - Use guard clauses to avoid deeply nested logic
- **Extract complex logic** - Move complex conditions/calculations into well-named helper methods
- **No defensive programming** - Trust initialization; only check when genuinely uncertain

**For detailed examples with correct/incorrect comparisons**, see wiki page [[angelscript-code-examples]]

## Logging Patterns

### Log Category Declaration

**For constants shared across multiple files in a system, use namespaces:**

```angelscript
// In SystemConst.as
namespace SystemConst
{
	const FName LogSystem = n"LogSystem";
}

// Usage in other files
Log(SystemConst::LogSystem, f"Initialized system");
LogDisplay(SystemConst::LogSystem, f"State changed to {NewState}");
```

**For file-specific log categories, declare at the top of file:**

```angelscript
const FName LogMySystem = n"LogMySystem";
```

**When to use each:**
- **Namespace** - Multiple files in a system need the same log category (preferred for modular systems)
- **File-level** - Single file or unique log category not shared with other files

### Logging Functions (4 types)

AngelScript provides **four** logging functions, all taking signature: `FunctionName(FName Category, FString Message)`

| Function | Purpose | When to Use |
|----------|---------|-------------|
| `Log()` | Verbose/detailed logging | Detailed flow tracking, verbose debug info |
| `LogDisplay()` | Informational logging | **Most common** - general information, state changes |
| `Warning()` | Warning messages | Recoverable issues, unexpected but handled conditions |
| `Error()` | Error messages | Serious problems, failed operations |

### F-String Interpolation

Supports: `f"Text {Variable}"`, `f"Value: {Object.Property}"`, `f"Result: {Method()}"`, `f"Formatted: {Value:.2f}"`

**CRITICAL**: F-strings do **NOT** support ternary operators. Extract conditional logic first:
```angelscript
// ❌ WRONG - f"Name: {Actor != nullptr ? Actor.GetName() : "Unknown"}"
// ✅ CORRECT
FString ActorName = (Actor != nullptr) ? Actor.GetName() : "Unknown";
f"Name: {ActorName}"
```

### FName Type Handling

**Create FName**: Use `n"Name"` literal or `FName("Name")` constructor

**Ternary operators - Both branches must match type:**
```angelscript
// ❌ WRONG - FName Name = (Actor != nullptr) ? Actor.GetName() : "Unknown";
// ✅ CORRECT - Use n"Unknown" to match FName type
FName Name = (Instigator != nullptr) ? Instigator.GetName() : n"Unknown";
```

### Print() vs Logging Functions

**Use `Print()` for:**
- Temporary debug output during development
- User-facing messages
- Quick testing

**Use `Log/LogDisplay/Warning/Error()` for:**
- Systematic logging with categories
- Production code logging
- Tracking system state and flow

## Namespace Constants Pattern

When a system has constants that need to be shared across multiple files, use a dedicated namespace const file:

### File Structure
```angelscript
// {Project}{System}Const.as - Shared constants for the system
namespace {Project}{System}Const
{
	const FName Log{System} = n"Log{System}";
}
```

### Naming Conventions
- **File name**: `{Project}{System}Const.as` (e.g., `SoloCombatConst.as`)
- **Namespace**: `{Project}{System}Const` (matches file name without `.as`)
- **Access pattern**: `NamespaceName::ConstantName`

## Gameplay Tag Constants

Use predefined constants from the `GameplayTags::` namespace instead of runtime lookups:

```angelscript
// ❌ WRONG - Runtime string lookup
FGameplayTag LaunchTag = FGameplayTag::RequestGameplayTag(n"Effect.Launched");

// ✅ CORRECT - Use predefined constant
FGameplayTag LaunchTag = GameplayTags::Effect_Launch;
```

## Type Casting

Explicit `Cast<T>()` is **required** for downcasting:

```angelscript
// ❌ WRONG - Implicit downcast not supported
AMyCharacter Character = SomeActor;

// ✅ CORRECT - Explicit Cast<> required
AMyCharacter Character = Cast<AMyCharacter>(SomeActor);
if (Character != nullptr)
{
	Character.DoThing();
}
```

## UPROPERTY Patterns

```angelscript
// Configuration
UPROPERTY(EditAnywhere, Category = "Movement")
float MaxWalkSpeed = 600.f;

// Blueprint readable
UPROPERTY(BlueprintReadOnly, Category = "Upgrade")
UWeaponUpgradeData UpgradeData;

// Runtime state
UPROPERTY(NotEditable, Transient)
UUserWidget MainHUDWidget;

// Components
UPROPERTY(DefaultComponent, RootComponent)
USphereComponent CollisionComponent;

UPROPERTY(DefaultComponent, Attach = CollisionComponent)
UStaticMeshComponent ProjectileMesh;
```

## Formatting Rules

- **Indentation**: Use tabs (never spaces)
- **Blank lines**:
  - 1 blank line between methods
  - 2 blank lines before major section separators
  - No blank lines between related variable declarations
- **Spacing**:
  - Space after commas: `FVector(0.f, 0.f, 100.f)`
  - Space around operators: `Count = Math::Min(3, Available.Num());`
  - No space before function parentheses: `BeginPlay()`
  - Space after control keywords: `if (`, `for (`, `while (`
- **Line length**: Generally under 120 characters
- **Brace style**: Opening brace on same line, closing on new line aligned with opening statement

## Complete Class Example

**For a fully-annotated class template**, see wiki page [[angelscript-class-template]]

## AngelScript vs C++ Naming Differences

AngelScript for Unreal Engine uses different naming conventions than C++ Unreal Engine. **NEVER use C++ syntax** - always use AngelScript equivalents:

### Math Functions
```angelscript
// ❌ WRONG - C++ Unreal Engine syntax
float Clamped = FMath::Clamp(Value, 0.f, 1.f);

// ✅ CORRECT - AngelScript syntax
float Clamped = Math::Clamp(Value, 0.f, 1.f);
```

**Rule**: Use `Math::` namespace, **NOT** `FMath::`. Drop the `F` prefix from all math functions.

### Class References
```angelscript
// ❌ WRONG - C++ syntax
Target.AbilitySystemComponent.ApplyEffect(UMyEffect::StaticClass());

// ✅ CORRECT - AngelScript syntax
Target.AbilitySystemComponent.ApplyEffect(UMyEffect.Get());
if (Actor.IsA(AMyCharacter.Get())) { ... }
```

**Rule**: Use `.Get()` to obtain class references (TSubclassOf), **NOT** `::StaticClass()` or `::Class`.

### Common Pitfalls
- **FVector, FRotator, FTransform**: Keep the `F` prefix for data types (these are the same)
- **Math functions**: Always drop the `F` prefix (`Math::` not `FMath::`)
- **Class references**: Use `.Get()` instead of `::StaticClass()`
- **Type names**: Most UE types keep their prefixes (UObject, AActor, UActorComponent, etc.)

## Actor Lifecycle Override Limitations

Some C++ lifecycle methods are **NOT** available as `BlueprintOverride` in AngelScript.

### LifeSpanExpired() - NOT Available

Use `System::SetTimer()` with `FTimerHandle` instead:
```angelscript
UPROPERTY()
FTimerHandle LifeSpanTimerHandle;

UFUNCTION(BlueprintOverride)
void BeginPlay()
{
	LifeSpanTimerHandle = System::SetTimer(this, n"HandleLifeSpanExpired", ProjectileLifeSpan, false);
}

UFUNCTION()
void HandleLifeSpanExpired()
{
	Deactivate();
}
```

### Timer API
```angelscript
// Create — ALWAYS store the handle
FTimerHandle Handle = System::SetTimer(UObject Target, FName FunctionName, float Time, bool bLoop);

// Clear — use handle-based (preferred)
System::ClearAndInvalidateTimerHandle(Handle);
```

### Destroyed() - IS Available
```angelscript
UFUNCTION(BlueprintOverride)
void Destroyed()
{
	System::ClearAndInvalidateTimerHandle(LifeSpanTimerHandle);
}
```

## Compilation Verification (MANDATORY)

After writing or modifying any `.as` file, you MUST verify compilation by checking the Unreal Editor log:

```bash
grep "Angelscript: Error\|Angelscript: Warning" "Saved/Logs/{ProjectName}.log" | tail -20
```

- **Errors** = compilation failed, code must be fixed before proceeding
- **Warnings** = code compiles but has issues that should be addressed (e.g., ambiguous property names)
- If no errors/warnings appear after the latest timestamp, compilation succeeded

**Do NOT assume code compiles.** The AngelScript runtime in Unreal Engine may not expose all C++ APIs. Always verify.

## Enhanced Input in AngelScript — Known Limitations

**CRITICAL**: The Enhanced Input C++ API (`UEnhancedInputComponent::BindAction(UInputAction, ETriggerEvent, ...)`) is **NOT exposed** to AngelScript in standard UE builds. Do NOT attempt to bind Enhanced Input actions from AngelScript code.

### What Does NOT Work
```angelscript
// ❌ NONE of these compile in standard AngelScript builds:
EnhancedInput.BindAction(MoveAction, ETriggerEvent::Triggered, Delegate);
ActionValue.Axis2D;
ActionValue.GetAxis2D();
Subsystem.AddMappingContext(Context, 0, FModifyContextOptions());
```

### Correct Pattern: Blueprint-Bound Input
Expose `UFUNCTION()` methods on the character/pawn that Blueprint Input Action nodes call directly:

```angelscript
// Character exposes input methods for Blueprint to call
UFUNCTION()
void DoMove(FVector2D InputDir)
{
	MoveInput = InputDir;
}

UFUNCTION()
void DoLook(FVector2D InputDir)
{
	LookInput = InputDir;
}
```

Then in Blueprint: Create Enhanced Input Actions (IA_Move, IA_Look) and bind them to these UFUNCTION methods.

## Name Shadowing — Properties, Accessors, and Local Variables

AngelScript warns when any name (UPROPERTY, local variable, parameter) shadows a parent class property or accessor. This applies to **all** name scopes, not just UPROPERTY fields.

### UPROPERTY Shadowing Parent Accessors
```angelscript
// ❌ WRONG - UMovementComponent has GetMaxSpeed(), so naming a property MaxSpeed
// causes "ambiguous read" warnings
UPROPERTY(EditAnywhere, Category = "Movement")
float MaxSpeed = 1200.f;  // Conflicts with inherited GetMaxSpeed()

// ✅ CORRECT - Use a distinct name
UPROPERTY(EditAnywhere, Category = "Movement")
float TopSpeed = 1200.f;  // No conflict
```

### Local Variables Shadowing Parent Properties
```angelscript
// ❌ WRONG - AController has a ControlledPawn property;
// a local variable with the same name causes a shadow warning
APawn ControlledPawn = GetControlledPawn();

// ✅ CORRECT - Use a distinct local name, keep the accessor as-is
APawn MyPawn = GetControlledPawn();
```

### How to Avoid
- Before naming a UPROPERTY, local variable, or parameter, consider whether the parent class already has a property or `Get___()` accessor with that name
- Use descriptive prefixes or alternative names: `MyPawn`, `OwnerPawn`, `TargetActor`, `TopSpeed`
- Common parent names to avoid shadowing: `MaxSpeed`, `Velocity`, `Location`, `Rotation`, `ControlledPawn`, `PlayerState`, `InputComponent`

## Personal Knowledge Base

When answering AngelScript style questions, check if a personal wiki exists at `F:/AI/liang-wiki/`.
If it does, scan `wiki/index.md` for entries tagged `gamedev` or containing AngelScript-related
keywords (angelscript, style, scripting). Read relevant pages for personal project
context, gotchas, and coding conventions.
SKILL.md knowledge is primary; wiki adds personal context on top.
If the wiki has no relevant content, proceed with built-in knowledge only.
