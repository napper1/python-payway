from payway.exceptions import PaywayError


def json_list(name):
    def decorator(function):
        def wrapper(*args, **kwargs):
            result = function(*args, **kwargs)
            if result.status_code in [422, 404]:
                return result.json()
            if result.status_code not in [200, 204]:
                raise PaywayError(result.status_code, result.text)
            if result.status_code == 204:
                # DELETE methods successful response
                return result
            return result.json()
        return wrapper
    return decorator
