# Class / Struct Layout — Canonical Template & Reference

Companion to `SKILL.md` §4. Contains the full canonical UCLASS template, the marker-block edge cases, and the public-vs-protected base-class virtuals reference. Consult when starting a new class or when the inline §4 rules need a concrete example.

---

## Canonical UCLASS Template

Section order is fixed. This is the master template every new UCLASS should mirror:

```cpp
UCLASS(ClassGroup=(S1), meta=(BlueprintSpawnableComponent))
class S1_API US1MyComponent : public UActorComponent
{
	GENERATED_BODY()

	friend class UFriendClass;       // friend declarations before any access specifier

public:
	US1MyComponent();

public:
	//~ Begin UActorComponent Interfaces
	virtual void BeginPlay() override;
	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;
	//~ End UActorComponent Interfaces

public:
	/** Public API callable from Blueprints. */
	UFUNCTION(BlueprintCallable, Category = "MyComp")
	void Activate();

protected:
	void InternalUpdate(float DeltaTime);

protected:
	// BlueprintAssignable delegates first, then config UPROPERTYs
	UPROPERTY(BlueprintAssignable, Category = "MyComp|Event")
	FMyDelegate OnSomethingHappened;

	UPROPERTY(EditAnywhere, Category = "MyComp")
	bool bIsAutoStart = true;

private:
	bool bIsRegistered = false;
	int32 CurrentIndex = 0;

#if WITH_EDITORONLY_DATA
protected:
	void DebugDraw() const;
#endif
};
```

---

## Override Marker Blocks — Multi-Base / `#if WITH_EDITOR` Edge Case

When an override group is split by `#if WITH_EDITOR`, repeat the marker pair on each side even when the contract is the same:

```cpp
// CORRECT — defining base named, plural form, repeated marker around #if WITH_EDITOR split
public:
	//~ Begin UFlowNodeBase Interfaces
	virtual void ExecuteInput(const FName& PinName) override;
	//~ End UFlowNodeBase Interfaces

#if WITH_EDITOR
public:
	//~ Begin UFlowNodeBase Interfaces                          // same contract, second marker block
	virtual FString GetNodeDescription() const override;        // because #if WITH_EDITOR splits the group
	//~ End UFlowNodeBase Interfaces
#endif
```

Multi-interface classes (`: public UActorComponent, public IGameplayTagAssetInterface`) write two separate marker blocks, one per defining base.

---

## Common UE Base-Class Virtuals — Public vs Protected

Override visibility must mirror the base. Demoting `public virtual` to `protected` is a Liskov violation and Rider/ReSharper flags it explicitly. When in doubt, open the base header — never guess; the defining base may be several levels up.

### Public (most engine virtuals — override stays `public:`)

- `AActor::Tick`
- `UActorComponent::BeginPlay` / `EndPlay` / `TickComponent` / `OnRegister` / `OnUnregister` / `InitializeComponent`
- `UObject::PostInitProperties` / `BeginDestroy` / `Serialize` / `PostEditChangeProperty` / `PreEditChange`
- `FTickableGameObject::Tick` / `GetStatId` / `IsTickable` / `IsAllowedToTick`
- `UGameInstance::Init` / `Shutdown`

### Protected (engine-internal entry points — override stays `protected:`)

- `APlayerController::SetupInputComponent` / `PlayerTick`
- `APawn::SetupPlayerInputComponent`
- `AActor::BeginPlay` / `EndPlay`
- `UUserWidget::NativeConstruct` / `NativeDestruct` / `NativeTick`

These are protected by design — gameplay code is meant to call public APIs (`EnableInput`, `Possess`, etc.) rather than the input-setup hooks directly. Placing them in `public:` is gratuitous API exposure.
