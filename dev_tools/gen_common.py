from config_generator import Builder, GenDict, build_python, build_toml
from config_generator.gen_types import GenStr, GenCustom
from pathlib import Path


def make_builder() -> Builder:
    spacing_type = GenCustom(
        parse_command='SpacingType.safe_from_str($value, SpacingType.NORMAL)', config_value=GenStr("normal"), code_type="SpacingType")

    casing_type = GenCustom(
        parse_command='Casing.safe_from_str($value, Casing.NORMAL)', config_value=GenStr("normal"), code_type="Casing")

    chunking_type = GenCustom(
        parse_command='ChunkingType.safe_from_str($value, ChunkingType.LAST)', config_value=GenStr("last"), code_type="ChunkingType")
    import_statements = [
        "from spacing_type import SpacingType",
        "from casing import Casing",
        "from chunking import ChunkingType",
        "from config_support import load_chips",
        "from fuzzy_events import parse_on_press, parse_on_toggle, parse_while_down, parse_on_mouse_button_down",

    ]
    # Initialize builder with TOML formatting settings matching the example
    builder = Builder(
        code_indent="    ",
        config_indent="  ",
        config_new_line="\n",
        code_new_line="\n",
        config_comment_sep=" ",
        import_statements=import_statements
    )

    # Top-level note comment
    builder.comment(" NOTE: all settings besideds the chips section at the bottom of the file are set equal to their default behavior so if you want the described functionality you don't need  to override that key")

    # [general] section
    builder.new_line().add_section("general")
    # capitalize_after
    builder.comment(
        " if the previous word ends with one of these characters then the current word will be capitalized once you hit space")
    builder.comment(" set to an empty list to avoid any auto captlizing")
    builder.comment(" capitalize_after = []")
    builder.add_list("capitalize_after", [
                     GenStr("."), GenStr("!"), GenStr("?")])
    builder.new_line()

    # append_chars and auto_append
    builder.comment(
        " append_chars have special behavior depending on the setting of auto_append")
    builder.comment(
        " if true when pressing an append char it will be automatically appended to the previous word in the buffer and white space will be restored")
    builder.comment(
        " if false then it won't append until you press space and will fail to do so if you press shift+space")
    builder.comment(
        " you probably don't want to auto append when working with shells and programming")
    builder.add_list("append_chars", [GenStr("."), GenStr("!"), GenStr(
        "?"), GenStr(","), GenStr(";"), GenStr(")"), GenStr("]"), GenStr("}")])
    builder.add_bool("auto_append", False)
    builder.new_line()
    builder.comment(
        " the maximum capacity for the internal buffer in fuzzy chips")
    builder.comment(" defaults to 500 or that is to say up to the last 500")
    builder.comment(
        " key events are stored if you set it to 0 or less then the buffer will have unlimited capacity")
    builder.comment(
        " but if you do that and never clear the buffer it is a memory leak")
    builder.add_int("buffer_size", 500)
    builder.new_line()

    builder.comment(
        " the following 4 sections define allow you to define actions based on certain keyboarnd and mouse conditions.")
    builder.comment(
        " NOTE: in toml any key that has a special symbol like a + needs to be in quotes")
    builder.comment(
        " these are the available commands: clear_buffer, clear_buffer_ipc_safe, delete_word, toggle_casing, expand")
    builder.comment(
        " this is also the order of precedence if a binding would have both deleted a word and expanded an expression delete_word will run expand will not")
    builder.comment(
        " clear buffer clears the internal buffer used by fuzzy chips")
    builder.comment(
        " clear buffer ipc safe clears the internal buffer used by fuzzy chips unless it was just set via ipc")

    builder.comment(
        " delete_word backspaces the previous/current word based on the buffer")

    builder.comment(" toggle_case toggles the previous word between upper and lowwer case unless there is a non leading underscore then it will toggle the captlization of the whole word")
    builder.comment(
        " expand: expands the current word based on the buffer also handles appending punctuation if autoexpand is false")

    builder.new_line()
    builder.comment(
        " the on_press section triggers when an exact hotkey is pressed that is to say")
    builder.comment(
        " if you put space as a key it will trigger if you press space but not if you press shift+space unless that is explicitly also a key")
    builder.add_custom_section("on_press", "parse_on_press($map)", GenDict)
    builder.add_str("space", "expand")
    builder.comment(
        ' enter = "expand" # expand when you preess enter/return, annoying for coding.')
    builder.comment(
        ' "shift+space" = "expand" # expand when you press shift+space, that way it is harder to accidentally expand')
    builder.add_str("shift+backspace", "delete_word")
    builder.comment(" these two should probably always be set to this")
    builder.add_str("up", "clear_buffer_ipc_safe")
    builder.add_str("down", "clear_buffer_ipc_safe")
    builder.new_line()

    builder.comment(
        ' on toggle triggers when a key is pressed and then released without pressing any keys in between.')
    builder.comment(
        ' this must be a single key like shift or alt not a hotkey')
    builder.add_custom_section("on_toggle", "parse_on_toggle($map)", GenDict)
    builder.add_str("shift", "toggle_case")
    builder.new_line()

    builder.comment(
        ' while_down triggers whenever you press any key while one of these keys are down')
    builder.comment(
        ' can only be applied to ctrl, alt, and windows')
    builder.comment(
        ' fair warning to keyd users if you use overload(alt,whatever) with keyd it will also press control')
    builder.comment(
        ' when you release the key without pressing any other keys. That is to avoid triggering a hotkey in firefox I think.')
    builder.add_custom_section("while_down", "parse_while_down($map)", GenDict)
    builder.add_str("windows", "clear_buffer")
    builder.add_str("ctrl", "clear_buffer")
    builder.add_str("alt", "clear_buffer")
    builder.new_line()

    builder.comment(
        ' triggers when a certain mouse button is pressed, left, right, X1, X2, maybe middle or wheel TODO: look into wheel/middle')

    builder.comment(
        ' in any case the main functionality you would want with this is clearing the buffer when you left click')
    builder.add_custom_section(
        "on_mouse_button_down", "parse_on_mouse_button_down($map)", GenDict)
    builder.add_str("left", "clear_buffer")
    builder.new_line()

    # [chunking] section
    builder.add_section("chunking")
    builder.comment(" none, last, all")
    builder.comment(" all will expand all chunks in the last word")
    builder.comment(
        " example: t-tg-th->the-thing-that, assuming t->the tg->thing th->that")

    builder.comment(" last will only expand the last word and is the default behavior, although witching to all can be faster for certain workflows, it is easier to mess up using")
    builder.comment(
        " none of disable chunking as it can get in the way if you type a lot of equations")
    # chunking_type uses ChunkingType.safe_from_str when loaded, store as string
    builder.add_field("chunking_type", chunking_type)
    builder.comment(" will only expand chunk that are new so if where in all mode and you typed \"t-tg-th\" and you did a non-expanding space(shift+space by default) then backspaced back and add -ab-tg only the last part would expand")
    builder.comment(" so t-tg-th-about-again")
    builder.comment(
        " this setting is generally advisiable if your using a external program or plugin for your text editor to sync the buffer with your current text")
    builder.add_bool("new_chunks_only", False)
    builder.comment(
        " non alphanumeric characters treated as alphanumeric characters for chunking, ' that way contractions like that's wont expand")

    builder.comment(
        " if you are using things like code casing  likely want _ in the chunking_ignore section")
    builder.comment(" while chunking with _ works fine in the forward direction it is not as effective for editing snake case code in post as dedicated code casing and new casing modes")
    builder.add_list("chunking_ignore", [GenStr("'"), GenStr("_")])

    # [rare] section
    builder.new_line().add_section("rare")
    builder.comment(" these settings can be changed but rarely should")
    builder.comment(
        " passes through the captlization modifier of the last word so if it is 'hi.' the next word will be captlized")
    builder.comment(" where as 'hi' it will not")
    builder.add_list("captlize_passthrough", [
                     GenStr('"'), GenStr("'"), GenStr("`")])

    # [code] section
    builder.new_line().add_section("code")
    builder.comment(
        " WARNING: these setting does nothing when not in normal casing mode.")
    builder.comment(" normal -> best for natural language")
    builder.comment(
        " code -> nice for coding breaks some natural language use cases")
    builder.comment(
        " new -> also nice for coding work well with fuzzychips and with chording systems.")
    builder.new_line()
    builder.comment(
        " if code spacing is used then the casing of the current word is detected and used")
    builder.comment(
        " so if you have something in cammel case like \"helloT\" and you press space it would expand to \"helloThe\"")
    builder.comment(
        " this breaks the use case like this tH would normally expand to something like That but instead would expand to tHere")
    builder.comment(
        " this allows you to modify in the middle of words as well and also supports snake casing, when spacing after typing something at the")
    builder.comment(
        " end of a snake cased variable it will type an _ until you hit space again")
    builder.new_line()
    builder.comment(
        " so hello_there+space becomes hello_there_ if you do space again it becomes \"hello_there \"")
    builder.comment(" if you press space when doing cammel case if it wouldn't change anything then it will just put a space between the words or afterwards if it would expand something then it will expand and not insert a space")
    builder.comment(
        " propercase and UPPER_SNAKE_CASE are also detected and supported kebab is not currently")
    builder.new_line()
    builder.comment(
        " new spacing works similar to code spacing except it uses only new characters typed and will treat the new characters typed as a whole word")
    builder.comment(" so if you have hello_there_person")
    builder.comment(
        " and you type hello_th<t space>ere_person it will expand to hello_th_the_ere_person")
    builder.comment(
        " cammel,snake,UPPER_SNAKE,ProperCase, normal are all supported")
    # spacing_type uses SpacingType.safe_from_str when loaded
    builder.add_field("spacing_type", spacing_type)
    builder.new_line()
    builder.comment(
        " this setting only applies to new mode, everything typed except when detected otherwise will be assumed to be in this mode")
    builder.comment(
        " ex: if it is set to cammel casing then \"hello_there<t space>\" will still expand to hello_there_the")
    builder.comment(" however \"hello<t space>\" will expand to helloThe")
    builder.comment(" values snake, camel, upper snake, normal")
    # assumed_casing uses Casing.safe_from_str when loaded
    builder.add_field("assumed_casing", casing_type)
    builder.new_line()
    builder.comment(
        " space on new is when true measn that if nothing chegss as a result of hitting space when using new mode it will just space forward")
    builder.comment(
        " the only real reason to them this to false is if you are using charachroder with autocorrect it can be convenient since you would have to use")
    builder.comment(
        " two spaces to move forward instead of one when dealing with code so autocorrect won't backspace your regular text")
    builder.add_bool("space_on_new", True)

    # [ipc] section
    builder.new_line().add_section("ipc")
    builder.comment(" uses a tcp socket")
    builder.add_int("port", 8765)
    builder.add_str("host", "127.0.0.1",
                    comment="local host, I can't think of a reason to change this but it's here")
    builder.new_line()
    builder.comment(
        " commands that can be sent through ipc, all disabled by default")
    builder.comment(
        " works nicely with this neovim plugin: https://github.com/Ben-Collett/chipped.nvim")
    builder.comment(
        " do keep in mind any program can access these commands even a malicouse one(theoretically atleast)")
    builder.comment(
        " highly unlikely for a attack area since most commands can't really be used in a very harmful way for most users")
    builder.comment(
        " plus pretty much no one is using fuzzy chips so there is no inscentive to try to exploit it.")
    builder.new_line()

    # All entries commented out, empty list
    # None = newline
    comments = [
        " With thee commands a prakster could theortically prevent you from typing in normal mode with this I guess",
        " though why they would I don't know, and it is pretty pointless if you have a chip set up to quit the program",
        None,
        ' "mc",  # activate normal casing',
        ' "sc",  # activate snake_casing',
        ' "pm",  # activate ProperCasing',
        ' "cm",  # activate camelCasing',
        ' "us",  # activate UPPER_SNAKE_CASING',
        " I guess a bad actor could force you to type the wrong chip if they had these commands...",
        ' "cb",  # clear buffer',
        ' "sm",  # set main buffer',
        ' "sr",  # set right buffer',
        None,
        " WARNING: the below are more exploitable",
        " for example I could change your config file and change chips to something else if I where a malisouce actor with rl and rs",
        " like if you used a crypto wallett or something like that it could be bad.",
        None,
        " although a bad actor with the remote code execution required to do that could probably do worse...",
        ' "rl",  # reload config'
        ' "rs",  # restart program'
    ]
    builder.add_comment_list("ipc_enabled_commands",
                             comments, value_type=GenStr)

    # [chips] section
    builder.new_line().add_custom_section("chips", "load_chips($map)", GenDict)
    builder.comment(
        " chips can be a list of keys or a string of characters, if its a list each element must be a valid key name")
    builder.comment(" if it is a string then space will be automatically added at the end when triggering the chip this is not true for list in that case you must end with a space key if you want to space")

    # Example chips with lists
    builder.comment(
        " examples using a list very nice for after you type something like th for that and then hitting 's to make that's")
    builder.add_list("'s", [GenStr("backspace"), GenStr(
        "'"), GenStr("s"), GenStr("space")])
    builder.add_list("n't", [GenStr("backspace"), GenStr(
        "n"), GenStr("'"), GenStr("t"), GenStr("space")])
    builder.add_list("'l", [GenStr("backspace"), GenStr(
        "'"), GenStr("l"), GenStr("l"), GenStr("space")])
    builder.new_line()

    # Command chips
    builder.add_list("rl", [GenStr("reload_config")])
    builder.add_list("qui", [GenStr("quit")])
    builder.add_list("ras", [GenStr("restart")])
    builder.add_list("cl", [GenStr("clear_buffer")])
    builder.new_line()

    # Casing mode chips
    builder.add_list("-", [GenStr("kebab-case-mode")])
    builder.add_list("nm", [GenStr("normal case mode")])
    builder.add_list("_", [GenStr("snake_case_mode")])
    builder.add_list("__", [GenStr("UPPER_SNAKE_CASE_MODE")])
    builder.add_list("pm", [GenStr("ProperCaseMode")])
    builder.add_list("cmm", [GenStr("camelCaseMode")])
    builder.new_line()

    # String chips
    builder.add_str("t,", "this is dumb, but legal and useful for testing",
                    comment=" just keep in mind if you do this and you have auto append on and , set to append you better hit t before ,")
    builder.comment(
        " you can use to to make typing a word order independent, example ta = at or toni = into")
    builder.add_str("at", "at")
    builder.add_str("it", "it")
    builder.add_str("in", "in")
    builder.new_line()
    builder.comment(
        " I on it's own is always captlized(if your not doing coding/math)")
    builder.add_str("i", "I")
    builder.comment(
        " abbreviations for speed, they can even be a single letter!")
    builder.add_str("d", "and")
    builder.add_str("r", "are")
    builder.comment(" or reuse letters")
    builder.add_str("ppl", "people")
    builder.comment(" you can also map to multiple words")
    builder.add_str("mws", "this is multiple words isn't that cool")
    builder.comment(
        " keep in mind since order doesn't matter you probably don't want to overried on to be on since it is the same as no")
    builder.add_str("o", "on")
    builder.add_str("n", "no")
    builder.new_line()
    builder.comment(
        " You can use non-letters just keep in mind your ignored prefixes and postfixes")
    builder.add_str("w'", "we're")
    builder.comment(
        " =================== nothing new below this point just more examples ===============================")
    builder.add_str("is", "is")
    builder.add_str("of", "of")
    builder.add_str("to", "to")
    builder.add_str("so", "so")
    builder.add_str("be", "be")
    builder.add_str("into", "into")
    builder.add_str("do", "do")
    builder.add_str("us", "us")
    builder.add_str("an", "an")
    builder.add_str("by", "by")
    builder.add_str("up", "up")
    builder.add_str("or", "or")
    builder.add_str("ag", "anything")
    builder.add_str("go", "go")
    builder.add_str("he", "he")
    builder.add_str("me", "me")
    builder.add_str("if", "if")
    builder.add_str("we", "we")
    builder.add_str("as", "as")
    builder.add_str("am", "am")
    builder.add_str("my", "my")
    builder.add_str("his", "his")
    builder.add_str("now", "now")
    builder.add_str("y", "you")
    builder.add_str("f", "for")
    builder.add_str("g", "get")
    builder.add_str("c", "can")
    builder.add_str("b", "be")
    builder.add_str("t", "the")
    builder.add_str("tt", "the")
    builder.add_str("js", "just")
    builder.add_str("nv", "never")
    builder.add_str("th", "that")
    builder.add_str("bu", "but")
    builder.add_str("ar", "are")
    builder.add_str("nt", "not")
    builder.add_str("yr", "your")
    builder.add_str("al", "all")
    builder.add_str("hv", "have")
    builder.add_str("aw", "was")
    builder.add_str("ts", "this")
    builder.add_str("wt", "what")
    builder.add_str("ty", "they")
    builder.add_str("wn", "when")
    builder.add_str("kw", "know")
    builder.add_str("oe", "one")
    builder.add_str("tr", "there")
    builder.add_str("lk", "like")
    builder.add_str("wi", "will")
    builder.add_str("ig", "it's")
    builder.add_str("dn", "don't")
    builder.add_str("im", "I'm")
    builder.add_str("iv", "I've")
    builder.add_str("lf", "life")
    builder.add_str("tm", "time")
    builder.add_str("ow", "who")
    builder.add_str("ou", "out")
    builder.add_str("et", "them")
    builder.add_str("ab", "about")
    builder.add_str("mr", "more")
    builder.add_str("yo", "you're")
    builder.add_str("hd", "had")
    builder.add_str("ur", "our")
    builder.add_str("ly", "only")
    builder.add_str("hw", "how")
    builder.add_str("tg", "thing")
    builder.add_str("eg", "enough")
    builder.add_str("se", "see")
    builder.add_str("rw", "were")
    builder.add_str("lv", "live")
    builder.add_str("ov", "love")
    builder.add_str("jt", "than")
    builder.add_str("ei", "their")
    builder.add_str("bj", "because")
    builder.add_str("bk", "back")
    builder.add_str("bl", "black")
    builder.add_str("bh", "behind")
    builder.add_str("bo", "before")
    builder.add_str("tk", "think")
    builder.add_str("mk", "make")
    builder.add_str("en", "then")
    builder.add_str("sm", "some")
    builder.add_str("sg", "something")
    builder.add_str("bn", "been")
    builder.add_str("ej", "end")
    builder.add_str("ev", "even")
    builder.add_str("wy", "way")
    builder.add_str("hm", "him")
    builder.add_str("cu", "could")
    builder.add_str("dy", "day")
    builder.add_str("hs", "has")
    builder.add_str("oj", "other")
    builder.add_str("aj", "another")
    builder.add_str("ys", "yes")
    builder.add_str("ye", "you're")
    builder.add_str("yv", "you've")
    builder.add_str("di", "did")
    builder.add_str("wht", "with")
    builder.add_str("wnt", "want")
    builder.add_str("ghs", "things")
    builder.add_str("wor", "word")
    builder.add_str("wrl", "world")
    builder.add_str("wul", "would")
    builder.add_str("frm", "from")
    builder.add_str("dif", "different")
    return builder


def example_config_path() -> str:
    return str(_root_dir()/"example_config.toml")


def python_path() -> str:
    return str(_root_dir()/"config.py")


def make_python(builder: Builder) -> str:
    return build_python(builder)


def make_toml(builder: Builder) -> str:
    return build_toml(builder)


def _root_dir():
    return Path(__file__).resolve().parent.parent
