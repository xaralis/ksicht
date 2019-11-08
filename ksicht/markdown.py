from markdown_deux.templatetags.markdown_deux_tags import markdown_filter


def markdownify(content):
    return markdown_filter(content)
