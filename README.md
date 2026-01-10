# Fuzzy Chips
Want to type faster with fewer errors? You're in the right place.

Fuzzy Chips is a configurable typing utility that expands abbreviations and partial words
based on what you *meant* to type — without worrying about the exact order you pressed your keys.

### Example

| You type | Output |
|----------|--------|
|`th`      |`that`  |
|`ta`      |`at`    |
|`dn`      |`don't` |
|`i`       |`I`     |
|`ths`     |`that's`|

The expansion/correction occurs when you press the space bar. For example `th + space` expands to `that`, and `ta + space` corrects to `at`

The order independent nature of chips allows you to parallelize your key strokes similar to chording if you are familiar.

You can still preserve character entry by hitting `shift+space` instead so if you do `"th" + "shift+space" ` you will be left with `th ` as output


## Core Concepts

### The Buffer
Fuzzy Chips keeps a short buffer of recent characters.
This buffer is cleared or modified based on configurable key events.

If you are experiencing any unusual behaviors, it is likely that your buffer has become desynced from your actual text. In that case, I recommend clearing the buffer.
### Chips
A *chip* is a fuzzy abbreviation that expands into text or key sequences.

The name comes from smashing chord (like in stenography) and snip (short for snippet) together.

Chips:
- are order-independent (`ta` → `at`)
- can be as small as one character (`t` ->`the`)
- can expand into text or explicit key presses (`'s` -> `backspace+'+s+space`)
- expand when you press the space key and don't when you hit shift+space

### Append Characters
Certain characters (like `.`, `!`, `,`) can retroactively attach to the
previous word instead of breaking it.

### Automatic Capitalization 
You can configure certain characters so that the next word after they are typed automatically capitalizes (like `.`,`!`,`?`)

### Toggle Capitalization
You can set a key(defaults to shift) where if you press and realase that key, it will toggle the captlization of the previous word. 

## Installation
```bash
git clone https://github.com/Ben-Collett/fuzzy_chip 
```

## Configuration
Configuration is done through a file called `config.toml`.

The program will first look inside the program’s directory

It will then fall back to the configuration directory location depending on your OS.


On Linux this is usually `~/.config/fuzzy_chip/config.toml`

On Windows: `C:\Users\<username>\AppData\Roaming\fuzzy_chip\config.toml`

The toml config has two main tags: general for all settings, and chips to define chips.

There is an example configuration file in this repo which documents every configuration option: [example_config.toml](example_config.toml)

## Running The Program
From the terminal navigate to the project directory and run 
```bash
python main.py
```
on Linux the user you are running the program as has to be part of the tty group or you can run with root privlages.
```bash
sudo python main.py
```
or use this to add yourself to the tty group
```bash
sudo usermod -a -G tty USER
```

## Acknowledgments

This project vendors a keyboard module from
[Ben-Collett/py_keys](https://github.com/Ben-Collett/py_keys), a fork I
maintain of the original
[boppreh/keyboard](https://github.com/boppreh/keyboard) library.

The `keyboard` project, created by boppreh, enabled reliable cross-platform
keyboard event handling and text injection, and forms a critical foundation
for this software. Without it this program would have stayed Linux only, like it originally was. 

## Additional Resources
I created a program called [missed_chord](https://github.com/Ben-Collett/missed_chord). Originally, it was designed to detect when I missed an opportunity to chord using a CharaChorder. However I added a setting allowing you to detect when you missed an opportunity to us a chip instead of typing out a word.

## Planned Features
-  add support for clearing buffer on mouse events, like left click
-  add control over buffer and config through IPC, so that I can integrate nicer with programs like neovim where modal editing desyncs the buffer.
-  add a way to reload config without restarting the program, either auto-reloading when the config changes or allowing the user to set a reload event in a chip, IPC could also work.
- adding a video/gif to this readme demonstrating fuzzy chips in action
-  X11, non-root, support? requires updating py_keys
-  Mac support? I will need to get access to a Mac before I can do this. Also requires updating py_keys, and handling a supposed segfault that was listed in the keyboard repo

## License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details
