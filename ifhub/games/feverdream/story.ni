"Fever Dream" by Anonymous

The story headline is "A Perceptual Horror".
The story genre is "Horror".
The story description is "Three items alter your perception. The world stays the same. You do not."

Use brief room descriptions.

Part 1 - Configuration and Global State

Chapter 1 - Perceptual States

A thing can be perception-hidden. A thing is usually not perception-hidden.

The fungus-consumed is a truth state that varies. The fungus-consumed is false.

The spray-active is a truth state that varies. The spray-active is false.

The cistern-drained is a truth state that varies. The cistern-drained is false.

Chapter 2 - Regions

The Ward is a region.
The Basement is a region.
The Depths is a region.

Chapter 3 - Status Line and Opening

When play begins:
	now the left hand status line is "[the player's surroundings]";
	now the right hand status line is "".

After printing the banner text:
	say "[paragraph break]You wake on a cold floor. Your head aches. You do not remember arriving.[paragraph break]The air smells of iodine and old paper.[paragraph break]"

Part 2 - The Ward

Chapter 1 - The Receiving Room

The Receiving Room is a room. The Receiving Room is in the Ward. "Fluorescent tubes buzz overhead, one of them flickering at the edge of failure. A long counter divides the room -- scuffed linoleum on your side, dark wood on the other. The only door leads east, into a corridor.[if the player is wearing the spectacles][paragraph break]Under the counter, scratched into the linoleum in letters too small for the naked eye: THEY BUILT DOWN BEFORE THEY BUILT UP.[end if]"

The player is in the Receiving Room.

The fluorescent tubes are scenery in the Receiving Room.

The long counter is scenery in the Receiving Room.

The intake form is on the long counter. "A yellowed form lies on the counter."

The spectacles are on the long counter. "A pair of wire-rimmed spectacles sits beside the form." The spectacles are wearable.

Instead of taking the intake form:
	say "The paper crumbles at the edges when you touch it. Better to leave it where it is."

Section - Receiving Room Descriptions

The description of the fluorescent tubes is "Long glass cylinders behind a yellowed plastic panel. One flickers in a pattern that almost repeats but never quite does."

The description of the long counter is "Chest-high, laminated in something that might once have been wood-grain. A deep gouge runs its full length, as though someone dragged something heavy across it."

The description of the intake form is "A pre-printed form on brittle paper. Your name is at the top, in handwriting you do not recognise. Below it, in the same hand: [italic type]Patient exhibits reduced perception. Corrective lenses issued[roman type]."

The description of the spectacles is "Wire-rimmed, with thick lenses that distort the light when you tilt them. The prescription label inside the arm reads your name."

Section - Receiving Room Vocabulary

Understand "lights" and "light" and "tube" and "fluorescent" and "panel" as the fluorescent tubes.
Understand "counter" and "gouge" and "desk" as the long counter.
Understand "form" and "document" as the intake form.
Understand "glasses" and "lenses" and "spectacle" as the spectacles.

Chapter 2 - The Corridor

The Corridor is a room. The Corridor is in the Ward. It is east of the Receiving Room. "A long hallway tiled in white, though several tiles have cracked and not been replaced. The gaps show raw concrete beneath. The Receiving Room lies west. East, a treatment room door stands ajar.[if the player is wearing the spectacles][paragraph break]Between the cracked tiles, a seam runs the width of the floor -- too straight to be structural damage. It outlines a trapdoor. A recessed handle sits flush with the tile.[end if][if fungus-consumed is true][paragraph break]The tiles pulse faintly, expanding and contracting like something breathing. The cracks between them are veins. The hallway is a throat and you are inside it.[end if]"

The white tiles are scenery in the Corridor.

The hidden trapdoor is a door. The hidden trapdoor is perception-hidden. The hidden trapdoor is below the Corridor and above the Stairwell. The hidden trapdoor is open. The hidden trapdoor is not openable. The hidden trapdoor is scenery.

Instead of opening the hidden trapdoor:
	say "It is already open -- propped against the wall where the hinge holds it."

Instead of closing the hidden trapdoor:
	say "You would rather not seal yourself away from the only way back up."

