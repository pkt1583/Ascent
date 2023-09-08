from behave import *

from tests import environment

use_step_matcher("re")


@given("I am running in end to end mode")
def step_impl(context):
    assert environment.is_running_end_to_end == True, "Failed: Not running in end to end mode"
    assert environment.base_url_for_end_to_end != None, "Failed: please define BASE_URL_FOR_E2E in environment variable"
