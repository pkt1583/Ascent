import re
import time
from logging import getLogger
from typing import List, Any, Callable

from fastapi import HTTPException, status

from app.utils.constants import NAME_VALIDATION_PATTERN

log = getLogger(__name__)


def create_filter_condition(query_params):
    """Create a filter condition from query parameters
    Input: query_params: dict
    Returns: dict
    """

    log.info(f"Creating filter condition from query parameters {query_params}")

    filter_dict = {}

    if query_params is None:
        return filter_dict

    for param in query_params.split("&"):
        # Split the parameter by "=" to get the key and value

        if '=' not in param:
            raise HTTPException(status_code=422, detail='Query string is not valid.')

        key, value = param.split("=")

        # Add the key-value pair to the filter condition
        values = value.split(",")
        if len(values) > 1:
            filter_dict[key] = {"$in": values}
        else:
            filter_dict[key] = value

    log.debug(
        f"Created filter condition from query parameters {query_params} :  {filter_dict}"
    )
    return filter_dict


def dict_to_query_string(params, parent_key=None):
    """Convert a dictionary to a query string
    Returns:
        str: Query String
    """
    log.info(
        f"Converting dictionary to query string: {params} and parent_key: {parent_key}"
    )
    query_string_parts = []
    if len(params) == 0:
        return ""
    # Loop through the dictionary items
    for key, value in params.items():
        # Check if the value is a list or tuple, and convert it to a comma-separated string
        if isinstance(value, (list, tuple)):
            value = ",".join(value)
        # Convert the key-value pair to a query string part in the format "key=value"
        query_string_part = ""
        if parent_key:
            query_string_part = f"{parent_key}.{key}={value}"
        else:
            query_string_part = f"{key}={value}"
        # Add the query string part to the list of query string parts
        query_string_parts.append(query_string_part)

    # Join the query string parts with "&" to create the final query string
    query_string = "&".join(query_string_parts)

    log.debug(
        f"Converted dictionary to query string: {query_string} and parent_key: {parent_key}"
    )

    return query_string


def find_delta_items(items1: List[Any], items2: List[Any], key: Callable[[Any], Any]) -> List[Any]:
    """
    Finds the delta between two lists of items.

    Args:
        items1: A list of items.
        items2: Another list of items.
        key: A function that takes an item and returns its unique identifier.


    Returns:
        A list of items that are in items1 but not in items2, or that are in items2 but have different attribute values than the corresponding instance in items1.
    """
    delta_items = list(filter(lambda x: key(x) not in {key(item) for item in items2}, items1))
    return delta_items


def validate_name(name: str):
    if not re.match(NAME_VALIDATION_PATTERN, name):
        raise ValueError("Invalid name. Only lowercase letters, numbers and hyphens are allowed.")
    return name


def init_common_model_attributes(object, user):
    if getattr(object, "metadata", None) is not None:
        metadata = object.metadata
        if metadata is not None:
            metadata["name"] = object.name  # should i respect what user provided or overwrite
            metadata["id"] = object.id
    created_by = getattr(object, "created_by", None)
    if created_by is None:
        object.created_by = user.name
    object.updated_by = user.name
    object.updated_on = int(time.time_ns())
    return object


async def popualate_env_cache(env: List[str] = None):
    global env_cache
    env_cache.update(env)


env_cache = set()
