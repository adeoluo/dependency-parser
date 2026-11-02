# Records docs/demo/http.gif from a real run: `vhs docs/demo/http.tape` from the repo root.
Output docs/demo/http.gif
Set Shell "bash"
Set FontSize 15
Set Width 1300
Set Height 440
Set Padding 18
Set Theme "Catppuccin Mocha"
Set TypingSpeed 22ms

Hide
Type `export PS1='$ ' && uv sync -q && source .venv/bin/activate` Enter
Sleep 2s
Type `python -m dependency_parser serve --port 18309 >/dev/null 2>&1 &` Enter
Sleep 2s
Sleep 12s
Type `clear` Enter
Sleep 1s
Show
Type `curl -s localhost:18309/health; echo` Enter
Sleep 1.5s
Type `curl -s localhost:18309/parse -d '{"tokens": [{"form": "the", "pos": "DET"}, {"form": "model", "pos": "NOUN"}, {"form": "learns", "pos": "VERB"}]}' | jq -c '.arcs[] | {form, head_form, deprel}'` Enter
Sleep 3.5s
Hide
Type `kill %1` Enter
Sleep 1s
