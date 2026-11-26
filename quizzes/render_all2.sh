#!/bin/bash
cd /home/claude/histoires-animees
for v in v15 v16 v17 v18 v19 v20 v21 v22 v23 v24 v25 v26; do
  python src/quiz.py quizzes/$v.json exemples/quiz_$v.mp4
done
echo ALLDONE
