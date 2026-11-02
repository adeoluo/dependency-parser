# Records docs/demo/parse.gif from a real run: `vhs docs/demo/parse.tape` from the repo root.
Output docs/demo/parse.gif
Set Shell "bash"
Set FontSize 15
Set Width 1300
Set Height 440
Set Padding 18
Set Theme "Catppuccin Mocha"
Set TypingSpeed 22ms

Hide
Type `export PS1='$ ' && uv sync -q && source .venv/bin/activate && clear` Enter
Sleep 10s
Show
Type `python -m dependency_parser parse the/DET engineer/NOUN trains/VERB the/DET model/NOUN` Enter
Sleep 5s
