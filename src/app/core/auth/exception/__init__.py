class AccessTokenMissingException(Exception):
    def __init__(self, message, **kwargs):
        super().__init__(message)


class IdTokenMissingException(Exception):
    def __init__(self, message, **kwargs):
        super().__init__(message)


class UnAuthorizedException(Exception):
    def __init__(self, message, **kwargs):
        super().__init__(message)
        self.user_roles = kwargs.pop('user_roles', None)
        self.message = message
        self.expected_roles = kwargs.pop('expected_roles', None)