Section - Corridor Descriptions

The description of the white tiles is "[if fungus-consumed is true]They breathe. You are certain of this now. Each tile swells slightly on the inhale and settles on the exhale. The grout between them is wet and warm.[otherwise]Standard institutional ceramic. Most are intact. The cracked ones reveal grey concrete underneath -- poured, not mortared.[end if]"

The description of the hidden trapdoor is "A section of floor cut to look like tiles, but the seam gives it away. A recessed handle allows you to pull it up."

Section - Corridor Vocabulary

Understand "tiles" and "tile" and "cracks" and "crack" and "floor" as the white tiles.
Understand "trapdoor" and "trap door" and "seam" and "recessed handle" as the hidden trapdoor.

Chapter 3 - The Treatment Room

The Treatment Room is a room. The Treatment Room is in the Ward. It is east of the Corridor. "A reclining chair dominates the room, bolted to the floor and surrounded by a ring of drainage channels. Instrument trays line the east wall, empty. A faded note has been pinned to the wall above them.[paragraph break]The corridor is back to the west."

The reclining chair is an enterable scenery supporter in the Treatment Room.

Instead of entering the reclining chair:
	say "You lower yourself into it. The leather is cold and gives slightly, like skin. You get back up."

The instrument trays are scenery in the Treatment Room.

The faded note is scenery in the Treatment Room.

Instead of taking the faded note:
	say "It is pinned firmly to the wall. The pin has been driven in deep."

Section - Treatment Room Descriptions

The description of the reclining chair is "Padded in cracked leather, tilted fifteen degrees back. The armrests have restraint loops, unbuckled. The drainage channels around its base are dry but stained."

The description of the instrument trays is "Stainless steel, arranged in a precise row. Each tray has a label etched into its rim -- EXTRACTION, CALIBRATION, REFINEMENT -- but all are empty."

The description of the faded note is "Typewritten, the ink barely legible:[paragraph break][italic type]Re: access to the lower level. What you cannot see is still there. The corrective lenses are not optional. They are the first step[roman type]."

Section - Treatment Room Vocabulary

Understand "chair" and "leather" and "restraint" and "restraints" and "armrest" and "armrests" and "loops" as the reclining chair.
Understand "sit on/in [something]" as entering.
Understand "sit" as entering.
Understand "trays" and "tray" and "instruments" as the instrument trays.
Understand "note" as the faded note.

Part 3 - The Basement

Chapter 1 - The Stairwell

The Stairwell is a room. The Stairwell is in the Basement. "Concrete steps descend to a landing where the air turns cold and damp. Pipes run along the ceiling, sweating condensation. The trapdoor above opens back to the corridor. A passage continues south into a laboratory.[if the player is wearing the spectacles][paragraph break]Scratched into the underside of one pipe, visible only from this angle: a row of tally marks. You count thirty-seven.[end if]"

The sweating pipes are scenery in the Stairwell.

The pipe wrench is in the Stairwell. "A pipe wrench lies on the bottom step, half-hidden by shadow."

Section - Stairwell Descriptions

The description of the sweating pipes is "Copper and iron, bundled together with wire. Droplets of condensation bead along their surfaces and fall at irregular intervals."

The description of the pipe wrench is "Heavy steel, the jaw rusted half-open. It still works. Someone left it here in a hurry -- the handle is dented where it was dropped."

Section - Stairwell Vocabulary

Understand "pipes" and "pipe" and "copper" and "condensation" and "ceiling" as the sweating pipes.
Understand "wrench" and "tool" as the pipe wrench.

Chapter 2 - The Laboratory

The Laboratory is a room. The Laboratory is in the Basement. It is south of the Stairwell. "A long room lined with workbenches and glass-fronted cabinets. Everything is labelled. Everything is in order. The labels are handwritten in the same careful script as the intake form upstairs. A passage leads north to the stairwell. East, a heavy door opens into cold storage.[if the player is wearing the spectacles][paragraph break]One of the glass cases, mounted on the far wall, holds something you missed before: a brass key, suspended on a wire inside the glass.[end if]"

