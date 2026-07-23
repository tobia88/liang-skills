# Rename Hazards

Reference for the recon and rename passes (Execution Flow steps 2–4). The
governing rule:

> **A rename is safe only when every reference site is found and updated in
> the same changeset. Anything less: skip the rename and report it.**

The danger is names that live outside the compiler's sight — serialized data,
scene files, string lookups, reflection. These break silently: the project
still builds, and the failure surfaces at runtime or as quietly reset data.

## Search checklist (before any rename)

For each candidate identifier, search project-wide (not just the target file)
for:

1. The exact identifier in code (callers, overrides, signal connections)
2. The identifier as a **string literal** (dynamic lookups, key names)
3. The identifier inside **asset/config files** (scenes, prefabs, INI, JSON, YAML)
4. Case-variant and separator-variant forms where the ecosystem converts names
   (e.g. `snake_case` properties surfaced as `Capitalized Words` in editors)

If step 2 or 3 hits and the consumer cannot be updated in the same changeset,
the rename is blocked.

## Godot

- **Exported variables** (`@export`) are serialized by name into `.tscn`/`.tres`
  files. Renaming one silently resets every scene's tuned value to the default.
  Update all scene files in the same changeset, or skip.
- **Node names and paths:** `$"Child"`, `get_node("Path/To/Node")`, and
  `NodePath` exports all reference scene-tree names as strings.
- **Input actions:** `Input.is_action_pressed("move_left")` — action names live
  in `project.godot`. Renaming the string breaks input without any error.
- **Signals connected in scenes:** `.tscn` `[connection]` blocks name both the
  signal and the method. Renaming a connected method breaks the connection.
- **`class_name`** registrations are referenced by other scripts and scenes.
- **Script file renames:** each script pairs with a `.uid` file; move both
  together, or the editor regenerates references.
- **Autoload names** are project-wide identifiers set in `project.godot`.
- **Callables by StringName:** `call("method")`, `has_method`, `Callable(self, "m")`.

## Unity / C#

- **Serialized fields** (`public` or `[SerializeField]`) are stored by name in
  scenes and prefabs. Rename only with `[FormerlySerializedAs("oldName")]`
  left in place, or data silently resets.
- **String-based invocation:** `Invoke("MethodName")`, `SendMessage`,
  `StartCoroutine("Name")`, animation events, UnityEvent bindings in the
  Inspector.
- **Shader property names** referenced via `Shader.PropertyToID("_Name")`.

## Unreal

- **`UPROPERTY` names** are serialized into assets; renames need a core
  redirect entry (`[CoreRedirects]` in the project ini) shipped in the same
  change.
- **Blueprint references** to C++ functions, properties, and classes bind by
  name; renaming C++ without redirects breaks every referencing Blueprint.
- **Delegate/timer bindings by FName:** `BindUFunction`, `SetTimer` with
  function names.

## Dynamic languages and data boundaries

- **Reflection and dynamic access:** `getattr`/`setattr`, `obj["name"]`,
  `__getattr__`, decorators that register by function name.
- **Serialization keys:** JSON/YAML field names, ORM column mappings, protobuf
  field names, API payload shapes — renaming the code-side name changes the
  wire/storage format unless a mapping pins the old key.
- **Public API surface:** anything importable by code outside the project is a
  contract; renames are breaking changes, not cleanup, and belong in findings.
- **FFI and embedded scripts:** names referenced from another language
  (C headers, Lua/Python embedded in a host) will not appear in a same-language
  search — check the boundary explicitly.

## Safe by default

Locals, private helpers, function parameters, and file-scope constants with no
string-literal or asset hits in the search checklist. These are the bread and
butter of rename-for-truth — verify with the checklist once, then rename
freely.
