"""A separator fixes simple aliases but collides with punctuation in IDs."""


def compose(namespace, token):
    return namespace + ":" + token
