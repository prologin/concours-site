import rules


@rules.predicate
def can_view_forum(user, forum):
    # Temporary hack before we have an actual way of setting per-forum permissions
    return not forum.name.startswith('[STAFF]')


@rules.predicate
def can_view_thread(user, thread):
    return can_view_forum(user, thread.forum)


@rules.predicate
def can_view_post(user, post):
    return can_view_thread(user, post.thread)


@rules.predicate
def is_resource_author(user, obj):
    return user == obj.author


@rules.predicate
def is_thread_resource_author(user, obj):
    return is_resource_author(user, obj.first_post)


@rules.predicate
def is_thread_open(user, thread):
    return thread.is_open


@rules.predicate
def is_post_visible(user, post):
    return post.is_visible


# Permissions
rules.add_perm('forum.view_forum', rules.is_staff | can_view_forum)
rules.add_perm('forum.create_thread', rules.is_staff | can_view_forum)
rules.add_perm('forum.view_thread', rules.is_staff | can_view_thread)
rules.add_perm('forum.edit_thread', rules.is_staff | (can_view_thread & is_thread_resource_author))
rules.add_perm('forum.view_post', rules.is_staff | can_view_post)
rules.add_perm('forum.create_post', rules.is_staff | (can_view_thread & is_thread_open))
rules.add_perm('forum.edit_post', rules.is_staff | (is_post_visible & can_view_post & is_resource_author))
rules.add_perm('forum.edit_post_visibility', rules.is_staff)
