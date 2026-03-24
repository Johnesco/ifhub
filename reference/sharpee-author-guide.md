# Sharpee Author Guide

Reference from sharpee.net/docs/author-guide/ (2026-03-23) + Family Zoo tutorial from engine fork (2026-03-24).

**Primary source**: Family Zoo tutorial at `/c/code/fork/sharpee/tutorials/familyzoo/` — 16 progressive versions with complete source + transcript tests.


---

## Creating Stories

### Minimal Story Requirements

A basic Sharpee story needs: `package.json` with `@sharpee/sharpee` dependency, a Story class implementing the `Story` interface, and at least one room + player.

### Story Interface

**Required methods:**

- `createPlayer(world: WorldModel): IFEntity` — instantiate player with `ActorTrait({ isPlayer: true })` and `IdentityTrait`
- `initializeWorld(world: WorldModel): void` — create all rooms, objects, NPCs; place player via `world.moveEntity()`

**Optional methods:**

- `extendParser(parser)` — custom grammar patterns
- `extendLanguage(language)` — story-specific messages
- `getCustomActions()` — return action implementations
- `onEngineReady(engine)` — register behaviors and daemons

### Project Structure

- **Small:** single `src/index.ts`
- **Medium:** `src/regions/` for rooms/objects, separate NPC folders
- **Large:** separate directories for regions, NPCs, actions, grammar, messages, handlers, traits

Regions are single files, not nested directories.

### Region Pattern

```typescript
export interface ForestRooms {
  clearing: IFEntity;
  path: IFEntity;
  grove: IFEntity;
}

export function createForest(world: WorldModel): ForestRooms {
  // Create rooms, set exits, add objects
  return { clearing, path, grove };
}
```

Cross-region connections wired in `initializeWorld()`.

---

## Objects & Traits

Sharpee uses **composition over inheritance**. Objects gain capabilities by adding traits.

### Creating Items

```typescript
// Portable item
const key = world.createEntity('key', EntityType.ITEM);
key.add(new IdentityTrait({
  name: 'brass key',
  description: 'A small brass key with an ornate handle.',
  aliases: ['key', 'brass key'],
}));
world.moveEntity(key.id, room.id);

// Scenery (non-portable)
const fountain = world.createEntity('fountain', EntityType.SCENERY);
fountain.add(new IdentityTrait({ name: 'marble fountain', description: '...' }));
fountain.add(new SceneryTrait());
world.moveEntity(fountain.id, courtyard.id);
```

### Containers

```typescript
// Basic container
const chest = world.createEntity('chest', EntityType.CONTAINER);
chest.add(new IdentityTrait({ name: 'wooden chest', description: '...' }));
chest.add(new ContainerTrait({ capacity: { maxItems: 10 }, isTransparent: false }));
chest.add(new OpenableTrait({ isOpen: false }));

// Supporter (items ON top)
const table = world.createEntity('table', EntityType.SCENERY);
table.add(new IdentityTrait({ name: 'oak table' }));
table.add(new SupporterTrait({ capacity: 50 }));
table.add(new SceneryTrait());
```

### Locks & Keys

```typescript
// Create key first
const key = world.createEntity('key', EntityType.ITEM);
key.add(new IdentityTrait({ name: 'iron key' }));

// Create lockable door
const door = world.createEntity('door', EntityType.DOOR);
door.add(new IdentityTrait({ name: 'iron door' }));
door.add(new OpenableTrait({ isOpen: false }));
door.add(new LockableTrait({ isLocked: true, keyId: key.id }));
```

### Placing Items in Closed Containers (AuthorModel)

```typescript
import { AuthorModel } from '@sharpee/world-model';
const author = new AuthorModel(world.getDataStore(), world);
author.moveEntity(gem.id, closedChest.id);  // Bypasses validation
```

Use AuthorModel for: setup of closed containers, special mechanics (magic/teleportation), tests.

### All Available Traits

| Trait | Purpose | Key Properties |
|-------|---------|----------------|
| `IdentityTrait` | Name and description | name, aliases, description |
| `SceneryTrait` | Fixed in place | — |
| `ContainerTrait` | Holds items inside | capacity, isTransparent |
| `SupporterTrait` | Items placed on top | capacity |
| `OpenableTrait` | Can open/close | isOpen |
| `LockableTrait` | Can lock/unlock | isLocked, keyId |
| `SwitchableTrait` | On/off toggle | isOn |
| `LightSourceTrait` | Provides illumination | brightness, requiresOn |
| `ReadableTrait` | Has text to read | text |
| `EdibleTrait` | Can be eaten | nutrition, consumedOnEat |
| `WearableTrait` | Can be worn | isWorn |
| `DoorTrait` | Connects rooms | — |
| `ClimbableTrait` | Can climb on | — |
| `PushableTrait` | Can be pushed | — |
| `PullableTrait` | Can be pulled | — |
| `BreakableTrait` | Can be broken | isBroken |
| `EnterableTrait` | Can enter (vehicle, bed) | — |
| `WeaponTrait` | Combat weapon | damage, weaponType |
| `CombatantTrait` | Can fight | health, skill, hostile |
| `NpcTrait` | Non-player character | isAlive, isConscious |
| `AttachedTrait` | Attached to something | attachedTo |
| `ButtonTrait` | Pressable button | — |

