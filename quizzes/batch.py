"""Génère les specs JSON des 12 quiz (v03..v14) + métadonnées YouTube. Réponses vérifiées à la main."""
import json
from pathlib import Path
SC = lambda a, b: [[f"3/3  {a}", "🏆"], ["2/3  Nice job", "👏"], [f"0-1  {b}", "🔁"]]
def mv(e, items, ans, name): return {"kind": "emoji", "q": "Which movie is this?", "emoji": e, "items": items, "answer": ans, "answer_text": name}
def ct(e, items, ans, name): return {"kind": "emoji", "q": "Which country is this?", "emoji": e, "items": items, "answer": ans, "answer_text": name}
def rd(q, items, ans, name): return {"kind": "emoji", "q": q, "emoji": ["🤔"], "ey": 640, "items": items, "answer": ans, "answer_text": name}
def gr(base, odd, pos, name, rows=5, cols=5): return {"kind": "grid", "q": "Find the odd emoji!", "rows": rows, "cols": cols, "base": base, "odd": odd, "pos": pos, "answer_text": name}
def od(items, ans, name): return {"kind": "odd", "q": "Which one is the odd one out?", "items": items, "answer": ans, "answer_text": name}
V = {
"v03": ("Guess the Movie by Emoji 🎬 Part 2", "Can you guess these 3 movies from emojis?", "movie quiz",
  ["3 MORE MOVIES", "Guess them by emoji!"], "🍿", SC("Movie fan", "Watch more!"),
  [mv(["🧊","👸","❄️"], ["Frozen","Moana","Tangled","Brave"], 0, "Frozen"),
   mv(["🐠","🔍"], ["The Little Mermaid","Finding Nemo","Shark Tale","Luca"], 1, "Finding Nemo"),
   mv(["🧙","⚡","👓"], ["Harry Potter","Narnia","Merlin","Matrix"], 0, "Harry Potter")]),
"v04": ("Guess the Country by Flag 🌍", "Can you name these 3 flags?", "flag quiz",
  ["3 FLAGS", "Name the country!"], "🌍", SC("Geography pro", "Study maps!"),
  [ct(["🇧🇷"], ["Portugal","Brazil","Mexico","Argentina"], 1, "Brazil"),
   ct(["🇯🇵"], ["South Korea","China","Japan","Vietnam"], 2, "Japan"),
   ct(["🇨🇦"], ["Canada","Austria","Peru","Switzerland"], 0, "Canada")]),
"v05": ("Find the Odd Animal 🐶 Eagle Eyes Test", "Spot the different animal in 5 seconds!", "spot the difference",
  ["EAGLE EYES?", "Find the odd animal!"], "🦅", SC("Eagle eyes", "Look closer!"),
  [gr("🐶","🐺",[1,3],"Wolf"), gr("🐼","🐻",[4,0],"Brown bear"), gr("🐱","🐯",[2,2],"Tiger")]),
"v06": ("Find the Odd Fruit 🍎 Can You Spot It?", "Spot the different fruit in 5 seconds!", "find the odd one",
  ["SHARP EYES?", "Find the odd fruit!"], "🍎", SC("Sharp eyes", "Try again!"),
  [gr("🍎","🍅",[0,4],"Tomato"), gr("🍊","🍑",[3,3],"Peach"), gr("🍓","🍒",[1,1],"Cherries")]),
"v07": ("Spot the Odd One Out 👀 3 Levels", "Level up your eyes! 3 levels of spotting.", "visual puzzle",
  ["3 LEVELS", "Find the odd emoji!"], "👀", SC("Hawk vision", "Practice more!"),
  [gr("🚗","🚓",[2,0],"Police car"), gr("🦆","🐤",[4,4],"Baby chick"), gr("⭐","🌟",[0,2],"Glowing star")]),
"v08": ("Odd One Out Quiz 🧠 Easy Level", "Which one doesn't belong? Easy level!", "odd one out",
  ["ODD ONE OUT", "Which one is different?"], "🧠", SC("Big brain", "Think again!"),
  [od([["🐟","Fish"],["🐙","Octopus"],["🦀","Crab"],["🐘","Elephant"]], 3, "Elephant (lives on land)"),
   od([["🌙","Moon"],["⭐","Star"],["☀️","Sun"],["🌧️","Rain"]], 3, "Rain (not in space)"),
   od([["🚗","Car"],["🚌","Bus"],["✈️","Plane"],["🏠","House"]], 3, "House (not a vehicle)")]),
"v09": ("Odd One Out Quiz 🤯 Medium Level", "Which one doesn't belong? Medium level!", "brain game",
  ["MEDIUM LEVEL", "Which one is different?"], "🤯", SC("Genius", "Try again!"),
  [od([["🦅","Eagle"],["🦉","Owl"],["🐕","Dog"],["🐦","Bird"]], 2, "Dog (not a bird)"),
   od([["👕","T-shirt"],["👖","Jeans"],["🧦","Socks"],["🍎","Apple"]], 3, "Apple (not clothing)"),
   od([["📱","Phone"],["💻","Laptop"],["🖥️","Computer"],["🍕","Pizza"]], 3, "Pizza (not a device)")]),
"v10": ("Guess the Movie by Emoji 🎬 Part 3", "3 more movies to guess from emojis!", "movie quiz",
  ["MOVIE TIME", "Guess by emoji!"], "🎥", SC("Cinema king", "Watch more!"),
  [mv(["🦈","🏖️"], ["Jaws","Moana","Aquaman","Nemo"], 0, "Jaws"),
   mv(["🤠","🚀","🧸"], ["Cars","Toy Story","Up","Coco"], 1, "Toy Story"),
   mv(["🦇","🌃"], ["Superman","Spider-Man","Batman","Aquaman"], 2, "Batman")]),
"v11": ("Guess the Country by Emoji 🌎", "Guess the country from 2 emojis!", "geography quiz",
  ["GUESS THE COUNTRY", "From emojis only!"], "🌎", SC("World traveler", "Pack your bags!"),
  [ct(["🍕","🍝"], ["France","Italy","Spain","Greece"], 1, "Italy"),
   ct(["🦘","🏄"], ["Australia","Brazil","Kenya","India"], 0, "Australia"),
   ct(["🐼","🥢"], ["Japan","Thailand","China","Peru"], 2, "China")]),
"v12": ("Can You Solve These 3 Riddles? 🤔", "3 riddles. 5 seconds each. Can you solve them?", "riddles",
  ["3 RIDDLES", "5 seconds each!"], "🤔", SC("Riddle master", "Think harder!"),
  [rd("What has hands but can't clap?", ["A clock","A fish","A book","A river"], 0, "A clock"),
   rd("What gets wetter as it dries?", ["A sponge","A towel","Soap","A cloud"], 1, "A towel"),
   rd("What has an eye but can't see?", ["A needle","A rock","A spoon","A chair"], 0, "A needle")]),
"v13": ("3 Hard Riddles 🧩 Only Smart People Solve", "3 more riddles! Comment your score.", "brain teaser",
  ["3 NEW RIDDLES", "Can you solve them?"], "🧩", SC("Super smart", "Try again!"),
  [rd("What has a neck but no head?", ["A bottle","A cloud","A giraffe","A river"], 0, "A bottle"),
   rd("What can you catch but not throw?", ["A ball","A cold","A mountain","A rainbow"], 1, "A cold"),
   rd("What goes up but never comes down?", ["A balloon","A bird","Your age","A kite"], 2, "Your age")]),
"v14": ("Mixed Quiz Challenge 🎯 Movies, Eyes & Logic", "Movie, spot-it and odd-one-out in one quiz!", "mixed quiz",
  ["MIXED CHALLENGE", "Movie. Eyes. Logic."], "🎯", SC("Quiz champion", "Play again!"),
  [mv(["🦁","👑"], ["Zootopia","The Lion King","Madagascar","Tarzan"], 1, "The Lion King"),
   gr("🙂","🙃",[2,3],"Upside-down face"),
   od([["🍎","Apple"],["🍌","Banana"],["🥕","Carrot"],["🍇","Grapes"]], 2, "Carrot (a vegetable)")]),
}
meta = {}
for k, (title, desc, tag, hook, he, sc, rounds) in V.items():
    json.dump({"brand": "QUICK QUIZ", "hook": hook, "hook_emoji": he, "rounds": rounds, "scores": sc},
              open(Path(__file__).parent / f"{k}.json", "w"), ensure_ascii=False)
    meta[k] = {"title": title + " #Shorts", "description": desc + " Comment your score! #Shorts #Quiz #BrainGames",
               "tags": [tag, "quiz", "brain game", "shorts", "trivia", "challenge", "riddle"]}
json.dump(meta, open(Path(__file__).parent / "meta.json", "w"), ensure_ascii=False, indent=1)
print(len(V), "specs")
