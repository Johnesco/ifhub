"Dracula's Castle" by "Anonymous"

The story headline is "An Interactive Adventure".
The story genre is "Horror".
The story description is "Explore Dracula's Castle and uncover its dark secret before midnight strikes."

Part 1 - Configuration

The carrying capacity of the player is 6.

Use scoring.
The maximum score is 1.

Part 2 - Time System

The game-hour is a number that varies. The game-hour is 8.
The game-minute is a number that varies. The game-minute is 0.

To say the-time:
	let h be the game-hour;
	let m be the game-minute;
	if h < 10:
		say " [h]";
	otherwise:
		say "[h]";
	say ":";
	if m < 10:
		say "0[m]";
	otherwise:
		say "[m]".

Every turn:
	increment the game-minute;
	if the game-minute is 60:
		now the game-minute is 0;
		increment the game-hour;
	if the game-hour >= 12:
		say "[paragraph break]It's midnight: Dracula is awake. He's at your neck!";
		end the story saying "You have died".

Part 3 - Rooms

Chapter 1 - Main Castle East-West Corridor

The Entrance Hall is a room. "You are in the Entrance Hall."
The player is in the Entrance Hall.

The Study is west of the Entrance Hall. "You are in the Study."

The Library is east of the Entrance Hall. "You are in the Library."

The Armory is east of the Library. "You are in the Armory."

The Tower is east of the Armory. "You are in the Tower."

Chapter 2 - Lower Tower and Chapel

The Lower Tower is a room. "You are in the Lower Tower."

The Chapel is south of the Lower Tower. "You are in the Chapel."

[Lower Tower: up goes to Tower (one-way, no reciprocal down from Tower)]
Instead of going up in the Lower Tower:
	now the player is in the Tower.

[Chapel: up goes to Armory (one-way)]
Instead of going up in the Chapel:
	now the player is in the Armory.

Chapter 3 - Fireplace Area

The Brick Fireplace Room is a room. The printed name is "Brick Fireplace". "You are in a Brick Fireplace."

[Brick Fireplace Room: south goes to Study (one-way)]
Instead of going south in the Brick Fireplace Room:
	now the player is in the Study.

[Brick Fireplace Room: north goes to Secret Passage only after fireplace is broken]
The fireplace-broken is a truth state that varies. The fireplace-broken is false.

Instead of going north in the Brick Fireplace Room:
	if the fireplace-broken is true:
		now the player is in the Secret Passage;
	otherwise:
		say "You can't go that way."

Chapter 4 - Below the Library

The Hidden Corridor is a room. "You are in a Hidden Corridor."

