START "python.exe" "launch.py"  -u aaa -p 111 & 
ping localhost -n 3 >nul
START "python.exe" "launch.py"  -u bbb -p 111 & 
ping localhost -n 3 >nul
START "python.exe" "launch.py"  -u ccc -p 111 & 
ping localhost -n 3 >nul
START "python.exe" "launch.py"  -u ddd -p 111 & 
ping localhost -n 3 >nul