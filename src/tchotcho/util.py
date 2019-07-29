from tchotcho.log import log
import botocore


def boto_exception(fn):
    """Handle boto errors"""

    def decorator(self, *args, **kwargs):
        res = None
        try:
            res = fn(self, *args, **kwargs)
        except botocore.exceptions.ClientError as ex:
            error_message = ex.response["Error"]["Message"]
            log.exception("Boto error: %s" % error_message)
        except Exception:
            log.exception(f"An error occured on: {fn.__name__}")
        return res

    return decorator


def get_wrapped_waiter(cf, name, callback):
    waiter = cf.get_waiter(name)
    orig_func = waiter._operation_method

    def wrapper(**kwargs):
        response = orig_func(**kwargs)
        callback(response)
        return response

    waiter._operation_method = wrapper
    return waiter