The workbenches are scenery in the Laboratory.

The lab plaque is scenery in the Laboratory.

The glass case is scenery in the Laboratory. The glass case is perception-hidden.

Instead of attacking the glass case:
	if the player carries the pipe wrench:
		say "You swing the wrench. The glass shatters cleanly. The brass key drops into your hand.";
		now the brass key is carried by the player;
		now the description of the glass case is "A shattered display case. Glass fragments cling to the frame.";
	otherwise:
		say "You rap your knuckles against it. Thin, but you cannot break it with your bare hands. You need something heavy."

Instead of taking the glass case:
	say "It is bolted to the wall."

The brass key is a thing. The brass key is perception-hidden.

Understand "break [something]" as attacking.

Section - Laboratory Descriptions

The description of the workbenches is "Slate-topped, scored with knife marks and chemical burns. Each bench has a numbered brass plate screwed to its front edge. The numbers run from one to twelve, but benches seven through ten are missing."

The description of the lab plaque is "A brass plaque mounted beside the door to cold storage. It reads:[paragraph break][italic type]CISTERN MAINTENANCE[line break]Valve operation: LEFT drains. RIGHT floods.[line break]Do not operate without authorization[roman type]."

The description of the glass case is "A small display case mounted on the wall, sealed shut. Inside, a brass key hangs from a wire. The glass is thin -- it would break under any real force."

The description of the brass key is "Small, ornate, warm to the touch even in this cold air. The bow is stamped with a snowflake -- the same symbol on the cold storage cabinet."

Section - Laboratory Vocabulary

Understand "bench" and "benches" and "workbench" and "slate" as the workbenches.
Understand "plaque" and "brass plaque" as the lab plaque.
Understand "case" and "display case" and "display" as the glass case.
Understand "key" and "brass" and "ornate key" as the brass key.

Chapter 3 - Cold Storage

Cold Storage is a room. Cold Storage is in the Basement. It is east of the Laboratory. "The temperature drops the moment you cross the threshold. Your breath fogs. Racks of specimen jars line the walls, their contents suspended in amber fluid. A heavy metal cabinet stands against the far wall, marked with a snowflake symbol.[paragraph break]The laboratory is back to the west.[if the player is wearing the spectacles][paragraph break]The amber fluid in the jars is moving. Not flowing -- twitching, as if the things inside are not entirely preserved.[end if]"

The specimen jars are scenery in Cold Storage.

The metal cabinet is a container in Cold Storage. The metal cabinet is closed, locked and openable. The matching key of the metal cabinet is the brass key.
The initial appearance of the metal cabinet is "[if the metal cabinet is locked]A heavy metal cabinet stands against the far wall, locked tight.[otherwise if the metal cabinet is open]The metal cabinet stands open.[otherwise]The metal cabinet stands closed.[end if]"

Instead of attacking the metal cabinet:
	say "You strike it. The steel rings dully and your hand aches. It will not yield to force."

The glass dish is in the metal cabinet. The glass dish is fixed in place.

The grey fungus is in the metal cabinet. The grey fungus is edible.
The initial appearance of the grey fungus is "A clump of grey fungus sits in a glass dish."

Section - Cold Storage Descriptions

The description of the specimen jars is "Dozens of them, sealed with wax. The contents are dark shapes suspended in fluid -- organic, but beyond identification. Each jar has a patient number. None of the numbers match."

The description of the metal cabinet is "[if the metal cabinet is locked]A floor-standing steel cabinet with a snowflake embossed on its door. A keyhole sits below the handle. Locked.[otherwise if the metal cabinet is open]The cabinet stands open. Inside, a single shelf holds a glass dish.[otherwise]The cabinet is closed but unlocked.[end if]"

The description of the glass dish is "A shallow petri dish containing a mass of grey fungus. A label on the rim reads: [italic type]PERCEPTUAL AGENT -- STAGE 2 THERAPY. CONSUME FOR ACCESS TO LOWER LEVELS[roman type]."

The description of the grey fungus is "A dense, velvety mass the color of wet ash. It gives slightly under pressure, like bread dough. It smells of nothing at all."

Section - Cold Storage Vocabulary

