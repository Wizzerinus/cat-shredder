## Settings file

Read from `user/settings.json`. The following values are the defaults: 

```python
{
    "stretched-screen": false,
    "controls": {
        "move_forward": "arrow_up",
        "move_backwards": "arrow_down",
        "move_left": "arrow_left",
        "move_right": "arrow_right",
        "jump": "control",
        "sprint": "shift",
        "open_chat": "t",
        "make_screenshot": "f12",
        "crane_grab": "control"
    },
    # Options are Toggle, Auto, and Hold
    "sprintMode": "Toggle",
    # glitchy, do not recommend
    "sprintFOVChanges": false,
    # can be set to 0 to disable music/sfx/both
    "musicVolume": 0.4,
    "sfxVolume": 0.6,
    "frameRateMeter": false,
    "fullscreen": false,
    "toonChatSounds": true,
    # Set to 5/6 of the screen's resolution by default (uses 1366x768 if screen resolution cannot be determined)
    "resolution": [WindowWidth, WindowHeight],
    "antialiasing": 0
}
```

Only the changed settings will have to be overridden in the file. No GUI yet.
