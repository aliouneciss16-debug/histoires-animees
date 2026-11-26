#!/bin/bash
# Compilation 16:9 (format long) des quiz difficiles + micro, fond flou, chapitres dans out/marathon_chapters.txt
cd /home/claude/histoires-animees
L=out/marathon_list.txt; : > $L; t=0; : > out/marathon_chapters.txt
for v in v15 v16 v17 v18 v19 v20 v21 v22 v23 v24 v25 v26 m01 m02 m03 m04 m05 m06 m07 m08 m09 m10; do
  d=$(ffprobe -v error -show_entries format=duration -of csv=p=0 exemples/quiz_$v.mp4)
  printf "%d:%02d %s\n" $((${t%.*}/60)) $((${t%.*}%60)) $v >> out/marathon_chapters.txt
  echo "file '/home/claude/histoires-animees/exemples/quiz_$v.mp4'" >> $L
  t=$(python3 -c "print($t+$d)")
done
ffmpeg -y -loglevel error -f concat -safe 0 -i $L -filter_complex "[0:v]split=2[a][b];[a]scale=480:270:force_original_aspect_ratio=increase,crop=480:270,boxblur=8:2,scale=1920:1080[bg];[b]scale=608:1080[fg];[bg][fg]overlay=(W-w)/2:0,format=yuv420p[v]" -map "[v]" -map 0:a -c:v libx264 -crf 24 -preset ultrafast -threads 2 -c:a aac -b:a 160k exemples/quiz_marathon.mp4
echo total $t