Understand "jars" and "jar" and "specimens" and "specimen" and "fluid" and "amber" and "racks" and "rack" as the specimen jars.
Understand "cabinet" and "steel cabinet" and "locker" and "snowflake" as the metal cabinet.
Understand "dish" and "petri" and "petri dish" as the glass dish.
Understand "fungus" and "grey" and "mushroom" and "mold" and "mould" as the grey fungus.

Part 4 - The Below

Chapter 1 - The Cistern

The Cistern is a room. The Cistern is in the Depths. "[if cistern-drained is true][cistern-drained-desc][otherwise if spray-active is true][cistern-spray-desc][otherwise if fungus-consumed is true][cistern-fungus-desc][otherwise][cistern-normal-desc][end if]"

To say cistern-normal-desc:
	say "A circular chamber of old brick, half-filled with dark water. The walls are slick with mineral deposits. Pipes enter from above, some intact, some cracked and leaking. An iron valve protrudes from the north wall at chest height. A faded instructional sign hangs beside it.[paragraph break]The passage back up is to the west."

To say cistern-fungus-desc:
	say "The chamber is alive. The bricks are teeth in a circular jaw. The dark water below is a throat, swallowing and unswallowing in slow rhythm. The pipes overhead are arteries, pulsing with something that is not water.[paragraph break]An iron valve grows from the north wall like a bone spur. Beside it, a sign hangs from the flesh of the wall.[paragraph break]The passage back up is to the west."

To say cistern-spray-desc:
	say "Th3 chamb_r is al1ve. The brikcs are t33th in a circuler jaw. Th3 dark watr below is a thro@t, swllowing and unswll0wing.[paragraph break]An ir0n valv3 gros from the n0rth wall. Bes1de it, a s1gn.[paragraph break]The pa55age back up iz to th3 west."

To say cistern-drained-desc:
	say "The water is gone. Below the waterline, the bricks are coated in a pale slime that glistens under your light. The drain grate in the floor stands open, revealing a narrow passage descending further.[paragraph break]The passage back up is to the west."

The dark water is scenery in the Cistern.

The iron valve is scenery in the Cistern.

The instructional sign is scenery in the Cistern.

The drainage grate is scenery in the Cistern.

Section - Cistern Descriptions

The description of the dark water is "[if cistern-drained is true]Gone. A dark stain marks where the waterline was.[otherwise if spray-active is true]Drk watr. It movs but you c4nt tell which w@y.[otherwise if fungus-consumed is true]It moves, but you cannot tell which way. Something underneath displaces the surface in slow, deliberate patterns.[otherwise]Still and black. The surface reflects the pipes above in perfect detail, as though the water is a window into an inverted room.[end if]"

The description of the iron valve is "[if spray-active is true][one of]An ir0n valv3. It hs a handl you can trn.[or]Ir_n vlve. Th3 handl trns l3ft or r1ght.[or]V@lve. H4ndle. L3ft. R1ght.[at random][otherwise if fungus-consumed is true]A growth of iron, fused to the wall like coral. The handle is a joint that bends left or right.[otherwise]A cast-iron valve with a T-shaped handle. It turns left or right. A plaque beside it should explain which does what.[end if]"

The description of the instructional sign is "[if spray-active is true][one of]The l3tters sw1m. You c4n alm0st r3ad it. LEFT dr--ns? Or was 1t R1GHT?[or]Th3 s1gn s4ys s0meth1ng ab0ut the v4lve. The l3tters w0nt hold st1ll.[or]Y0u sq1nt. Th3 w0rds r3arrange th3mselves wh3n you bl1nk.[at random][otherwise if fungus-consumed is true]The sign is a flap of skin pinned to the wall with a thorn. The words are tattooed into it. They read the same as they always did -- valve directions, maintenance notes -- but the medium has changed.[otherwise]A laminated sign, institutional in tone:[paragraph break][italic type]CISTERN VALVE OPERATION[line break]LEFT: drains cistern to sublevel[line break]RIGHT: emergency flood (DO NOT OPERATE)[roman type].[end if]"

