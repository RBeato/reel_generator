@echo off
setlocal enabledelayedexpansion
set "INPUT_FOLDER=%USERPROFILE%\Desktop\ffmpeg_test\input"
set "OUTPUT_FOLDER=%USERPROFILE%\Desktop\ffmpeg_test\output"
set "LOGO_FILE=%USERPROFILE%\Desktop\ffmpeg_test\input\logo.png"
set "HEADER_TEXT_FILE=%USERPROFILE%\Desktop\ffmpeg_test\input\header_text.txt"
set "BODY_TEXT_FILE=%USERPROFILE%\Desktop\ffmpeg_test\input\body.txt"
set "AUTHOR_TEXT_FILE=%USERPROFILE%\Desktop\ffmpeg_test\input\author.txt"

:: Create output folder if it doesn't exist
if not exist "%OUTPUT_FOLDER%" mkdir "%OUTPUT_FOLDER%"

:: File checks
if not exist "%LOGO_FILE%" ( echo Error: Logo file not found & goto :end )
if not exist "%HEADER_TEXT_FILE%" ( echo Error: Header text file not found & goto :end )
if not exist "%BODY_TEXT_FILE%" ( echo Error: Body text file not found & goto :end )
if not exist "%AUTHOR_TEXT_FILE%" ( echo Error: Author text file not found & goto :end )

:: Read the content of the text files (preserving newlines)
set "HEADER_TEXT="
for /f "usebackq delims=" %%a in ("%HEADER_TEXT_FILE%") do set "HEADER_TEXT=!HEADER_TEXT!%%a\n"

set "BODY_TEXT="
for /f "usebackq delims=" %%a in ("%BODY_TEXT_FILE%") do set "BODY_TEXT=!BODY_TEXT!%%a\n"

set "AUTHOR_TEXT="
for /f "usebackq delims=" %%a in ("%AUTHOR_TEXT_FILE%") do set "AUTHOR_TEXT=!AUTHOR_TEXT!%%a\n"

:: Escape special characters in the text
set "HEADER_TEXT=%HEADER_TEXT:'=''%"
set "BODY_TEXT=%BODY_TEXT:'=''%"
set "AUTHOR_TEXT=%AUTHOR_TEXT:'=''%"

:: Create a PowerShell script to wrap text
echo $text = Get-Content "%BODY_TEXT_FILE%" -Raw > "%TEMP%\wrap.ps1"
echo $width = 40 >> "%TEMP%\wrap.ps1"
echo $words = $text -split ' ' >> "%TEMP%\wrap.ps1"
echo $lines = @() >> "%TEMP%\wrap.ps1"
echo $currentLine = '' >> "%TEMP%\wrap.ps1"
echo foreach ($word in $words) { >> "%TEMP%\wrap.ps1"
echo   if ($currentLine.Length + $word.Length + 1 -le $width) { >> "%TEMP%\wrap.ps1"
echo     $currentLine = if ($currentLine) { "$currentLine $word" } else { $word } >> "%TEMP%\wrap.ps1"
echo   } else { >> "%TEMP%\wrap.ps1"
echo     $lines += $currentLine >> "%TEMP%\wrap.ps1"
echo     $currentLine = $word >> "%TEMP%\wrap.ps1"
echo   } >> "%TEMP%\wrap.ps1"
echo } >> "%TEMP%\wrap.ps1"
echo if ($currentLine) { $lines += $currentLine } >> "%TEMP%\wrap.ps1"
echo $lines -join '\n' > "%TEMP%\wrapped.txt" >> "%TEMP%\wrap.ps1"

:: Run the PowerShell script
powershell -ExecutionPolicy Bypass -File "%TEMP%\wrap.ps1"

:: Read the wrapped text
set /p WRAPPED_TEXT=<"%TEMP%\wrapped.txt"

:: FFmpeg command with wrapped text
ffmpeg -i "!INPUT_VIDEO!" -i "%LOGO_FILE%" -filter_complex "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920[bg];[1:v]scale=200:-1[logo];[bg][logo]overlay=20:20[v1];[v1]drawtext=fontfile=/Windows/Fonts/arial.ttf:text='%HEADER_TEXT%':fontcolor=white:fontsize=80:box=1:boxcolor=black@0.5:boxborderw=5:x=(w-text_w)/2:y=50[v2];[v2]drawtext=fontfile=/Windows/Fonts/arial.ttf:text='%WRAPPED_TEXT%':fontcolor=white:fontsize=64:box=1:boxcolor=black@0.7:boxborderw=15:x=(w-text_w)/2:y=(h-text_h)/2:line_spacing=30[v3];[v3]drawtext=fontfile=/Windows/Fonts/arial.ttf:text='%AUTHOR_TEXT%':fontcolor=white:fontsize=48:box=1:boxcolor=black@0.5:boxborderw=5:x=(w-text_w)/2:y=h-text_h-40" -c:a copy "!OUTPUT_FILE!"

:: Clean up temporary files
del "%TEMP%\wrap.ps1"
del "%TEMP%\wrapped.txt"

:end
pause