# UE C++ Code-Block Style Contract

> Distilled from the `liang-ue-cpp-style` skill (`~/.claude/skills/liang-ue-cpp-style/SKILL.md`).
> That skill is the source of truth and wins on any conflict — update both files together.
>
> Applies to EVERY code block that is Unreal Engine C++ — detected by UCLASS / USTRUCT /
> UPROPERTY / UFUNCTION macros, `*.generated.h` includes, or file paths under `Source/`.
> Applies in every UE project; no per-project opt-in.

## 1. Allman braces — mandatory, no single-line control flow

Opening brace on its own line. Never collapse `if` / `for` / `while` / `case` / function
bodies onto one line.

```cpp
// WRONG
case ESoESkillCategory::Attack: return LOCTEXT("CatAttack", "Attack");
if (bEnabled) { OnClicked.Broadcast(Category); }

// RIGHT
case ESoESkillCategory::Attack:
	return LOCTEXT("CatAttack", "Attack");

if (bEnabled)
{
	OnClicked.Broadcast(Category);
}
```

Two exceptions only: aggregate initialization (`State = FMyState{};`) and trivial inline
getters in headers (`bool IsEnabled() const { return bIsEnabled; }` — single return
statement, no side effects).

## 2. UPROPERTY / UFUNCTION macro on its own line

The macro line and the declaration are ALWAYS two lines. No inner spaces inside macro parens.

```cpp
// WRONG
UPROPERTY(meta = (BindWidget)) TObjectPtr<UMyWidget> TabAttack;

// RIGHT
UPROPERTY(meta = (BindWidget))
TObjectPtr<UMyWidget> TabAttack;
```

## 3. Class layout — all functions first, then data

Fixed section order, repeating the access specifier per logical group (the repeated
specifier is the section label; a blank line is the section break):

1. `public:` — constructor
2. `public:` — overrides, wrapped in `//~ Begin <DefiningBase> Interfaces` /
   `//~ End <DefiningBase> Interfaces` markers. Name the base that DECLARES the virtual
   (not the immediate parent); plural "Interfaces" even for a single override.
3. `public:` — public API (`UFUNCTION`s, entry points)
4. `protected:` / `private:` — internal helper FUNCTIONS (incl. `BlueprintImplementableEvent`s)
5. `public:` or `protected:` — UPROPERTY data + delegate members (`public` for data-carrier
   classes like DataAssets/Flow nodes; `protected` for actors/components/subsystems)
6. `private:` — non-UPROPERTY runtime state
7. `#if WITH_EDITOR` / `#if WITH_EDITORONLY_DATA` blocks LAST

Data members NEVER sit above function declarations.

## 4. Everything else that recurs in snippets

- Tabs for indentation, never spaces.
- In-class initializers on every field, UPROPERTY or not (`bool bEnabled = true;` —
  UE does not zero non-UPROPERTY fields).
- .h: forward-declare instead of including; `*.generated.h` is ALWAYS the last include.
- .cpp: own header first (no blank line before it), then engine headers, then project headers.
- Constructors always in the .cpp, never inline in the header.
- Early-return guards at the top of functions; actual logic flat, no deep nesting.
- `#define LOCTEXT_NAMESPACE "..."` / `#undef LOCTEXT_NAMESPACE` pairs around user-facing `FText`.