The description of the drainage grate is "[if cistern-drained is true]A circular iron grate, now standing open. Below it, a narrow passage descends into darkness.[otherwise]A heavy circular grate set into the floor, submerged under the dark water.[end if]"

Section - Cistern Vocabulary

Understand "water" and "pool" as the dark water.
Understand "valve" as the iron valve.
Understand "sign" and "instructions" and "instructional" as the instructional sign.
Understand "grate" and "drain" and "drainage" as the drainage grate.

Chapter 2 - The Source

The Source is a room. The Source is in the Depths. "[if spray-active is true][source-spray-desc][otherwise][source-fungus-desc][end if]"

To say source-fungus-desc:
	say "You descend through the grate into a space that should not exist beneath a building this size. The walls are not walls -- they are membranes, translucent and veined. Light comes from inside them, a slow amber pulse.[paragraph break]In the center of the chamber, a low stone basin holds something luminous. It is warm. It has been waiting."

To say source-spray-desc:
	say "Y0u desc3nd thr0ugh th3 gr4te 1nto a sp@ce th4t sh0uld n0t ex1st. The w4lls ar3 n0t w4lls -- th3y ar3 m3mbranes, tr@nsluc3nt and ve1ned. L1ght c0mes fr0m 1ns1de th3m.[paragraph break]In th3 c3nter, a l0w st0ne b@sin h0lds s0meth1ng lum1nous. 1t 1s w@rm."

The membrane walls are scenery in the Source.

The stone basin is scenery in the Source.

Instead of taking the stone basin:
	say "It is part of the floor. It has always been part of the floor."

Instead of touching the stone basin:
	end the story saying "You reach in. It reaches back."

Section - Source Descriptions

The description of the membrane walls is "[if spray-active is true]Th3y puls3. Y0u c@n s3e sh4pes m0ving b3h1nd th3m. Th3y ar3 n0t shad0ws.[otherwise]They pulse. You can see shapes moving behind them. They are not shadows.[end if]"

The description of the stone basin is "[if spray-active is true]A b@sin c@rved fr0m a s1ngle p1ece of st0ne. Ins1de, s0meth1ng gl0ws. 1t 1s n0t l1ght. It 1s att3ntion.[otherwise]A basin carved from a single piece of stone, older than anything else in this building. Inside, something glows. It is not light. It is attention.[end if]"

Section - Source Vocabulary

Understand "walls" and "wall" and "membrane" and "membranes" and "veins" and "veined" as the membrane walls.
Understand "basin" and "luminous" and "glow" and "glowing" as the stone basin.

Part 5 - Perceptual Mechanics

Chapter 1 - Glasses Rules

Rule for deciding the concealed possessions of something:
	if the particular possession is perception-hidden and the player is not wearing the spectacles:
		yes;
	otherwise:
		no.

Before going down from the Corridor when the player is not wearing the spectacles:
	say "The floor is solid tile. There is no way down." instead.

Before going through the hidden trapdoor when the player is not wearing the spectacles:
	say "You see no such thing." instead.

Chapter 2 - Fungus Rules

Instead of eating the grey fungus:
	say "It tastes of nothing. Then of everything. The walls ripple once and settle into new shapes. You understand, now, that this is not distortion. This is clarity.[paragraph break]The world has not changed. Your ability to see it has.";
	now the fungus-consumed is true;
	remove the grey fungus from play;
	apply-fungus-transformations.

To apply-fungus-transformations:
	now the printed name of the reclining chair is "crouching thing";
	now the description of the reclining chair is "It has four legs and a flat back. You know it is a chair. It does not look like a chair. Its leather is skin. Its restraints are tendons.";
	now the printed name of the instrument trays is "bone shelves";
	now the description of the instrument trays is "They are not steel. They are cartilage, smooth and pale, arranged like ribs along the wall.";
	now the printed name of the sweating pipes is "arteries";
	now the description of the sweating pipes is "They pulse. The condensation is warm now, and slightly viscous. These are not pipes. They have never been pipes.";
	now the printed name of the metal cabinet is "iron ribcage";
	now the description of the metal cabinet is "What you called a cabinet is a cage of fused iron bones. It stands open like a chest cavity after surgery.";
	now the printed name of the specimen jars is "organs";
	now the description of the specimen jars is "Not jars. Transparent sacs of membrane, each holding a dark shape that twitches when you look directly at it. They are alive. They have always been alive.";
	change the south exit of the Laboratory to the Cistern.

