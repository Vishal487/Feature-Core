class DuplicateFeatureNameException(Exception):
    # raised when feature name already exists in db
    pass


class SelfParentException(Exception):
    # raised when feature tries to be its own parent
    pass


class FeatureNotFoundException(Exception):
    # raised when feature not found in db
    pass


class NestedChildException(Exception):
    # raised when there is chance of being grand child/parent relationship
    pass


class DBIntegrityError(Exception):
    # raised when we get IntegrityError exception from database
    pass


class NameLengthLimitException(Exception):
    # raised when name length is not within limit
    pass


class DeletingParentFeature(Exception):
    # raised when deleting a parent feature
    pass
