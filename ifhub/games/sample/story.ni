"Sample" by "Claude Code"

The story headline is "An Interactive Fiction".
The story genre is "Fantasy".
The release number is 1.
The story creation year is 2026.
The story description is "A practice game for learning Inform 7: rooms, objects, and interactions."

Use American dialect.
Use scoring.
The maximum score is 10.

Part 1 - Configuration

Chapter 1 - Bibliographic and Settings

When play begins:
	now the left hand status line is "[the player's surroundings]   Score: [score]/[turn count]";
	now the right hand status line is "";
	say "[bold type]Sample[roman type][line break]An Interactive Fiction by Claude Code[line break]Release 1[paragraph break]".

Chapter 2 - Score Ranks

Table of Rankings
score	ranking
0	"Beginner"
5	"Explorer"
10	"Winner"

Part 2 - The World

Chapter 1 - The Entrance Hall

The Entrance Hall is a room. "A grand hall with marble floors and high ceilings. A crystal chandelier hangs overhead. Exits lead north to a library, east to a kitchen, and south to a garden."

The crystal chandelier is scenery in the Entrance Hall. The description is "An ornate chandelier with dozens of sparkling crystals."

A brass key is in the Entrance Hall. The description is "A small brass key with an intricate pattern etched into its handle."

Chapter 2 - The Library

The Library is north of the Entrance Hall. "Tall bookshelves line every wall, crammed with leather-bound volumes. A reading desk sits in the center of the room. A narrow staircase leads up."

The bookshelves are scenery in the Library. The description is "Rows upon rows of old books. Most are too faded to read."

The reading desk is a supporter in the Library. The description is "A sturdy oak desk with a green leather writing surface." It is fixed in place.

A dusty journal is on the reading desk. The description is "A leather-bound journal. The pages are yellowed with age."

Instead of opening the dusty journal:
	say "You flip through the journal. Most entries are illegible, but one page reads: 'The treasure is hidden where water meets stone.'";
	if the dusty journal is not handled:
		increase the score by 2;
		now the dusty journal is handled.

A thing can be handled or unhandled. A thing is usually unhandled.

Chapter 3 - The Study

The Study is up from the Library. "A cozy room at the top of the narrow staircase. A wooden cabinet stands against one wall. The only exit is back down."

The wooden cabinet is a closed openable container in the Study. The description is "A tall cabinet made of dark walnut. It has a small brass lock." It is fixed in place and locked. The brass key unlocks the wooden cabinet.

A silver locket is in the wooden cabinet. The description is "A delicate silver locket on a fine chain. It feels warm to the touch."

After taking the silver locket for the first time:
	say "As you pick up the locket, it glows faintly. You feel a sense of accomplishment.";
	increase the score by 3.

Chapter 4 - The Kitchen

The Kitchen is east of the Entrance Hall. "A rustic kitchen with a stone hearth and a heavy wooden table. The smell of old spices lingers in the air. A doorway leads west back to the hall."

The stone hearth is scenery in the Kitchen. The description is "A large hearth, cold now, with a few charred logs inside."

The wooden table is a supporter in the Kitchen. The description is "A rough-hewn table scarred by years of use." It is fixed in place.

A loaf of bread is on the wooden table. The description is "A somewhat stale loaf of bread. Still edible, probably."
The loaf of bread is edible.

A ceramic mug is on the wooden table. The description is "A plain ceramic mug. It's empty."
The ceramic mug is a container. The carrying capacity of the ceramic mug is 1.

Chapter 5 - The Garden

The Garden is south of the Entrance Hall. "A walled garden overgrown with ivy and wildflowers. A stone fountain stands in the center, dry and cracked. A path continues south to a pond."

The stone fountain is scenery in the Garden. The description is "An old fountain carved with fish and waves. No water flows here anymore."

The ivy is scenery in the Garden. The description is "Thick green ivy covers much of the garden walls."

A rusty coin is in the Garden. The description is "An old coin, green with age. Some kind of face is stamped on one side."

After taking the rusty coin for the first time:
	say "You brush off the grime. Despite its age, the coin has a satisfying weight.";
	increase the score by 2.

Chapter 6 - The Pond

The Pond is south of the Garden. "A small, murky pond surrounded by reeds and flat stones. The water is still and dark. The garden lies back to the north."

The reeds are scenery in the Pond. The description is "Tall reeds swaying slightly, even though there is no wind."

The flat stones are scenery in the Pond. The description is "Smooth, flat stones line the edge of the pond. One of them looks loose."

A golden ring is nowhere. The description is "A simple gold band that gleams even in dim light."

Instead of pushing the flat stones:
	if the golden ring is nowhere:
		now the golden ring is in the Pond;
		say "You push aside one of the loose stones and discover a golden ring hidden beneath it!";
		increase the score by 3;
	otherwise:
		say "You already found what was hidden here."

Part 3 - Winning

Every turn:
	if the score is 10:
		say "[line break][bold type]Congratulations![roman type] You have found all the secrets of this place. You win!";
		end the story finally saying "You have won".