### Checking Traits

```typescript
const container = entity.get(ContainerTrait);
if (container) {
  console.log('Capacity:', container.capacity);
}
```

---

## Rooms & Connections

### Room Creation

```typescript
const kitchen = world.createEntity('kitchen', EntityType.ROOM);
kitchen.add(new RoomTrait({ exits: {}, isDark: false }));
kitchen.add(new IdentityTrait({
  name: 'Kitchen',
  description: 'A small kitchen with copper pots.',
  properName: true,
}));
```

### Connecting Rooms

```typescript
// Direct exit assignment
kitchen.get(RoomTrait)!.exits[Direction.NORTH] = { destination: diningRoom.id };
diningRoom.get(RoomTrait)!.exits[Direction.SOUTH] = { destination: kitchen.id };
```

Directions: NORTH, SOUTH, EAST, WEST, UP, DOWN, IN, OUT, NORTHEAST, NORTHWEST, SOUTHEAST, SOUTHWEST.

### Doors & Locked Passages

```typescript
const door = world.createEntity('oak-door', EntityType.DOOR);
door.add(new IdentityTrait({ name: 'oak door', description: '...' }));
door.add(new OpenableTrait({ isOpen: false }));
door.add(new DoorTrait());
world.moveEntity(door.id, hallway.id);

// Connect through door — must open door first
hallway.get(RoomTrait)!.exits[Direction.NORTH] = {
  destination: study.id,
  via: door.id,
};
```

### One-Way Exits

```typescript
setExits(cliffTop, { [Direction.DOWN]: ravine.id });
// Don't add UP exit from ravine
```

---

## NPCs

### Core Components

1. Entity with `NpcTrait`, `ActorTrait`, optional `CombatantTrait`
2. Behavior implementing `NpcBehavior` interface
3. Message IDs resolved through language layer

### Entity Creation

```typescript
const npc = world.createEntity('id', EntityType.ACTOR);
npc.add(new IdentityTrait({...}));
npc.add(new ActorTrait({ isPlayer: false }));
npc.add(new NpcTrait({ behaviorId: 'behavior-id', isHostile: false, canMove: true }));
```

### Built-in Behaviors

- **Guard** — stationary, hostile, blocks passage
- **Wanderer** — moves randomly between rooms
- **Follower** — tracks player movement
- **Patrol** — fixed route, loop/pause options

### Custom Behavior Interface

```typescript
onTurn(context: NpcContext): NpcAction[]
onPlayerEnters(context: NpcContext): NpcAction[]
onSpokenTo(context: NpcContext, words: string): NpcAction[]
onAttacked(context: NpcContext, attacker): NpcAction[]
```

### Registration

```typescript
const npcPlugin = engine.getPluginRegistry().get('sharpee.plugin.npc');
const npcService = npcPlugin.getNpcService();
npcService.registerBehavior(behavior);
```

---

## Testing

### Transcript Format

```
title: Door Puzzle Test
story: my-story
description: Tests locked door requiring brass key
---
> look
[OK: contains "a locked door"]
> unlock door with brass key
[OK: contains "unlocked"]
```

### Assertions

| Assertion | Function |
|-----------|----------|
| `[OK: contains "text"]` | Output includes substring |
| `[OK: not contains "text"]` | Output excludes substring |
| `[OK: contains_any "a" "b"]` | At least one present |
| `[OK: matches /pattern/flags]` | Regex match |
| `[SKIP]` | Skip this command |
| `[TODO: reason]` | Mark unfinished |

### Event Assertions

```
[EVENT: true, type="if.event.taken"]
[EVENTS: 3]
```

### State Assertions

```
[STATE: true, egg.location = player]
[STATE: true, player.inventory contains lantern]
```

### Control Flow

- `[GOAL: name] / [REQUIRES:] / [ENSURES:] / [END GOAL]`
- `[IF: condition] / [END IF]`
- `[WHILE: condition] / [END WHILE]`
- `[DO] / [UNTIL "text"]`
- `[RETRY: max=N] / [END RETRY]`
- `[NAVIGATE TO: "Room Name"]`

### Save/Restore

```
$save wt-01
$restore wt-01
```

