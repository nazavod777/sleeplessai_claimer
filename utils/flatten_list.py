def flatten_list(nested_list: list) -> list:
    result = []

    def flatten(lst):
        for item in lst:
            if isinstance(item, list):
                flatten(item)

            else:
                result.append(item)

    flatten(nested_list)

    return result
