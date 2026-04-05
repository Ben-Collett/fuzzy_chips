from expansion_utils import expand_snake_and_upper_snake_case, expand_new
from config import Config
from casing import Casing, determine_code_casing

config = Config()
# print(expand_snake_and_upper_snake_case(
#     "hello", "_there", Casing.SNAKE, ))
# print(determine_code_casing("THIS_tg", ""))
# print(determine_code_casing("Config.this_is", ""))
# print(determine_code_casing("def hello_there", "(s:Str):"))
# left_part = "expandhi"
# new_parts = [False, False, False, False, False, False, True, True]
# white_space = " "
# right_part = "_new"
# print(expand_new(left_part, new_parts, white_space, right_part, config))

# left_part = "expan_dhi"
# new_parts = [False, False, False, False, False, False, False, True, True]
# white_space = " "
# right_part = "("
# print(expand_new(
#     left_part, new_parts, white_space, right_part, config))

# left_part = "HIex"
# new_parts = [False, False,  True, True]
# white_space = " "
# right_part = "PAN_DOD"
# print(expand_new(
#     left_part, new_parts, white_space, right_part, config))