### Test Commands

```
$teleport kitchen
$take egg
$kill troll
$immortal / $mortal
```

### Running Tests

```bash
npx sharpee build --test
node {story}-test.js --test tests/transcripts/*.transcript
node {story}-test.js --test --chain walkthroughs/wt-*.transcript
```

### Project Layout

```
walkthroughs/wt-*.transcript    # Chained walkthroughs
tests/transcripts/*.transcript  # Isolated unit tests
saves/*.json                    # Auto-generated checkpoints
```

---

## Family Zoo Tutorial (Progressive Reference)

The canonical Sharpee tutorial at `/c/code/fork/sharpee/tutorials/familyzoo/`. Each version is a self-contained `.ts` file with matching transcript tests.

| V | Concept | Key API | File |
|---|---------|---------|------|
| 1 | Single Room | `Story`, `WorldModel`, `RoomTrait` | `src/v01.ts` |
| 2 | Navigation | `Direction`, `RoomTrait.exits` | `src/v02.ts` |
| 3 | Scenery | `SceneryTrait` | `src/v03.ts` |
| 4 | Portables | `EntityType.ITEM` | `src/v04.ts` |
| 5 | Containers | `ContainerTrait`, `SupporterTrait` | `src/v05.ts` |
| 6 | Openable | `OpenableTrait` | `src/v06.ts` |
| **7** | **Locked Doors** | **`LockableTrait.keyId`, `DoorTrait`, `via`** | **`src/v07.ts`** |
| 8 | Light/Dark | `LightSourceTrait`, `isDark: true` | `src/v08.ts` |
| 9 | Readable | `ReadableTrait` | `src/v09.ts` |
| 10 | Switchable | `SwitchableTrait` | `src/v10.ts` |
| 11 | NPCs | `NpcPlugin`, `NpcTrait`, `NpcBehavior` | `src/v11.ts` |
| 12 | Events | `world.chainEvent()` | `src/v12.ts` |
| 13 | Custom Actions | `Action`, `extendParser()`, grammar | `src/v13.ts` |
| 14 | Capabilities | `registerCapabilityBehavior()` | `src/v14.ts` |
| 15 | Timed Events | `SchedulerPlugin`, daemons, fuses | `src/v15.ts` |
| 16 | Scoring | `world.awardScore()`, `setMaxScore()` | `src/v16.ts` |

### V7 Locked Door Pattern (Reference Implementation)

```typescript
// 1. Create key first (need its ID for the lock)
const keycard = world.createEntity('staff keycard', EntityType.ITEM);
keycard.add(new IdentityTrait({ name: 'staff keycard', aliases: ['keycard', 'key card', 'card', 'key'] }));
world.moveEntity(keycard.id, entrance.id);

// 2. Create door entity with all five traits
const staffGate = world.createEntity('staff gate', EntityType.DOOR);
staffGate.add(new IdentityTrait({ name: 'staff gate', aliases: ['gate', 'staff gate'] }));
staffGate.add(new DoorTrait({ room1: mainPath.id, room2: supplyRoom.id, bidirectional: true }));
staffGate.add(new OpenableTrait({ isOpen: false }));
staffGate.add(new LockableTrait({ isLocked: true, keyId: keycard.id }));
staffGate.add(new SceneryTrait());
world.moveEntity(staffGate.id, mainPath.id);

// 3. Wire exits with `via` — going action checks door state
mainPath.get(RoomTrait)!.exits = {
  [Direction.SOUTH]: { destination: supplyRoom.id, via: staffGate.id },
};
supplyRoom.get(RoomTrait)!.exits = {
  [Direction.NORTH]: { destination: mainPath.id, via: staffGate.id },
};
```

**Player sequence**: `take keycard` → `unlock gate with keycard` → `open gate` → `south`

**Common mistakes**:
- Forgetting `via: gate.id` in exits — player walks through without checking door state
- Creating door before key — need key's entity ID for `LockableTrait.keyId`
- Missing `DoorTrait` — door won't be recognized as a room connection
- Missing `.instrument('key')` in grammar — engine bug fixed in commit `29d6943e` (2026-03-23)

### Key Principles from Tutorial

- **Keys are just items** — no special trait needed. The lock decides what fits via `keyId`.
- **`via` is what makes doors work** — without it, exits are unconditional.
- **Three-step unlock**: find key → unlock → open. Realistic and creates natural puzzles.
- **AuthorModel** bypasses validation for setup (placing items in closed containers).
- **Capability dispatch** (V14) — same verb, different behavior per entity via traits.
- **Event chains** (V12) — `world.chainEvent()` for puzzle logic reacting to actions.
- **Score IDs are idempotent** — `world.awardScore('unique-id', points, description)` prevents double-scoring.
