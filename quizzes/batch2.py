"""v15–v26 : quiz plus difficiles (Facile -> Moyen -> Difficile). Réponses calculées ou vérifiées à la main."""
import json
from pathlib import Path
D = Path(__file__).parent
SC = lambda a: [[f"3/3  {a}", "🏆"], ["2/3  Nice job", "👏"], ["0-1  Try again!", "🔁"]]
HOOK = ["3 LEVELS", "Easy. Medium. HARD!"]

def pick(ans, deltas, pos):
    c = [ans]
    for d in deltas:
        v = ans + d
        if v > 0 and v not in c: c.append(v)
    assert len(c) == 4, (ans, c)
    order = c[1:]; order.insert(pos, ans)
    return [str(x) for x in order], pos

def math_round(level, e, vals, pos, deltas=(-3, 2, 5)):
    a, b, c = vals
    if level == "EASY":
        rows = [[e[0], "+", e[0], "=", str(2 * a)], [e[0], "+", e[1], "=", str(a + b)], [e[1], "+", e[1], "+", e[0], "=", "?"]]
        ans = 2 * b + a
    elif level == "MEDIUM":
        rows = [[e[0], "+", e[0], "+", e[0], "=", str(3 * a)], [e[0], "+", e[1], "+", e[1], "=", str(a + 2 * b)],
                [e[1], "+", e[2], "+", e[2], "=", str(b + 2 * c)], [e[0], "+", e[1], "+", e[2], "=", "?"]]
        ans = a + b + c
    else:
        rows = [[e[0], "+", e[0], "+", e[0], "=", str(3 * a)], [e[0], "+", e[1], "+", e[1], "=", str(a + 2 * b)],
                [e[1], "+", e[2], "+", e[2], "=", str(b + 2 * c)], [e[2], "+", e[2], "+", e[0], "+", e[1], "=", "?"]]
        ans = 2 * c + a + b
    items, k = pick(ans, deltas, pos)
    return {"kind": "emoji", "level": level, "q": "What is the missing number?", "lines": rows, "ly": 440, "lstep": 108, "tsize": 84,
            "oy": 840, "items": items, "answer": k, "answer_text": str(ans)}

def seq_round(level, seq, ans, deltas, pos):
    items, k = pick(ans, deltas, pos)
    return {"kind": "emoji", "level": level, "q": "Which number comes next?", "lines": [[str(x) for x in seq] + ["?"]], "ly": 560, "tsize": 100,
            "oy": 840, "items": items, "answer": k, "answer_text": str(ans)}

def mv(level, e, items, ans, name): return {"kind": "emoji", "level": level, "q": "Which movie is this?", "emoji": e, "items": items, "answer": ans, "answer_text": name}
def ct(level, e, items, ans, name): return {"kind": "emoji", "level": level, "q": "Which country is this?", "emoji": e, "items": items, "answer": ans, "answer_text": name}
def rd(level, q, items, ans, name): return {"kind": "emoji", "level": level, "q": q, "emoji": ["🤔"], "ey": 660, "esz": 140, "items": items, "answer": ans, "answer_text": name}
def gr(level, base, odd, pos, name, n=5, cell=150): return {"kind": "grid", "level": level, "q": "Find the odd emoji!", "rows": n, "cols": n, "cell": cell, "base": base, "odd": odd, "pos": pos, "answer_text": name}
def od(level, items, ans, name): return {"kind": "odd", "level": level, "q": "Which one is the odd one out?", "items": items, "answer": ans, "answer_text": name}

# sanity: vérification arithmétique des suites
assert 2*16 == 32 and 3*16 == 48 and 3 + 3 + 4 + 5 == 15 and 5+5+5+5 == 20
assert [n*(n+1) for n in range(1, 6)] == [2, 6, 12, 20, 30]
assert [n*n for n in range(1, 6)] == [1, 4, 9, 16, 25]
import math
assert [math.factorial(n) for n in range(1, 6)] == [1, 2, 6, 24, 120]

