"""Micro-quiz ~12 s (1 question difficile, ouverture en action, boucle) m01..m10."""
import json, sys
from pathlib import Path
sys.argv = ["x"]; D = Path(__file__).parent
exec(open(D / "batch2.py").read().split("V = {")[0])   # réutilise les générateurs
def micro(r, title, tag):
    r["level"] = "HARD"
    return {"micro": True, "hook_len": 0, "outro_len": 3.2, "think": 5.0, "reveal": 1.8, "intro": 2.1, "brand": "QUICK QUIZ", "hook": ["", ""],
            "hook_emoji": "🧠", "rounds": [r], "scores": [], "outro_say": "Comment your answer, and subscribe for a new quiz every day!"}, title, tag
M = {
"m01": micro(math_round("HARD", ["🍕","🍔","🍟"], (9, 4, 7), 1, (-4, 3, 6)), "Hard Emoji Math 🧮 Can You Solve It?", "emoji math"),
"m02": micro(rd("HARD", "What has to be broken before you can use it?", ["An egg","A plate","A watch","A key"], 0, "An egg"), "Hard Riddle 🧩 What Must Be Broken?", "riddles"),
"m03": micro(seq_round("HARD", [2,3,5,7], 11, (-2, 2, 4), 1), "Next Number? 🔢 Prime Time Puzzle", "number sequence"),
"m04": micro(mv("HARD", ["🦖","🏝️"], ["Kong","Jurassic Park","Godzilla","Ice Age"], 1, "Jurassic Park"), "Guess the Movie by Emoji 🦖 Hard", "movie quiz"),
"m05": micro(od("HARD", [["🐬","Dolphin"],["🐋","Whale"],["🦇","Bat"],["🦈","Shark"]], 3, "Shark (not a mammal)"), "Which Is NOT a Mammal? 🦈 Hard Quiz", "odd one out"),
"m06": micro(ct("HARD", ["🇳🇬"], ["Ireland","Italy","Nigeria","Ivory Coast"], 2, "Nigeria"), "Guess the Flag 🇳🇬 Hard Level", "flag quiz"),
"m07": micro(gr("HARD", "🕒", "🕞", [3, 2], "Clock at 3:30", 6, 115), "Find the Odd Clock 🕞 Hard Eyes Test", "spot the difference"),
"m08": micro(rd("HARD", "The more you take, the more you leave behind. What am I?", ["Sand","Footsteps","Time","Money"], 1, "Footsteps"), "Hard Riddle 👣 The More You Take", "riddles"),
"m09": micro(math_round("MEDIUM", ["🐶","🐱","🐭"], (9, 2, 6), 3, (-3, 2, 5)), "Emoji Math Puzzle 🐶 Medium", "emoji math"),
"m10": micro(od("HARD", [["🦅","Eagle"],["🦆","Duck"],["🐧","Penguin"],["🦉","Owl"]], 2, "Penguin (can't fly)"), "Which Bird Can't Fly? 🐧 Quiz", "odd one out"),
}
INTRO_M = {'m02': 3.3, 'm08': 4.1}
meta = {}
for k, (spec, title, tag) in M.items():
    spec['intro'] = INTRO_M.get(k, spec['intro'])
    json.dump(spec, open(D / f"{k}.json", "w"), ensure_ascii=False)
    meta[k] = {"title": title + " #Shorts", "description": "One hard question, 5 seconds. Comment your answer (A, B, C or D)! Subscribe for a new quiz every day. #Shorts #Quiz #BrainGames",
               "tags": [tag, "quiz", "brain game", "shorts", "hard quiz", "trivia", "challenge"]}
json.dump(meta, open(D / "meta3.json", "w"), ensure_ascii=False, indent=1)
print(len(M), "micro specs")
