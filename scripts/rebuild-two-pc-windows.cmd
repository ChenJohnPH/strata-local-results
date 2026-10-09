@echo off
setlocal
set VSLANG=1033
set CL=/utf-8
call "C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat"
if errorlevel 1 exit /b 1
"C:\Program Files\Microsoft Visual Studio\2022\Community\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe" --build D:\LLM\two-pc-build-win --target strata -j 4
exit /b %errorlevel%