[Hidden Corridor: up goes to Library, north goes to Alchemist's Lab]
Instead of going up in the Hidden Corridor:
	now the player is in the Library.

Instead of going north in the Hidden Corridor:
	now the player is in the Alchemists Lab.

[Library: down goes to Hidden Corridor only after bookcase is pushed]
The bookcase-pushed is a truth state that varies. The bookcase-pushed is false.

Instead of going down in the Library:
	if the bookcase-pushed is true:
		now the player is in the Hidden Corridor;
	otherwise:
		say "You can't go that way."

Chapter 5 - Underground

The Secret Passage is a dark room. "You are in a Secret Passage."

Instead of going north in the Secret Passage:
	now the player is in the Underground Lake Chamber.

Instead of going south in the Secret Passage:
	now the player is in the Brick Fireplace Room.

Instead of going west in the Secret Passage:
	now the player is in the Torture Chamber.

The Underground Lake Chamber is a dark room. "You are in an Underground Lake Chamber."

Instead of going east in the Underground Lake Chamber:
	now the player is in the Secret Passage.

Chapter 6 - The Boat

Aboard the Boat is a dark room. "You are aboard a small boat on an underground lake."

The boat-shore is a room that varies. The boat-shore is the Underground Lake Chamber.

Instead of going east in Aboard the Boat:
	now the player is in the boat-shore.

Chapter 7 - Alchemist Area

The Alchemists Lab is a room. The printed name is "Alchemist's Lab". "You are in an Alchemist's Lab."

Instead of going south in the Alchemists Lab:
	now the player is in the Storeroom.

Instead of going east in the Alchemists Lab:
	now the player is in the Hidden Corridor.

The Storeroom is a room. "You are in a Storeroom."

[Storeroom: south goes to Alchemist's Lab (non-euclidean), up goes to Study]
Instead of going south in the Storeroom:
	now the player is in the Alchemists Lab.

Instead of going up in the Storeroom:
	now the player is in the Study.

Chapter 8 - Gallery Area

The Overhang is a room. "You are on an Overhang high above the Gallery."

Instead of going down in the Overhang:
	now the player is in the Gallery.

The Gallery is a room. "You are in the Gallery."

The tapestry-removed is a truth state that varies. The tapestry-removed is false.

Instead of going north in the Gallery:
	if the tapestry-removed is true:
		now the player is in the Antechamber;
	otherwise:
		say "You can't go that way."

Chapter 9 - Dracula's Domain

The Antechamber is a room. "You are in the Antechamber."

Instead of going south in the Antechamber:
	now the player is in the Gallery.

The door-opened is a truth state that varies. The door-opened is false.

Instead of going north in the Antechamber:
	if the door-opened is true:
		now the player is in Draculas Tomb;
	otherwise:
		say "You can't go that way."

Draculas Tomb is a dark room. The printed name is "Dracula's Tomb". "You are in Dracula's Tomb."

Instead of going south in Draculas Tomb:
	now the player is in the Antechamber.

Chapter 10 - Torture Chamber

The Torture Chamber is a room. "You are in the Torture Chamber."

Instead of going east in the Torture Chamber:
	now the player is in the Secret Passage.

Instead of going west in the Torture Chamber:
	now the player is in the Alchemists Lab.

Part 4 - Portable Objects

The sledge hammer is a thing in the Tower. The description is "A heavy sledge hammer."
Understand "hammer" and "sledge" as the sledge hammer.

The timepiece is a thing in the Entrance Hall. The description is "An old timepiece."
Understand "watch" and "clock" as the timepiece.

The coil of rope is a thing in the Hidden Corridor. The description is "A long coil of rope."
Understand "rope" as the coil of rope.

The parchment scroll is a thing in the Library. The description is "An old parchment scroll."
Understand "scroll" and "parchment" as the parchment scroll.

The axe is a thing in the Armory. The description is "A sharp axe."

The oar is a thing in the Lower Tower. The description is "A wooden oar."

The rusty key is a thing. The description is "A rusty iron key."
Understand "key" as the rusty key.
[The key starts hidden -- it is revealed by examining the rat]
The key-visible is a truth state that varies. The key-visible is false.

The holywater is a thing in the Chapel. The description is "A vessel of holy water."
Understand "holy" and "water" as the holywater.
The holywater-collected is a truth state that varies. The holywater-collected is false.

The flask of oil is a thing in the Alchemists Lab. The description is "A flask of oil."
Understand "oil" and "flask" as the flask of oil.

The crate is a thing in the Storeroom. The description is "A wooden crate."
The crate-is-stakes is a truth state that varies. The crate-is-stakes is false.

The bucket is a thing in the Storeroom. The description is "A wooden bucket."

The torch is a thing in the Brick Fireplace Room. The torch is lit. The description is "A flaming torch."

The nails is a thing in the Overhang. The description is "A handful of iron nails."
Understand "nail" as the nails.
The nails-removed is a truth state that varies. The nails-removed is false.

The tapestry is a thing in the Gallery. The description is "A large woven tapestry."

The wine is a thing in the Study. The description is "A bottle of wine."

The cheddar cheese is a thing in the Study. The description is "A wedge of cheddar cheese."
Understand "cheese" and "cheddar" as the cheddar cheese.

Part 5 - Scenery Objects

The wooden boat is scenery in the Underground Lake Chamber. The description is "A small wooden boat sits at the water's edge."
Understand "boat" as the wooden boat.

The rusty door is scenery in the Antechamber.
Understand "door" as the rusty door.
The description of the rusty door is "[if the door-opened is true]The door stands open[otherwise]A rusty iron door blocks the way north[end if]."

The closed coffin is scenery in Draculas Tomb.
The coffin-open is a truth state that varies. The coffin-open is false.
The description of the closed coffin is "[if the coffin-open is true]The coffin lies open. Dracula rests within![otherwise]A large closed coffin.[end if]".
Understand "coffin" as the closed coffin.
The printed name of the closed coffin is "[if the coffin-open is true]Dracula in the Coffin[otherwise]Closed Coffin[end if]".

The fireplace-fire is scenery in the Study. The printed name is "Fire in the Fireplace".
Understand "fire" and "fireplace" as the fireplace-fire.
The fire-extinguished is a truth state that varies. The fire-extinguished is false.
The description of the fireplace-fire is "[if the fire-extinguished is true]Smoldering ashes are all that remain of the fire.[otherwise]A roaring fire burns in the fireplace.[end if]".

The study-fireplace is scenery in the Study. The printed name is "Brick Fireplace".
Understand "brick" as the study-fireplace.
The description of the study-fireplace is "A large brick fireplace dominates one wall of the study. [if the fire-extinguished is false]A fire burns within it.[otherwise]The fire has been extinguished.[end if]".

The bookcase is scenery in the Library. The description is "A large, heavy bookcase."
Understand "bookcase" and "book case" and "books" as the bookcase.

The castle-sign is scenery in the Entrance Hall. The printed name is "Sign".
Understand "sign" as the castle-sign.
The description of the castle-sign is "'Dracula Wakes at Midnight'".

The parapets is scenery in the Tower.
Understand "parapet" as the parapets.
The description of the parapets is "[if the rope-on-parapet is true]A rope hangs from the parapets, leading down[otherwise]Stone parapets overlook a dizzying drop[end if]."

The brick-wall-fireplace is scenery in the Brick Fireplace Room. The printed name is "[if the fireplace-broken is true]Broken Fireplace[otherwise]Brick Fireplace wall[end if]".
Understand "brick" and "wall" and "bricks" as the brick-wall-fireplace.
The description of the brick-wall-fireplace is "[if the fireplace-broken is true]The fireplace wall has been smashed open, revealing a passage to the north.[otherwise]Solid brickwork surrounds you.[end if]".

The rat is scenery in the Torture Chamber.
Understand "rat" as the rat.
The description of the rat is "[if the key-visible is false]A rat scurries about -- a key is in its mouth![otherwise]A rat scurries about, nibbling on some cheese[end if]."

Part 6 - Custom Actions

Chapter 1 - Reading the Scroll

Instead of examining the parchment scroll:
	if the player carries the parchment scroll:
		say "The scroll reads: 'Not all exits are obvious.'";
	otherwise:
		say "You don't have it."

Chapter 2 - Reading the Timepiece

Instead of examining the timepiece:
	if the player carries the timepiece:
		say "The time is now [the-time].";
	otherwise:
		say "You don't have it."

Chapter 3 - Examining the Sign

Instead of examining the castle-sign:
	say "'Dracula Wakes at Midnight'".

Chapter 4 - Examining the Rat and Getting the Key

After examining the rat:
	if the key-visible is false:
		say "A key is in its mouth!";
		now the key-visible is true;
		now the rusty key is in the location of the rat.

Instead of taking the rusty key:
	if the key-visible is false:
		say "You don't see any key here." instead;
	if the cheddar cheese is in the location:
		say "The rat takes the cheese and drops the key. You got the key!";
		now the player carries the rusty key;
		remove the cheddar cheese from play;
	otherwise:
		say "The rat has it! Perhaps something could lure it away."

Chapter 5 - Getting the Holywater

Instead of taking the holywater:
	if the holywater-collected is true:
		continue the action;
	if the player does not carry the bucket:
		say "You can't carry holy water without a container. You need a bucket." instead;
	say "You collect the holy water in the bucket.";
	now the holywater-collected is true;
	now the player carries the holywater.

Chapter 6 - Getting the Nails

Instead of taking the nails:
	if the nails-removed is true:
		continue the action;
	if the player does not carry the sledge hammer:
		say "You have no hammer to pry out the nails." instead;
	say "Using the hammer, you pry the nails loose. The tapestry is loose!";
	now the nails-removed is true;
	now the player carries the nails.

Chapter 7 - Getting the Tapestry

Instead of taking the tapestry:
	if the nails-removed is false:
		say "It's nailed to an overhang. You can't pull it free." instead;
	say "AHA! A hole in the wall is revealed behind the tapestry![paragraph break]";
	now the tapestry-removed is true;
	now the player carries the tapestry.

Chapter 8 - Entering the Fireplace

Instead of entering the fireplace-fire:
	try going inside.

Instead of entering the study-fireplace:
	try going inside.

Instead of going inside in the Study:
	if the fire-extinguished is false:
		say "You have burned to death!";
		end the story saying "You have died";
	otherwise:
		now the player is in the Brick Fireplace Room.

Chapter 9 - Dropping Oil on Fire

Instead of dropping the flask of oil in the Study:
	if the fire-extinguished is false:
		say "The oil douses the flames. The fire sputters and dies, leaving only smoldering ashes.";
		now the fire-extinguished is true;
		remove the flask of oil from play;
	otherwise:
		continue the action.

Chapter 10 - Pushing the Bookcase

Instead of pushing the bookcase:
	if the bookcase-pushed is true:
		say "The bookcase has already been moved." instead;
	say "Aha! You have revealed a doorway leading down!";
	now the bookcase-pushed is true.

Chapter 11 - Breaking the Crate into Stakes

Attacking it with is an action applying to one visible thing and one carried thing.
Understand "hit [something] with [something]" as attacking it with.
Understand "break [something] with [something]" as attacking it with.
Understand "smash [something] with [something]" as attacking it with.

Instead of attacking the crate:
	say "Hit it with what?"

Instead of attacking the crate with the axe:
	if the crate-is-stakes is true:
		say "You have already made wooden stakes." instead;
	if the player does not carry the axe:
		say "You don't have the axe." instead;
	say "You chop the crate into wooden stakes!";
	now the printed name of the crate is "Wooden Stakes";
	now the crate-is-stakes is true;
	now the description of the crate is "Sharpened wooden stakes, fashioned from the crate."

Understand "stakes" and "wooden stakes" and "stake" as the crate when the crate-is-stakes is true.

Chapter 12 - Breaking the Fireplace Wall

Instead of attacking the brick-wall-fireplace:
	say "Hit it with what?"

Instead of attacking the brick-wall-fireplace with the sledge hammer:
	if the fireplace-broken is true:
		say "It's already smashed open." instead;
	say "You smash through the brickwork! A passage is revealed to the north!";
	now the fireplace-broken is true.

Chapter 13 - Tying the Rope

The rope-on-parapet is a truth state that varies. The rope-on-parapet is false.

Understand "attach [something] to [something]" as tying it to.

Instead of tying the coil of rope to the parapets:
	say "You tie the rope securely to the parapets!";
	now the rope-on-parapet is true;
	remove the coil of rope from play.

Instead of tying something to something:
	say "You can't tie that to that."

Chapter 14 - Climbing Down from Tower

Instead of going down in the Tower:
	if the rope-on-parapet is true:
		say "You climb down the rope.";
		now the player is in the Lower Tower;
	otherwise:
		say "You can't go that way."

Instead of climbing the parapets:
	if the rope-on-parapet is true:
		say "You climb down the rope.";
		now the player is in the Lower Tower;
	otherwise:
		say "You would fall to your death! You need a rope."

Chapter 15 - Entering and Rowing the Boat

Instead of entering the wooden boat:
	say "You climb into the boat.";
	now the player is in Aboard the Boat.

Rowing is an action applying to nothing.
Understand "row" as rowing.

Check rowing:
	if the player is not in Aboard the Boat:
		say "You're not in a boat." instead;
	if the player does not carry the oar:
		say "You have nothing to row with. You need an oar." instead.

Carry out rowing:
	if the boat-shore is the Underground Lake Chamber:
		now the boat-shore is the Gallery;
		say "You row across the underground lake...";
		now the player is in the Gallery;
		now the wooden boat is in the Gallery;
	otherwise:
		now the boat-shore is the Underground Lake Chamber;
		say "You row across the underground lake...";
		now the player is in the Underground Lake Chamber;
		now the wooden boat is in the Underground Lake Chamber.

Chapter 16 - Climbing to the Overhang

Instead of going up in the Gallery:
	if the crate is in the Gallery and the crate-is-stakes is false:
		say "You stand on the crate and climb up to the overhang.";
		now the player is in the Overhang;
	otherwise if the crate-is-stakes is true:
		say "The crate has been chopped into stakes. You can't climb up.";
	otherwise:
		say "It's a little too high to reach."

Understand "climb to overhang" or "climb to the overhang" or "go to overhang" or "go to the overhang" as a mistake ("You'd need to go up to reach the overhang. Try 'up'.") when the location is the Gallery.

Chapter 17 - Oiling the Door

Oiling is an action applying to one visible thing.
Understand "oil [something]" as oiling.

Check oiling:
	if the noun is not the rusty door:
		say "You can't oil that." instead;
	if the player does not carry the flask of oil:
		say "You have no oil." instead;
	if the location is not the Antechamber:
		say "You don't see a door here." instead.

Carry out oiling:
	if the noun is the rusty door:
		say "The door squeaks open!";
		now the door-opened is true;
		now the printed name of the rusty door is "Open Door";
		remove the flask of oil from play.

Chapter 18 - Opening the Coffin

Instead of opening the closed coffin:
	if the coffin-open is true:
		say "The coffin is already open." instead;
	if the player does not carry the rusty key:
		say "The coffin is locked." instead;
	say "You unlock and open the coffin... Dracula lies within!";
	now the coffin-open is true.

Chapter 19 - Killing Dracula

Killing it with is an action applying to one visible thing and one carried thing.
Understand "kill [something] with [something]" as killing it with.
Understand "stab [something] with [something]" as killing it with.
Understand "stake [something] with [something]" as killing it with.

Instead of attacking the closed coffin:
	try killing the closed coffin with the crate.

Instead of killing the closed coffin with something:
	if the coffin-open is false:
		say "The coffin is closed." instead;
	if the crate-is-stakes is false:
		say "You have failed! Dracula awakes and sucks your blood!";
		end the story saying "You have died";
	if the second noun is not the crate:
		say "You have failed! Dracula awakes and sucks your blood!";
		end the story saying "You have died";
	if the player does not carry the crate:
		say "You don't have the wooden stakes!" instead;
	say "[paragraph break]Congratulations! You have KILLED Dracula at [the-time] p.m.!";
	increase the score by 1;
	end the story finally saying "You have won".

Chapter 20 - Swimming

Swimming is an action applying to nothing.
Understand "swim" as swimming.

Instead of swimming in the Underground Lake Chamber:
	say "You have drowned in the ice cold water!";
	end the story saying "You have died".

Instead of swimming:
	say "There's no water here to swim in."

Part 7 - Miscellaneous Rules

[Block going in directions with no exit from rooms that use Instead rules]
Instead of going nowhere:
	say "You can't go that way."

[Print available exits after room description]
After looking:
	let exit-list be a text;
	let exit-list be "";
	if the room north from the location is not nothing or (the location is the Gallery and the tapestry-removed is true) or (the location is the Antechamber and the door-opened is true) or (the location is the Brick Fireplace Room and the fireplace-broken is true) or (the location is the Hidden Corridor) or (the location is the Secret Passage):
		let exit-list be "[exit-list]North ";
	if the room south from the location is not nothing or (the location is the Brick Fireplace Room) or (the location is the Alchemists Lab) or (the location is the Storeroom) or (the location is the Antechamber) or (the location is Draculas Tomb) or (the location is the Secret Passage):
		let exit-list be "[exit-list]South ";
	if the room east from the location is not nothing or (the location is the Underground Lake Chamber) or (the location is Aboard the Boat) or (the location is the Alchemists Lab) or (the location is the Torture Chamber):
		let exit-list be "[exit-list]East ";
	if the room west from the location is not nothing or (the location is the Secret Passage) or (the location is the Torture Chamber):
		let exit-list be "[exit-list]West ";
	if (the location is the Lower Tower) or (the location is the Chapel) or (the location is the Hidden Corridor) or (the location is the Storeroom):
		let exit-list be "[exit-list]Up ";
	if (the location is the Library and the bookcase-pushed is true) or (the location is the Tower and the rope-on-parapet is true) or (the location is the Overhang):
		let exit-list be "[exit-list]Down ";
	if exit-list is not "":
		say "Obvious exits are: [exit-list][line break]".

When play begins:
	say "[bold type]W E L C O M E[roman type][line break]";
	say "TO DRACULA'S CASTLE ADVENTURE[line break]";
	say "[italic type]ENTER IF YOU DARE[roman type][paragraph break]";
	say "Dracula's Castle has a concealed goal. You will learn the goal by exploring your surroundings. The computer will act as your hands and eyes.[paragraph break]";
	say "Important words: GET, DROP, LOOK, GO, INVENTORY, PUSH, TIE, HIT, OIL, ROW, OPEN, KILL.[paragraph break]";
	say "Direction abbreviations: N, S, E, W, U, D.[paragraph break]";
	say "[bold type]--- GOOD LUCK ---[roman type][paragraph break]".
