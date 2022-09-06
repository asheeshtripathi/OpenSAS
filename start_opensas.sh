#!/bin/bash
tmux new -A -s opensas-server 'cd OpenSAS-dashboard; npm run dev'\; split-window -h "cd Core; python3 HttpsServer.py"
