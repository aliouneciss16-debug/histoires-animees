#!/bin/bash
cd /home/claude/histoires-animees
for v in v03 v04 v05 v06 v07 v08 v09 v10 v11 v12 v13 v14; do
  [ -f exemples/quiz_$v.mp4 ] || python src/quiz.py quizzes/$v.json exemples/quiz_$v.mp4
done
echo ALLDONE