Before going south from the Laboratory when the fungus-consumed is false:
	say "The floor here is solid. There is no passage south." instead.

Before going south from the Laboratory when the fungus-consumed is true:
	if the Cistern is not visited:
		say "Where the floor was solid before, a wound has opened -- a vertical shaft lined in something wet and muscular. You descend.[paragraph break]";
	otherwise:
		say "You descend through the opening in the floor.";
	continue the action.

Chapter 3 - Spray Rules

Spray Exposure is a scene.
Spray Exposure begins when the player is in the Cistern and the spray-active is false and the fungus-consumed is true.

When Spray Exposure begins:
	say "A hiss from the cracked pipes overhead. Something cold and chemical settles on your skin, your eyes, your tongue. You blink. The letters on the sign shift. The walls flicker like a signal losing coherence.[paragraph break]When your vision steadies, the world has not returned to normal. It has gone further.";
	now the spray-active is true.

Rule for printing the name of the iron valve when the spray-active is true:
	say "[one of]ir0n valv3[or]iorn vlve[or]ir_n v@lve[at random]".

Rule for printing the name of the instructional sign when the spray-active is true:
	say "[one of]s1gn[or]fad3d s1gn[or]s_gn[at random]".

Rule for printing the name of the dark water when the spray-active is true:
	say "[one of]d@rk watr[or]drk w4ter[or]d_rk wat3r[at random]".

Rule for printing the name of the drainage grate when the spray-active is true:
	say "[one of]gr@te[or]dr4inage gr8[or]gr_te[at random]".

Rule for printing the name of the membrane walls when the spray-active is true:
	say "[one of]m3mbr@ne w4lls[or]w@lls[or]m_mbrane wal1s[at random]".

Rule for printing the name of the stone basin when the spray-active is true:
	say "[one of]st0ne b@sin[or]b4sin[or]st_ne bas1n[at random]".

Part 6 - Puzzles

Chapter 1 - The Hidden Stairwell

[Handled by concealment rules in Part 5 Chapter 1.]

Chapter 2 - The Locked Cabinet

Instead of unlocking the metal cabinet with the brass key:
	say "The key turns smoothly. The lock disengages with a click that echoes longer than it should.";
	now the metal cabinet is unlocked;
	now the metal cabinet is open.

Instead of unlocking the metal cabinet with something that is not the brass key:
	say "That does not fit the lock."

Instead of opening the metal cabinet when the metal cabinet is locked:
	say "It is locked. The keyhole beneath the handle is stamped with a snowflake."

Chapter 3 - The Valve Puzzle

Turning-left is an action applying to one thing.
Understand "turn [something] left" as turning-left.
Understand "turn [something] counterclockwise" as turning-left.
Understand "rotate [something] left" as turning-left.

Turning-right is an action applying to one thing.
Understand "turn [something] right" as turning-right.
Understand "turn [something] clockwise" as turning-right.
Understand "rotate [something] right" as turning-right.

Instead of turning-left the iron valve:
	if the cistern-drained is true:
		say "The valve is already fully open. The cistern is drained.";
	otherwise:
		say "You grip the handle and turn it left. Metal screams against metal. Below, the dark water begins to move -- circling, spiraling, draining. The level drops and keeps dropping until only a slick of pale residue remains on the bricks.[paragraph break]The drainage grate in the floor stands open now, revealing a narrow passage below.";
		now the cistern-drained is true.

Instead of turning-right the iron valve:
	if the cistern-drained is true:
		say "You grip the handle and turn it right. Water rushes back in with terrible speed. You did not expect it to be warm.";
		end the story saying "The water fills the chamber. It does not stop.";
	otherwise:
		say "You grip the handle and turn it right. A roar from the pipes above. Water surges in -- warm, fast, rising past your knees, your waist, your chest.";
		end the story saying "The water fills the chamber. It does not stop."

