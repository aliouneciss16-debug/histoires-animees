"""w01..w05 : quiz 5 manches (~55-60 s), formats variés, réponses vérifiées à la main."""
import json
from pathlib import Path
D = Path(__file__).parent
exec(open(D / "batch2.py").read().split("V = {")[0])
SC5 = lambda a: [[f"5/5  {a}", "🏆"], ["3-4  Nice job", "👏"], ["0-2  Try again!", "🔁"]]
def cap(level, flag, items, ans, name):
    return {"kind": "emoji", "level": level, "q": "What is the capital?", "emoji": [flag], "items": items, "answer": ans, "answer_text": name}
H = lambda a, b: [a, b]
W = {
"w01": ("5 Movies by Emoji 🎬 Can You Get 5/5?", "movie quiz", H("5 MOVIES", "Easy to HARD!"), "🎬", "Cinema king",
  [mv("EASY", ["🦁","👑"], ["The Lion King","Madagascar","Tarzan","Bambi"], 0, "The Lion King"),
   mv("EASY", ["🕷️","🦸"], ["Batman","Spider-Man","Venom","Ant-Man"], 1, "Spider-Man"),
   mv("MEDIUM", ["🦈","🏖️"], ["Titanic","Frozen","Cars","Jaws"], 3, "Jaws"),
   mv("MEDIUM", ["🧊","👸"], ["Tangled","Brave","Frozen","Moana"], 2, "Frozen"),
   mv("HARD", ["🕰️","🚗","⚡"], ["Tenet","Back to the Future","Cars","Speed"], 1, "Back to the Future")], 3.0),
"w02": ("Guess the Capital 🌍 5 Flags Challenge", "capital cities", H("5 CAPITALS", "Easy to HARD!"), "🌍", "Geography pro",
  [cap("EASY", "🇫🇷", ["Lyon","Paris","Nice","Marseille"], 1, "Paris"),
   cap("EASY", "🇯🇵", ["Osaka","Kyoto","Tokyo","Seoul"], 2, "Tokyo"),
   cap("MEDIUM", "🇦🇺", ["Sydney","Melbourne","Perth","Canberra"], 3, "Canberra"),
   cap("MEDIUM", "🇨🇦", ["Toronto","Ottawa","Vancouver","Montreal"], 1, "Ottawa"),
   cap("HARD", "🇧🇷", ["Rio de Janeiro","Sao Paulo","Brasilia","Salvador"], 2, "Brasilia")], 2.6),
"w03": ("5 Riddles 🧩 Only Geniuses Get 5/5", "riddles", H("5 RIDDLES", "Easy to HARD!"), "🧩", "Riddle master",
  [rd("EASY", "What has keys but can't open locks?", ["A door","A piano","A map","A clock"], 1, "A piano"),
   rd("EASY", "What gets wetter the more it dries?", ["A sponge","Rain","A towel","A river"], 2, "A towel"),
   rd("MEDIUM", "What building has the most stories?", ["A hotel","A school","A castle","A library"], 3, "A library"),
   rd("MEDIUM", "What has words but never speaks?", ["A book","A phone","A radio","A parrot"], 0, "A book"),
   rd("HARD", "What begins with T, ends with T, and has T in it?", ["A toast","A ticket","A teapot","A tent"], 2, "A teapot")], 3.3),
"w04": ("Guess the Country 🗽 5 Symbols Test", "geography quiz", H("5 COUNTRIES", "Easy to HARD!"), "🗺️", "World explorer",
  [ct("EASY", ["🗽"], ["Canada","France","USA","Brazil"], 2, "USA"),
   ct("EASY", ["🗻"], ["China","Japan","Korea","Peru"], 1, "Japan"),
   ct("MEDIUM", ["🗿"], ["Mexico","Peru","Fiji","Chile"], 3, "Chile (Easter Island)"),
   ct("MEDIUM", ["🦙"], ["Kenya","India","Peru","Spain"], 2, "Peru"),
   ct("HARD", ["🇳🇿"], ["Australia","Fiji","New Zealand","UK"], 2, "New Zealand")], 2.6),
"w05": ("Emoji Math 🧮 5 Puzzles, Easy to HARD", "emoji math", H("5 PUZZLES", "Easy to HARD!"), "🧮", "Math genius",
  [math_round("EASY", ["🐶","🐱"], (6, 3, 0), 2),
   math_round("EASY", ["🍩","🍪"], (5, 2, 0), 1),
   math_round("MEDIUM", ["⚽","🏀","🎾"], (7, 2, 4), 3),
   math_round("MEDIUM", ["🍓","🍋","🍇"], (8, 3, 5), 0),
   math_round("HARD", ["🥕","🍍","🥥"], (12, 5, 3), 2, (-4, 3, 6))], 2.5),
}
DESC = "5 questions, from Easy to HARD. Comment your score (like 4/5)! Share it with a friend who thinks they're smart, and subscribe for a new quiz every day. #Shorts #Quiz #BrainGames"
meta = {}
for k, (title, tag, hook, he, sc, rounds, intro) in W.items():
    json.dump({"intro": intro, "brand": "QUICK QUIZ", "hook": hook, "hook_emoji": he, "rounds": rounds, "scores": SC5(sc)}, open(D / f"{k}.json", "w"), ensure_ascii=False)
    meta[k] = {"title": title[:95] + " #Shorts", "description": DESC, "tags": [tag, "quiz", "brain game", "shorts", "trivia", "challenge", "5 questions"]}
json.dump(meta, open(D / "meta4.json", "w"), ensure_ascii=False, indent=1)
print(len(W), "specs 5 manches")
