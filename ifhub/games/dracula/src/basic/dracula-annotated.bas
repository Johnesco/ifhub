@@ ================================================================
@@  DRACULA'S CASTLE - ANNOTATED SOURCE
@@  A classic 1980s BASIC text adventure
@@  Annotations explain the game engine, data structures, and logic
@@ ================================================================
@@
@@ --- INITIALIZATION AND TITLE SCREEN ---
@@ Clear screen, display ASCII castle art, show welcome text,
@@ and prompt the player for instructions.
@@
0 GOSUB 215
1 PRINT:PRINT
2 GOSUB 193
3 GOSUB 188
4 PRINT CHR$(27)+"Y38";"Do you need instructions Y / N ";:INPUT A$:A$=LEFT$(A$+" ",1):GOSUB 215
5 IF A$="Y" THEN GOSUB 168 ELSE IF A$="y" THEN GOSUB 168
@@
@@ --- DATA STRUCTURES ---
@@ D$(1..19)  = Room names (19 rooms)
@@ O$(1..6)   = Direction names: North, South, East, West, Up, Down
@@ O$(7..31)  = Object names (25 objects)
@@ L(1..25)   = Object locations: 0=carried, 99=hidden, else room number
@@ P(1..19, 1..6) = Movement table: P(room, direction) = destination room
@@ L = Current room number (starts at 1 = Entrance Hall)
@@ C = Number of items carried (max 6)
@@ T1 = Minutes counter (0-59), T2 = Hour counter (starts at 8pm)
@@ R = Boat destination toggle (starts at 11, toggles with 27-R)
@@
6 DIM D$(19),O$(31),L(25),P(19,6):L=1
@@
@@ --- ROOM NAMES (19 rooms) ---
@@
7 FOR X=1 TO 19:READ D$(X):NEXT
8 DATA Entrance Hall,Study,Library,Armory,Tower
9 DATA Lower Tower,Chapel,Brick Fireplace
10 DATA Hidden Corridor,Secret Passage
11 DATA Underground Lake Chamber,Boat,Alchemist's Lab
12 DATA Storeroom,Overhang,Gallery,Antechamber,Dracula's Tomb
13 DATA Torture Chamber
@@
@@ --- OBJECT NAMES AND STARTING LOCATIONS ---
@@ O$(1-6) are direction words, O$(7+) are objects.
@@ Each object after index 6 has a location value:
@@   0 = player is carrying it
@@   99 = hidden/not in game yet
@@   1-19 = in that room number
@@ T2=8 means game starts at 8:00 PM.
@@ R=11 is the boat's initial shore (Underground Lake Chamber).
@@ WS$="Wooden Stakes" is used when crate is chopped with axe.
@@
14 FOR X=1 TO 31:READ O$(X):IF X>6 THEN READ L(X-6)
15 NEXT:T2=8:R=11:WS$="Wooden Stakes"
16 DATA North,South,East,West,"Up ",Down,Sledge Hammer,5
17 DATA Timepiece,1,Coil of Rope,9,Parchment Scroll,3,Axe,4,Oar,6,Key,99
18 DATA Holywater,7,Flask of Oil,13,Crate,14,Bucket,14
19 DATA Torch,8,Nails,15,Tapestry,16,Boat,11,Rusty Door,17
20 DATA Closed Coffin,18,Fire in the Fireplace,2
21 DATA Bookcase,3,Sign,1,Parapets,5,Brick Fireplace,2
22 DATA Rat,19,Wine,2,Cheddar Cheese,2
@@
@@ --- MOVEMENT TABLE P(room, direction) ---
@@ 6 values per room: N, S, E, W, Up, Down
@@ 0 = no exit. Non-zero = destination room number.
@@ Some connections are added dynamically by puzzles.
@@
@@  Room 1  Entrance Hall: E->Library(3), W->Study(2)
@@  Room 2  Study: E->Entrance Hall(1)
@@  Room 3  Library: E->Armory(4), W->Entrance Hall(1)
@@  Room 4  Armory: E->Tower(5), W->Library(3)
@@  Room 5  Tower: W->Armory(4)
@@  Room 6  Lower Tower: S->Chapel(7), U->Tower(5)
@@  Room 7  Chapel: N->Lower Tower(6), U->Armory(4)
@@
23 FOR Y=1 TO 19:FOR X=1 TO 6:READ P(Y,X):NEXT X,Y
24 DATA ,,3,2,,,,,1,,,,,,4,1,,,,,5,3,,,,,,4,,,,7,,,5,,6,,,,4,
@@
@@  Room 8  Brick Fireplace: S->Study(2)  [N->10 added when broken]
@@  Room 9  Hidden Corridor: N->Alchemist's Lab(13), U->Library(3)
@@  Room 10 Secret Passage: N->Lake(11), S->Fireplace(8), W->Torture(19)
@@  Room 11 Underground Lake: E->Secret Passage(10)
@@  Room 12 Boat: E->Underground Lake(11)
@@  Room 13 Alchemist's Lab: S->Storeroom(14), E->Hidden Corridor(9)
@@
25 DATA ,2,,,,,13,,,,3,,11,8,,19,,,,10,,,,,,11,,,,,14,9,,,,
@@
@@  Room 14 Storeroom: S->Alchemist's Lab(13), U->Study(2) [non-euclidean!]
@@  Room 15 Overhang: D->Gallery(16)
@@  Room 16 Gallery: (no exits initially) [N->17 added by tapestry puzzle]
@@  Room 17 Antechamber: S->Gallery(16) [N->18 added when door opened]
@@  Room 18 Dracula's Tomb: S->Antechamber(17)
@@  Room 19 Torture Chamber: E->Secret Passage(10), W->Alchemist's Lab(13)
@@
26 DATA ,13,,,2,,,,,,,16,,,,,,,,16,,,,,,17,,,,,,,10,13,,
@@
@@ --- VERB LOOKUP TABLE (W$) ---
@@ Packed 3-char verb codes. Position/3 = verb ID (F value).
@@ F=1:GO  2:GET  3:LOOK  4:DROP  5:HIT  6:OPEN
@@ F=7:TIE  8:PUSH  9:KILL  10:OIL  11:ROW
@@ Aliases: CLIMB->GO  TAKE->GET  READ->LOOK  THROW->DROP  BREAK->HIT
@@ (IDs 12-16 wrap to 1-5 via "IF F>11 THEN F=F-11")
@@
27 W$="GO GETLOODROHITOPETIEPUSKILOILROWCLITAKREATHRBRE"
@@
@@ --- NOUN SHORTCUT TABLE (N$) ---
@@ Maps 3-char abbreviations to object S-indices for fast lookup.
@@ Format: 3-char code + 2-digit S-value, packed in 5-char blocks.
@@ Used to resolve ambiguous/special nouns faster than the O$ scan.
@@
28 N$="N  01S  02E  03W  04U  05D  06HAM07SCR10AX 11WAT14OIL15DOO22COF23DRA23FIR28"
@@
@@ --- OBJECT NAME TABLE (O$) ---
@@ All nouns packed as 3-char codes. Position/3 = S-index.
@@ S=1-6 are directions, S=7+ are objects matching O$(S).
@@ Used by: X=INSTR(O$,B$): IF X MOD 3=1 THEN S=(X+2)/3
@@
29 O$="NORSOUEASWESUP DOWSLETIMROPPARAXEOARKEYHOLFLACRABUCTORNAITAPBOARUSCLOFIRBOOSIGPARBRIRATWINCHE"
@@
@@ ================================================================
@@  MAIN GAME LOOP (lines 30-55)
@@  Displays room, objects, exits. Gets input. Parses and dispatches.
@@ ================================================================
@@
@@ --- DISPLAY CURRENT ROOM ---
@@ GOSUB 227 sets dim text. Print room name from D$(L).
@@ L2 saves current room for object display check.
@@
30 GOSUB 227:PRINT:PRINT TAB(27);"You are in the ";D$(L):Y=0:L2=L
@@
@@ --- DARKNESS CHECK ---
@@ Rooms 10-12 and 18 are dark unless carrying torch (L(12)=0).
@@ L(12) is torch location; 0 means player carries it.
@@
31 IF L(12)=0 OR L<10 OR (L>12 AND L<>18) THEN 33
32 PRINT TAB(27);"It's Dark ! you can't see":GOTO 38
@@
@@ --- LIST VISIBLE OBJECTS AND EXITS ---
@@ Scans L(1..25) for objects in current room. Y counts items shown.
@@ Then scans P(L,1..6) for available movement directions.
@@
33 PRINT TAB(27);"You see ";:FOR X=1 TO 25:IF L(X)=L2 THEN PRINT O$(X+6);", ";:Y=Y+1
34 IF Y=2 THEN PRINT TAB(27);
35 NEXT:IF Y=0 THEN PRINT"nothing interesting." ELSE PRINT"   "
36 PRINT TAB(27);"Obvious exits are: ";:FOR X=1 TO 6:IF P(L,X)>0 THEN PRINT O$(X);" ";
37 NEXT:PRINT
@@
@@ --- PLAYER INPUT ---
@@ Prompts "What do you want to do". Splits input into:
@@   A$ = first word (verb), truncated to 3 chars
@@   B$ = last word (noun), truncated to 3 chars
@@ Single-letter input (N,S,E,W,U,D) becomes "GO " + letter.
@@
38 S=0:F=0:GOSUB 230:PRINT:PRINT TAB(27);"What do you want to do";:INPUT A$:PRINT
39 A$=A$:B$="   ":FOR X=1 TO LEN(A$)
40 IF MID$(A$,X,1)=" " THEN B$=MID$(A$+"   ",X+1,3)
41 NEXT:IF LEN(A$)=1 THEN B$=A$+"  ":A$="GO "
@@
@@ --- UPPERCASE AND TIME ---
@@ GOSUB 160 converts A$ and B$ to uppercase (first 3 chars only).
@@ Increment minute counter T1. At 60 minutes, advance hour T2.
@@
42 GOSUB 160:L2=L:T1=T1+1:IF T1=60 THEN T1=0:T2=T2+1
@@
@@ --- MIDNIGHT CHECK (game over) ---
@@
43 IF T2=12 THEN PRINT:PRINT"It's midnight:Dracula is awake, He's at your neck ";:GOTO 156
@@
@@ --- SWIMMING = DEATH ---
@@
44 IF A$="SWI" AND L=11 THEN PRINT:PRINT" You have drowned in the ice cold water ";:GOTO 156
@@
@@ --- NOUN RESOLUTION ---
@@ First tries N$ (shortcut table) for S-index.
@@ Then tries O$ (full object table) for S-index.
@@ S = object/direction index used by all verb handlers.
@@
45 X=INSTR(N$,B$):IF X MOD 5=1 THEN S=VAL(MID$(N$,X+3,2)):GOTO 47
46 X=INSTR(O$,B$):IF X MOD 3=1 THEN S=(X+2)/3
@@
@@ --- VERB RESOLUTION ---
@@ Looks up A$ in W$ to get verb index F.
@@ F>11 wraps back (CLIMB=GO, TAKE=GET, READ=LOOK, THROW=DROP, BREAK=HIT).
@@
47 X=INSTR(W$,A$):IF X MOD 3=1 THEN F=(X+2)/3
48 IF F>11 THEN F=F-11
@@
@@ --- INVENTORY COMMAND ---
@@ Lists all objects with location L(X)=0 (carried by player).
@@
49 IF A$<> "INV" THEN 54
50 PRINT"You are carrying: ";:A=0:FOR X=1 TO 25
51 IF L(X)=0 THEN PRINT O$(X+6)", ";:A=A+1
52 NEXT:IF A=0 THEN PRINT"nothing";
53 PRINT:GOTO 38
@@
@@ --- ACTION DISPATCH ---
@@ ON F dispatches to: 1=GO, 2=GET, 3=LOOK, 4=DROP, 5=HIT,
@@ 6=OPEN, 7=TIE, 8=PUSH, 9=KILL, 10=OIL, 11=ROW
@@ F=0 means verb not recognized.
@@
54 ON F GOTO 58,75,94,107,113,121,130,137,142,149,153
55 PRINT TAB(27);"I don't know how to do that":GOTO 38
56 PRINT TAB(27);"I don't know that word":GOTO 38
@@
@@ ================================================================
@@  GO HANDLER (lines 58-73)
@@  Handles standard movement + special: fireplace entry, rope climb,
@@  boat entry, and climbing to overhang via crate.
@@ ================================================================
@@
57 REM    *******     GO      **********
@@ Standard directional movement via the P() table:
58 IF S<1 THEN 62 ELSE IF S>6 THEN 62
59 IF P(L,S)>0 THEN L=P(L,S):GOTO 30
60 PRINT TAB(27);"You can't go that way":GOTO 38
61 PRINT TAB(27);"You see nothing special":GOTO 38
@@ GO FIREPLACE in Study (S=28, L=2): burns you unless fire is out (FI=1)
62 IF S<>28 OR L<>2 THEN 65
63 IF FI=0 THEN PRINT:PRINT TAB(27);"You have burned to death";:GOTO 156
64 L=8:GOTO 30
@@ GO PARAPETS in Tower (S=27, L=5): climb down rope if tied, else fall
65 IF S<>27 OR L<>5 THEN 68
66 IF LEFT$(O$(27),1)="R" THEN L=6:PRINT TAB(27);"Climbed down the rope":PRINT:GOTO 30
67 PRINT TAB(27);"You fell and died ";:GOTO 156
@@ GO BOAT: enter boat if boat object (L(15)) is in current room
68 IF S=21 AND L(15)=L THEN L=12:GOTO 30
@@ GO OVERHANG from Gallery (L=16): need crate on floor and not yet chopped
69 IF L=16 AND B$="OVE" THEN 72
70 IF S<1 THEN 56
71 PRINT TAB(27);"You can't go there":GOTO 38
72 IF L(10)=L AND O$(16)="Crate" THEN L=15:GOTO 30
73 PRINT TAB(27);"It's a little too high":GOTO 38
@@
@@ ================================================================
@@  GET HANDLER (lines 75-92)
@@  Picking up objects with special cases for holywater (needs bucket),
@@  tapestry (needs nails removed), nails (needs hammer),
@@  key (needs cheese to lure rat), and scenery items (S>20).
@@ ================================================================
@@
74 REM    *******    GET     ********
75 IF S<7 THEN 56
@@ Carry limit: maximum 6 items
76 IF C>6 THEN PRINT TAB(27);"You can't carry any more":GOTO 38
@@ Object must be in current room
77 IF L(S-6)<>L THEN 91
@@ GET HOLYWATER: asks "In what?" - needs bucket (L(11)=0 = carried)
78 IF S<>14 THEN 81
79 V$="In":GOSUB 165:IF A$="BUC" AND L(11)=0 THEN 92
80 PRINT TAB(27);"You can't do that":GOTO 38
@@ GET TAPESTRY: blocked if nails not removed (TA=0).
@@ Success reveals passage: Gallery(16) North -> Antechamber(17)
81 IF S<>20 THEN 84
82 IF TA=0 THEN PRINT TAB(27);"It's nailed to an overhang":GOTO 38
83 P(16,1)=17:PRINT TAB(27);"AHA ! - A hole in the wall":PRINT:GOTO 92
@@ GET NAILS: needs sledge hammer (L(1)=0 = carried).
@@ Removing nails from overhang loosens the tapestry (TA=1).
84 IF S<>19 THEN 87
85 IF L(1)<>0 THEN PRINT TAB(27);"You have no hammer":GOTO 38
86 IF L(13)=15 THEN TA=1:PRINT TAB(27);"The tapestry is loose":GOTO 92
@@ GET KEY: rat carries the key. Drop cheese in room to lure rat away.
@@ L(23)=L moves rat to current room. L(25)=L checks if cheese is here.
87 IF S<>13 THEN 90
88 L(23)=L:IF L(25)=L THEN 92
89 PRINT TAB(27);"The rat has it":GOTO 38
@@ Scenery items (S=21-29) can't be picked up
90 IF S>20 AND S<30 THEN PRINT TAB(27);"You can't get it":GOTO 38 ELSE 92
91 PRINT TAB(27);"I don't see any "O$(S):GOTO 38
@@ Success: increment carry count, set object location to 0 (carried)
92 C=C+1:L(S-6)=0:PRINT TAB(27);"You got the "O$(S):GOTO 38
@@
@@ ================================================================
@@  LOOK HANDLER (lines 94-105)
@@  LOOK with no object redisplays the room. LOOK at specific objects
@@  reveals clues: sign, rat (key in mouth), scroll, timepiece.
@@ ================================================================
@@
93 REM    ********     LOOK     *********
@@ LOOK with no noun (S<7) redisplays room
94 IF S<7 THEN 30
@@ LOOK SIGN in Entrance Hall: reveals the game's objective
95 IF S=26 AND L=1 THEN PRINT TAB(27);"'Dracula Wakes at Midnight'":GOTO 38
@@ LOOK RAT: reveals a key in its mouth! Sets L(7)=L to place key in room.
96 IF S<>29 THEN 99
97 IF L(23) <>L THEN 91
98 PRINT TAB(27);"A key is in it's mouth !":L(7)=L:GOTO 38
@@ LOOK SCROLL: must be carrying it. Reveals puzzle hint.
99 IF S<>10 THEN 103
100 IF L(4)=0 THEN 102
101 PRINT TAB(27);"you don't have it":GOTO 38
102 PRINT TAB(17);"The Scroll reads: 'Not all exits are obvious.'":GOTO 38
@@ LOOK TIMEPIECE: must be carrying it. Displays current game time.
103 IF S<>8 THEN 61
104 IF L(2) <>0 THEN 101
105 PRINT TAB(27); USING "The time is now ##:##";T2,T1:GOTO 38
@@
@@ ================================================================
@@  DROP HANDLER (lines 107-111)
@@  DROP OIL in Study extinguishes fire (FI=1), enabling fireplace entry.
@@ ================================================================
@@
106 REM    ********    DROP    **********
107 IF S<7 THEN 56
108 IF L(S-6) <>0 THEN 101
@@ DROP OIL in Study (S=14, L=2): extinguishes fire, sets FI=1
109 IF S<>14 OR L<>2 THEN 111
110 O$(24)="Smoldering Ashes":FI=1:L(8)=99:C=C-1:GOTO 30
111 PRINT TAB(20);"Okay, the "O$(S) " is on the "D$(L) " Floor":L(S-6)=L:C=C-1:GOTO 38
@@
@@ ================================================================
@@  HIT HANDLER (lines 113-119)
@@  HIT CRATE WITH AXE -> creates Wooden Stakes (needed to kill Dracula)
@@  HIT FIREPLACE WITH HAMMER -> breaks wall, reveals north passage
@@ ================================================================
@@
112 REM    *********   HIT   **********
113 IF S<7 THEN 56
114 IF L(S-6) <>L AND (L<>8 OR S<>28) THEN 91
@@ HIT CRATE WITH AXE: transforms crate into Wooden Stakes
@@ Also adds "WOO" and "STA" as noun aliases for the stakes.
115 V$="With":GOSUB 165:IF A$<>"AXE" OR S<>16 OR L(5)<>0 THEN 117
116 O$(16)=WS$:N$=N$+"WOO16STA16":GOTO 30
@@ HIT FIREPLACE WITH SLEDGE HAMMER: breaks wall open
@@ Adds north exit from Brick Fireplace(8) to Secret Passage(10).
117 IF (A$<> "SLE" AND A$<>"HAM") OR S<>28 OR L(1)<>0 THEN 119
118 O$(28)="Broken Fireplace":P(8,1)=10:D$(8)=O$(28):GOTO 30
119 PRINT TAB(27);"Nothing happened":GOTO 38
@@
@@ ================================================================
@@  OPEN HANDLER (lines 121-128)
@@  OPEN COFFIN: needs key. Reveals Dracula inside.
@@  OPEN DOOR: needs oil applied first (OI flag). Unreachable by design
@@  due to bug/"9I" - player must use OIL verb instead.
@@ ================================================================
@@
120 REM    *********    OPEN    *********
121 IF S<7 THEN 56
122 IF L(S-6)<>L THEN 91
@@ OPEN COFFIN: needs key carried (L(7)=0). Reveals Dracula.
123 IF S<>23 THEN 126
124 IF L(7)<>0 THEN PRINT TAB(27);"The coffin is locked ... ";:GOTO 119
125 O$(23)="Dracula in the Coffin":GOTO 30
@@ OPEN DOOR: "9I" is likely a bug for "OI". Always fails; use OIL instead.
126 IF S<>22 THEN 119
127 IF 9I=0 THEN PRINT TAB(27);"Too much rust ... ";:GOTO 119
128 O$(22)="Open Door":P(17,1)=18:GOTO 30
@@
@@ ================================================================
@@  TIE HANDLER (lines 130-135)
@@  TIE ROPE TO PARAPETS: enables climbing down from Tower to Lower Tower.
@@  Rope is consumed (L(3)=99). Parapets text changes to show rope.
@@ ================================================================
@@
129 REM   **********    TIE    ***********
130 IF S<7 THEN 56
131 IF L(S-6)<>0 THEN 101
132 IF S<>9 THEN 80
@@ Asks "To what?" - must answer PARAPETS
133 V$="To":GOSUB 165:IF A$<>"PAR" THEN 80
134 L(3)=99:C=C-1:O$(27)="Rope tied to the Parapet":N$=N$+"ROP27"
135 PRINT TAB(27);O$(27);" !":GOTO 38
@@
@@ ================================================================
@@  PUSH HANDLER (lines 137-140)
@@  PUSH BOOKCASE in Library: reveals a secret down exit to
@@  Hidden Corridor (room 9). Sets P(L,6)=9 (Down direction).
@@ ================================================================
@@
136 REM   *********    PUSH    **********
137 IF S<7 THEN 56
138 IF L(S-6)<>L THEN 91
139 IF S<>25 THEN 119
140 PRINT TAB(27);"Aha ! - You have revealed a Doorway":PRINT:P(L,6)=9:GOTO 30
@@
@@ ================================================================
@@  KILL HANDLER (lines 142-147)
@@  KILL DRACULA WITH WOODEN STAKES = win condition!
@@  Coffin must be open (O$(23) starts with "D" for "Dracula").
@@  Must carry wooden stakes (L(10)=0, O$(16)=WS$).
@@ ================================================================
@@
141 REM   *********    KILL    ************
142 IF S<7 THEN 56
@@ Target must be the coffin AND it must show "Dracula" (open)
143 IF S<>23 OR LEFT$(O$(23),1)<>"D" THEN 80
144 V$="With":GOSUB 165
@@ Must use wooden stakes (WOO or STA), carried (L(10)=0), crate=stakes
145 IF (A$="WOO" OR A$="STA") AND L(10)=0 AND O$(16)=WS$ THEN 147
146 PRINT:PRINT"You have failed ! Dracula awakes and sucks your blood !";:GOTO 156
@@ *** VICTORY! ***
147 PRINT:PRINT TAB(14);:GOSUB 218:PRINT"Congratulations ! ";:GOSUB 230:PRINT"You have KILLED Dracula ";USING"at ##:## p.m.";T2,T1:GOTO 156
@@
@@ ================================================================
@@  OIL HANDLER (lines 149-151)
@@  OIL DOOR in Antechamber: opens rusty door to Dracula's Tomb.
@@  Must carry flask of oil (L(9)=0), be in Antechamber (L=17),
@@  and target the door (S=22).
@@ ================================================================
@@
148 REM   *********    OIL     ***********
149 IF L(9)<>0 OR L<>17 OR S<>22 THEN 80
150 PRINT TAB(27);"The door squeaks open":PRINT
151 OI=1:O$(22)="Open Door":P(17,1)=18:GOTO 30
@@
@@ ================================================================
@@  ROW HANDLER (lines 153-155)
@@  ROW while in Boat (room 12) with oar (L(6)=0):
@@  R toggles between 11 and 16 (27-R). Moves player to shore.
@@  Boat object (L(15)) follows player to the new shore.
@@ ================================================================
@@
152 REM *********    ROW     **********
153 IF L<>12 OR L(6)<>0 THEN 80
154 R=27-R:L=R:PRINT TAB(27);"You have rowed to the ";D$(L)
155 PRINT:L(15)=L:GOTO 30
@@
@@ ================================================================
@@  GAME OVER / RESTART (lines 156-159)
@@ ================================================================
@@
156 PRINT:PRINT:PRINT:PRINT TAB(24);"Would you like to try again Y/N";:INPUT A$:GOSUB 160
157 IF LEFT$(A$,1)="Y" THEN RUN 0 ELSE IF LEFT$(A$,1)="y" THEN RUN 0
158 IF LEFT$(A$,1)="R" THEN T1=T1-2:GOTO 38
159 RUN"M"
@@
@@ ================================================================
@@  SUBROUTINES
@@ ================================================================
@@
@@ --- UPPERCASE CONVERTER (GOSUB 160) ---
@@ Truncates A$ and B$ to 3 chars, converts lowercase to uppercase.
@@ This is why the game only checks the first 3 letters of each word.
@@
160 REM   ********   MAKE INPUT U/C   *********
161 A$=LEFT$(A$+"   ",3):FOR I=1 TO 3
162 CH=ASC(MID$(A$,I,1)):IF CH>96 THEN MID$(A$,I,1)=CHR$(CH-32)
163 CH=ASC(MID$(B$,I,1)):IF CH>96 THEN MID$(B$,I,1)=CHR$(CH-32)
164 NEXT:RETURN
@@
@@ --- "WITH WHAT?" PROMPT (GOSUB 165) ---
@@ Used by HIT, TIE, KILL: asks "-- [With/To/In] what?"
@@ V$ is set before calling. Response stored in A$ (3 chars, uppercase).
@@
165 REM **********     GET "WHAT"   *******
166 PRINT:PRINT TAB(27);:PRINT"-- "V$" what";:INPUT A$
167 PRINT:PRINT:GOSUB 160:RETURN
@@
@@ --- INSTRUCTIONS TEXT (GOSUB 168) ---
@@
168 REM *********    INSTRUCTIONS     ***********
169 PRINT:PRINT:PRINT TAB(26);:GOSUB 224:PRINT"D R A C U L A ' S  C A S T L E":GOSUB 230
170 PRINT:PRINT
171 GOSUB 227
172 PRINT" Dracula's Castle has a concealed goal. You will learn the goal by exploring "
173 PRINT"your surroundings. The computer will act as you hands and eyes. It will accept"
174 PRINT"short phrases as commands and assumes that the first word is a verb and the "
175 PRINT"last word is the object. For example: ";:GOSUB 230:PRINT" READ THE SIGN ";:GOSUB 227:PRINT" The computer has a"
176 PRINT"vocabulary of about 70 words. Some of the more important words you should know"
177 PRINT"before you start playing are: ";:GOSUB 230:PRINT"GET (object), DROP (object), LOOK (object) ";:GOSUB 227:PRINT"or"
178 PRINT"just ";:GOSUB 230:PRINT"LOOK, GO (direction) ";:GOSUB 227:PRINT"or ";:GOSUB 230:PRINT"(PLACE)";:GOSUB 227:PRINT", and ";:GOSUB 230:PRINT"INVENTORY ";:GOSUB 227:PRINT" (tells what you"
179 PRINT"are carrying). The computer knows the abbreviations: ";:GOSUB 230:PRINT" E, W, N, S, U, ";:GOSUB 227:PRINT"and ";:GOSUB 230:PRINT"D ";:GOSUB 227:PRINT"for ";:GOSUB 230:PRINT"GO EAST, GO WEST, ";:GOSUB 227:PRINT"etc.":PRINT
180 PRINT" The computer's vocabulary is good, but limited. If you are having trouble "
181 PRINT"doing something, try re-phrasing the command or you may need some object to"
182 PRINT"accomplish the task. By the way, the computer only looks at the first 3 letters"
183 PRINT"of each word.":GOSUB 230
184 PRINT:PRINT TAB(31);"--- GOOD LUCK ---":PRINT:PRINT
185 INPUT"Press return to continue.....",A$
186 GOSUB 215
187 RETURN
@@
@@ --- WELCOME TEXT (GOSUB 188) ---
@@ Uses ANSI cursor positioning to display the title screen.
@@
188 REM ********    PRINT AT    ********
189 PRINT CHR$(27)+"Y%B";"W E L C O M E"
190 PRINT CHR$(27)+"Y':";"TO DRACULA'S CASTLE ADVENTURE"
191 PRINT CHR$(27)+"Y,@";:GOSUB 221:PRINT"ENTER IF YOU DARE";:GOSUB 230
192 RETURN
@@
@@ --- ASCII CASTLE ART (GOSUB 193) ---
@@ Draws a castle silhouette using block characters (CHR$(177)).
@@ Z$ = 2 block chars + 2 spaces (battlements pattern)
@@ X$ = 2 block chars (solid wall segments)
@@
193 REM ***********       CASTLE        **************
194 GOSUB 215
195 PRINT:PRINT:PRINT:PRINT
196 Z$=STRING$(2,177)+SPACE$(2)
197 X$=STRING$(2,177)
198 REM
199 REM
200 PRINT TAB(10);" ";:FOR Z=1 TO 4:PRINT Z$;:NEXT:FOR S=1 TO 15:PRINT"  ";:NEXT:FOR Z=1 TO 4:PRINT Z$;:NEXT:PRINT
201 PRINT TAB(10);" ";:FOR B=1 TO 7:PRINT X$;:NEXT:FOR S=1 TO 16:PRINT"  ";:NEXT:FOR B=1 TO 7:PRINT X$;:NEXT:PRINT
202 PRINT TAB(10);"   ";:FOR B=1 TO 5:PRINT X$;:NEXT:FOR S=1 TO 18:PRINT"  ";:NEXT:FOR B=1 TO 5:PRINT X$;:NEXT:PRINT
203 PRINT TAB(10);"   ";:FOR B=1 TO 5:PRINT X$;:NEXT:FOR S=1 TO 18:PRINT"  ";:NEXT:FOR B=1 TO 5:PRINT X$;:NEXT:PRINT
204 PRINT TAB(10);"   ";:PRINT X$;X$;"  ";X$;X$;:FOR S=1 TO 18:PRINT"  ";:NEXT:PRINT X$;X$;"  ";X$;X$;:PRINT
205 PRINT TAB(10);"   ";:PRINT X$;X$;"  ";X$;X$;:FOR S=1 TO 18:PRINT"  ";:NEXT:PRINT X$;X$;"  ";X$;X$;:PRINT
206 PRINT TAB(10);"   ";:FOR B=1 TO 5:PRINT X$;:NEXT:FOR S=1 TO 9:PRINT Z$;:NEXT:FOR B=1 TO 5:PRINT X$;:NEXT:PRINT
207 PRINT TAB(10);"   ";:FOR B=1 TO 28:PRINT X$;:NEXT:PRINT
208 PRINT TAB(10);"   ";:FOR B=1 TO 28:PRINT X$;:NEXT:PRINT
209 PRINT TAB(10);"   ";:FOR B=1 TO 28:PRINT X$;:NEXT:PRINT
210 PRINT TAB(10);"   ";:FOR B=1 TO 28:PRINT X$;:NEXT:PRINT
211 PRINT TAB(10);"   ";:FOR B=1 TO 14:PRINT X$;:NEXT:PRINT"  ";:FOR B=1 TO 13:PRINT X$;:NEXT:PRINT
212 RETURN
@@
@@ --- ANSI ESCAPE CODE SUBROUTINES ---
@@ These control terminal text formatting:
@@   GOSUB 215 = Clear screen (ESC + "E")
@@   GOSUB 218 = Inverse/flash text (ESC + "p")
@@   GOSUB 221 = Reverse flash (ESC + "p")
@@   GOSUB 224 = Underline (ESC + "0")
@@   GOSUB 227 = Dim/low-light text (no-op in this version)
@@   GOSUB 230 = Reset text formatting (ESC + "q" + "1")
@@
213 REM *******************     ESCAPE CODES     ******************
214 REM
215 REM ************     CLS     *********
216 PRINT CHR$(27)+"E";:RETURN
217 REM
218 REM ***********     NORMAL FLASH   *************
219 PRINT CHR$(27)+"p";:RETURN
220 REM
221 REM ***********     REVERSE NORMAL FLASH    **************
222 PRINT CHR$(27)+"p";:RETURN
223 REM
224 REM **********      NORMAL UNDERLINE   **************
225 PRINT CHR$(27)+"0";:RETURN
226 REM
227 REM ***********     LOW LIGHT      *************
228 RETURN
229 REM
230 REM ***********      RESET       **********
231 PRINT CHR$(27);"q";CHR$(27)+"1";:RETURN
232 REM