Instead of turning the iron valve:
	say "The handle can turn left or right. Choose carefully."

Before going down from the Cistern when the cistern-drained is false:
	say "Dark water fills the chamber below the grate. There is nowhere to descend." instead.

Before going down from the Cistern when the cistern-drained is true:
	say "You lower yourself through the grate.";
	continue the action.

The Source is below the Cistern.

Part 7 - Scenes and Transitions

Chapter 1 - The Endgame

The Endgame is a scene. The Endgame begins when the player is in the Source.

Part 8 - Custom Actions and Default Message Overrides

Chapter 1 - Smelling

Instead of smelling the Receiving Room:
	say "Iodine and old paper. Under that, something antiseptic and faintly sweet."

Instead of smelling the Corridor:
	say "[if fungus-consumed is true]Copper and salt. Living tissue.[otherwise]Disinfectant, faded but still sharp enough to sting your sinuses.[end if]"

Instead of smelling the Treatment Room:
	say "Alcohol and something metallic. The drainage channels around the chair have their own scent -- old iron."

Instead of smelling the Stairwell:
	say "Damp concrete and copper. The air is heavier here."

Instead of smelling the Laboratory:
	say "Chemicals -- not sharp, but layered. Formaldehyde under something sweeter."

Instead of smelling Cold Storage:
	say "Cold air and preservative. The sealed jars contain whatever smell their contents would produce."

Instead of smelling the Cistern:
	say "[if spray-active is true]Y0u sm3ll... ch3micals. And s0mething 3lse.[otherwise if fungus-consumed is true]Blood and mineral water. The chamber is a stomach.[otherwise]Stale water and mineral buildup. The pipes leak something chemical.[end if]"

Instead of smelling the Source:
	say "[if spray-active is true]W@rm. It sm3lls w@rm.[otherwise]Warm stone and something biological. The air is humid and close.[end if]"

Chapter 2 - Listening

Instead of listening to the Receiving Room:
	say "The fluorescent tube buzzes. Under it, silence -- the heavy, pressurised silence of a sealed building."

Instead of listening to the Corridor:
	say "[if fungus-consumed is true]Breathing. Not yours.[otherwise]Your footsteps echo. Nothing else.[end if]"

Instead of listening to the Treatment Room:
	say "Nothing. The room absorbs sound."

Instead of listening to the Stairwell:
	say "Water dripping. The rhythm is not quite regular -- it falters, catches, resumes."

Instead of listening to the Laboratory:
	say "A faint hum from the cabinets. Something electrical, still drawing power."

Instead of listening to Cold Storage:
	say "The compressor in the wall ticks at irregular intervals. Between ticks, absolute silence."

Instead of listening to the Cistern:
	say "[if spray-active is true]Dr1pp1ng. 0r is it a v0ice?[otherwise if fungus-consumed is true]The water speaks in a language of surface tension and resonance. You almost understand it.[otherwise]Water dripping from the cracked pipes. The echoes make it hard to tell how large the space is.[end if]"

Instead of listening to the Source:
	say "[if spray-active is true]A hum. B3low h3aring. Y0u f33l it in y0ur t33th.[otherwise]A hum below the threshold of hearing. You feel it in your teeth and the bones of your wrists.[end if]"

Chapter 3 - General Overrides

Instead of jumping:
	say "Your feet leave the floor and return to it. Nothing changes."

Instead of sleeping:
	say "You are already dreaming. Or you have stopped. You cannot tell."

Understand "sing" as a mistake ("Your voice sounds wrong in here -- flattened, as if the walls are absorbing the higher frequencies.").

Instead of waiting:
	say "Time passes. You are not sure how much."

Instead of examining the player:
	say "Your hands are steady. Your clothes are not yours -- a patient[apostrophe]s gown, thin and pale blue. You do not remember changing into it."

Chapter 4 - Inventory and Taking

Instead of taking scenery:
	say "It is fixed in place. Part of the building -- or the building is part of it."

Chapter 5 - Going Nowhere

Instead of going nowhere:
	say "There is no passage in that direction."
