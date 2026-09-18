def list_live_services(index_page):
    """Services publiés, enfants directs de la page d'index, dans l'ordre de l'arbre Wagtail."""
    return index_page.get_children().live().specific()
