from django import template

register = template.Library()


@register.filter(name="concat")
def concat_str(str_1, str_2) -> str:
    if isinstance(str_1, str) and isinstance(str_2, str):
        return str_1 + str_2
    print(str_1, str_2)
    raise ValueError("arguments must be str")

# order matters when chaining template filters
@register.filter(name="permit")
def check_permission(permission, user):
    if isinstance(permission, str):
        return user.has_perm(permission)
    raise ValueError("permission argument must be str")

# use this syntax for functions in templates like {% func_name arg1 arg 2 arg3 %}
# instead of filter that generates functions like value|function:arguments
@register.simple_tag(name="list-join")
def link_list(*args):
    returned_value = []
    for item in args:
        if isinstance(item, list):
            returned_value += item
        else:
            raise ValueError("all arguments must be in form of a list")
    return returned_value