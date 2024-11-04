@echo off
setlocal enabledelayedexpansion
set "INPUT_FOLDER=%USERPROFILE%\Desktop\ffmpeg_test\input"
set "OUTPUT_FOLDER=%USERPROFILE%\Desktop\ffmpeg_test\output"
set "LOGO_FILE=%USERPROFILE%\Desktop\ffmpeg_test\input\logo.png"
set "HEADER_TEXT_FILE=%USERPROFILE%\Desktop\ffmpeg_test\input\header_text.txt"
set "BODY_TEXT_FILE=%USERPROFILE%\Desktop\ffmpeg_test\input\body.txt"
set "AUTHOR_TEXT_FILE=%USERPROFILE%\Desktop\ffmpeg_test\input\author.txt"

echo Input folder: %INPUT_FOLDER%
echo Output folder: %OUTPUT_FOLDER%
echo Logo file: %LOGO_FILE%
echo Header text file: %HEADER_TEXT_FILE%
echo Body text file: %BODY_TEXT_FILE%
echo Author text file: %AUTHOR_TEXT_FILE%

if not exist "%HEADER_TEXT_FILE%" ( echo Error: Header text file not found & goto :end )
if not exist "%BODY_TEXT_FILE%" ( echo Error: Body text file not found & goto :end )
if not exist "%AUTHOR_TEXT_FILE%" ( echo Error: Author text file not found & goto :end )

:: Read the content of the text files
for /f "delims=" %%a in ('type "%HEADER_TEXT_FILE%"') do set "HEADER_TEXT=%%a"
for /f "delims=" %%a in ('type "%BODY_TEXT_FILE%"') do set "BODY_TEXT=%%a"
for /f "delims=" %%a in ('type "%AUTHOR_TEXT_FILE%"') do set "AUTHOR_TEXT=%%a"

:: Escape special characters in the text
set "HEADER_TEXT=%HEADER_TEXT:'=''%"
set "BODY_TEXT=%BODY_TEXT:'=''%"
set "AUTHOR_TEXT=%AUTHOR_TEXT:'=''%"

echo Header text content: "%HEADER_TEXT%"
echo Body text content: "%BODY_TEXT%"
echo Author text content: "%AUTHOR_TEXT%"

for %%i in ("%INPUT_FOLDER%\*.mp4") do (
    set "INPUT_VIDEO=%%i"
    set "OUTPUT_FILE=%OUTPUT_FOLDER%\final_%%~ni.mp4"
    echo Processing: !INPUT_VIDEO!
    
    ffmpeg -i "!INPUT_VIDEO!" -i "%LOGO_FILE%" -filter_complex "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920[bg];^
    [1:v]scale=200:-1[logo];^
    [bg][logo]overlay=20:20[v1];^
    [v1]drawtext=fontfile=/Windows/Fonts/arial.ttf:^
text='%HEADER_TEXT%':^
fontcolor=white:^
fontsize=80:^
box=1:^
boxcolor=black@0.5:^
boxborderw=5:^
x=(w-text_w)/2:^
y=50[v2];^
    [v2]drawtext=fontfile=/Windows/Fonts/arial.ttf:^
text='%BODY_TEXT%':^
fontcolor=white:^
fontsize=64:^
box=1:^
boxcolor=black@0.5:^
boxborderw=5:^
x=(w-text_w)/2:^
y=(h-text_h)/2-200:^
line_spacing=30:^
text_align=center:^
fix_bounds=true[v3];^
    [v3]drawtext=fontfile=/Windows/Fonts/arial.ttf:^
text='%AUTHOR_TEXT%':^
fontcolor=white:^
fontsize=48:^
box=1:^
boxcolor=black@0.5:^
boxborderw=5:^
x=20:^
y=h-text_h-40[v]" -map "[v]" -map 0:a -c:a copy "!OUTPUT_FILE!"
    
    if !errorlevel! neq 0 (
        echo Error processing !INPUT_VIDEO!
    ) else (
        echo Successfully processed !INPUT_VIDEO!
    )
)
:end
pause