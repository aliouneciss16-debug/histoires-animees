#!/bin/bash
cd /home/claude/histoires-animees
for v in w01 w02 w03 w04 w05; do
  python src/quiz.py quizzes/$v.json exemples/quiz_$v.mp4
done
echo ALLDONE