V = {
"v15": ("Emoji Math Puzzle 🧮 Can You Solve #3?", "emoji math", HOOK, "🧮", "Math genius",
  [math_round("EASY", ["🍎","🍌"], (10, 4, 0), 1), math_round("MEDIUM", ["🍓","🍋","🍇"], (8, 3, 5), 2), math_round("HARD", ["🥕","🍍","🥥"], (12, 5, 3), 0, (-4, 3, 6))]),
"v16": ("Guess the Movie by Emoji 🎬 Level 3 is HARD", "movie quiz", ["MOVIE CHALLENGE", "Easy. Medium. HARD!"], "🎬", "Cinema king",
  [mv("EASY", ["🚢","🧊"], ["Titanic","Jaws","Frozen","Poseidon"], 0, "Titanic"),
   mv("MEDIUM", ["🐀","👨‍🍳"], ["Zootopia","Cars","Ratatouille","Coco"], 2, "Ratatouille"),
   mv("HARD", ["🌀","💤"], ["Tenet","Interstellar","Matrix","Inception"], 3, "Inception")]),
"v17": ("3 Riddles 🧩 Can You Solve the Last One?", "riddles", ["3 RIDDLES", "Easy. Medium. HARD!"], "🧩", "Riddle master",
  [rd("EASY", "What has hands but can't clap?", ["A clock","A fish","A book","A river"], 0, "A clock"),
   rd("MEDIUM", "I speak without a mouth and hear without ears. What am I?", ["A shadow","An echo","A cloud","A book"], 1, "An echo"),
   rd("HARD", "What comes once in a minute, twice in a moment, but never in a thousand years?", ["The sun","A clock","The letter M","A second"], 2, "The letter M")]),
"v18": ("Number Sequence Test 🔢 Find the Next One", "number sequence", ["NUMBER TEST", "Easy. Medium. HARD!"], "🔢", "Number ninja",
  [seq_round("EASY", [2,4,6,8], 10, (2, -2, 4), 1), seq_round("MEDIUM", [3,6,12,24], 48, (-12, 6, 12), 3), seq_round("HARD", [2,6,12,20], 30, (-2, 4, 6), 0)]),
"v19": ("Odd One Out 🦇 Level 3 Is Tricky", "odd one out", ["ODD ONE OUT", "Easy. Medium. HARD!"], "🧠", "Big brain",
  [od("EASY", [["🐟","Fish"],["🐙","Octopus"],["🦀","Crab"],["🐘","Elephant"]], 3, "Elephant (lives on land)"),
   od("MEDIUM", [["🦅","Eagle"],["🦉","Owl"],["🦇","Bat"],["🐦","Sparrow"]], 2, "Bat (a mammal)"),
   od("HARD", [["🐝","Bee"],["🦋","Butterfly"],["🕷️","Spider"],["🐜","Ant"]], 2, "Spider (8 legs, not an insect)")]),
"v20": ("Spot the Odd Emoji 👀 Level 3 Is Evil", "spot the difference", ["SPOT IT", "Easy. Medium. HARD!"], "👀", "Hawk vision",
  [gr("EASY", "🙂", "🙃", [3, 1], "Upside-down face"), gr("MEDIUM", "😐", "😑", [4, 2], "Expressionless face", 6, 115), gr("HARD", "🕐", "🕜", [1, 4], "Clock at 1:30", 6, 115)]),
"v21": ("Guess the Flag 🇸🇳 Level 3 Is African", "flag quiz", ["FLAG QUIZ", "Easy. Medium. HARD!"], "🌍", "Geography pro",
  [ct("EASY", ["🇧🇷"], ["Portugal","Brazil","Mexico","Argentina"], 1, "Brazil"),
   ct("MEDIUM", ["🇬🇭"], ["Ethiopia","Bolivia","Ghana","Mali"], 2, "Ghana"),
   ct("HARD", ["🇸🇳"], ["Mali","Guinea","Cameroon","Senegal"], 3, "Senegal")]),
"v22": ("3 Hard Riddles 🤯 Only 1 Is Easy", "brain teaser", ["3 RIDDLES", "Easy. Medium. HARD!"], "🤯", "Super smart",
  [rd("EASY", "What has a neck but no head?", ["A bottle","A cloud","A giraffe","A river"], 0, "A bottle"),
   rd("MEDIUM", "What is full of holes but still holds water?", ["A bucket","A glass","A sponge","A bottle"], 2, "A sponge"),
   rd("HARD", "I have cities but no houses, mountains but no trees, and water but no fish. What am I?", ["A forest","A volcano","A river","A map"], 3, "A map")]),
"v23": ("Emoji Math Puzzle 2 🧠 Can You Solve #3?", "emoji math", HOOK, "🧮", "Math genius",
  [math_round("EASY", ["🐶","🐱"], (6, 3, 0), 3), math_round("MEDIUM", ["⚽","🏀","🎾"], (7, 2, 4), 0), math_round("HARD", ["🍕","🍔","🍟"], (9, 4, 6), 2, (-5, 3, 7))]),
"v24": ("Guess the Movie by Emoji 🎥 Level 3 Is HARD", "movie quiz", ["MOVIE CHALLENGE", "Easy. Medium. HARD!"], "🎥", "Cinema king",
  [mv("EASY", ["🕷️","🧑"], ["Batman","Spider-Man","Ant-Man","Superman"], 1, "Spider-Man"),
   mv("MEDIUM", ["🎈","🏠"], ["Coco","Soul","Brave","Up"], 3, "Up"),
   mv("HARD", ["🕶️","💊"], ["The Matrix","Inception","Tenet","Avatar"], 0, "The Matrix")]),
"v25": ("Mixed Challenge 🎯 Math, Odd One & Riddle", "mixed quiz", ["MIXED CHALLENGE", "Easy. Medium. HARD!"], "🎯", "Quiz champion",
  [math_round("EASY", ["🍩","🍪"], (5, 2, 0), 2), od("MEDIUM", [["🦈","Shark"],["🐠","Tropical fish"],["🐋","Whale"],["🐡","Pufferfish"]], 2, "Whale (a mammal)"),
   rd("HARD", "I speak without a mouth and hear without ears. What am I?", ["A shadow","An echo","A cloud","A book"], 1, "An echo")]),
"v26": ("Next Number? 🔢 Level 3 Is a Trap", "number sequence", ["NUMBER TEST", "Easy. Medium. HARD!"], "🔢", "Number ninja",
  [seq_round("EASY", [5,10,15,20], 25, (5, -5, 10), 2), seq_round("MEDIUM", [1,4,9,16], 25, (-5, 4, 11), 1), seq_round("HARD", [1,2,6,24], 120, (-24, 24, 96), 3)]),
}
INTRO = {'v17': 5.5, 'v22': 6.8, 'v25': 4.1}
DESC = "3 levels: Easy, Medium, HARD. Comment your answer to level 3! Like if you got 3/3, share it with a friend and subscribe for a new quiz every day. #Shorts #Quiz #BrainGames"
meta = {}
for k, (title, tag, hook, he, sc, rounds) in V.items():
    json.dump({"intro": INTRO.get(k, 2.5), "brand": "QUICK QUIZ", "hook": hook, "hook_emoji": he, "rounds": rounds, "scores": SC(sc)}, open(D / f"{k}.json", "w"), ensure_ascii=False)
    meta[k] = {"title": title[:95] + " #Shorts", "description": DESC, "tags": [tag, "quiz", "brain game", "shorts", "riddle", "trivia", "challenge"]}
json.dump(meta, open(D / "meta2.json", "w"), ensure_ascii=False, indent=1)
print(len(V), "specs OK")
