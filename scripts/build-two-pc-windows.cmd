@echo off
setlocal
call "C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat"
if errorlevel 1 exit /b 1
set "TASK_SOURCE=D:\LLM\Strata-two-pc-source\NTRYourWaifu-Strata-7add08d"
set "TASK_CMAKE=C:\Program Files\Microsoft Visual Studio\2022\Community\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe"
set "TASK_NINJA=C:\Program Files\Microsoft Visual Studio\2022\Community\Common7\IDE\CommonExtensions\Microsoft\CMake\Ninja\ninja.exe"
"%TASK_CMAKE%" -G Ninja -S "%TASK_SOURCE%" -B D:\LLM\two-pc-build-win ^
 -DCMAKE_BUILD_TYPE=Release -DSTRATA_ENABLE_CUDA=ON -DSTRATA_BUILD_TESTS=OFF ^
 -DSTRATA_PORTABLE=ON -DCMAKE_CUDA_RUNTIME_LIBRARY=Shared -DCMAKE_CUDA_ARCHITECTURES=89 ^
 "-DCMAKE_CUDA_COMPILER=C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.6\bin\nvcc.exe" ^
 "-DCMAKE_MAKE_PROGRAM=%TASK_NINJA%" "-DSTRATA_GGML_DIR=%TASK_SOURCE%\third_party\llama.cpp"
if errorlevel 1 exit /b 1
"%TASK_CMAKE%" --build D:\LLM\two-pc-build-win --target strata -j 6
exit /b %errorlevel%
