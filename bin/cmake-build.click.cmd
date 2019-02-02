@echo off
REM ==========================================================================
REM CMAKE-BUILD
REM ==========================================================================

setlocal
set HERE=%~dp0
if not defined PYTHON   set PYTHON=python

%PYTHON% %HERE%cmake-build.click %*
