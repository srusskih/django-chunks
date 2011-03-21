from django import template
from django.db import models
from django.core.cache import cache

register = template.Library()

Chunk = models.get_model('chunks', 'chunk')
CACHE_PREFIX = "chunk_"

def do_get_chunk(parser, token):
    # split_contents() knows not to split quoted strings.
    tokens = token.split_contents()
    if len(tokens) < 2 or len(tokens) > 3:
        raise template.TemplateSyntaxError, "%r tag should have either 2 or 3 arguments" % (tokens[0],)
    if len(tokens) == 2:
        tag_name, key = tokens
        cache_time = 0
    if len(tokens) == 3:
        tag_name, key, cache_time = tokens

    # Check to see if the key is properly double/single quoted
    if (key[0] == key[-1] and key[0] in ('"', "'")):
        return ChunkNode(key[1:-1], cache_time)

    key = parser.compile_filter(key)
    return ChunkNode(key, cache_time)

class ChunkNode(template.Node):
    def __init__(self, key, cache_time=0):
       self.key = key
       self.cache_time = cache_time
    
    def render(self, context):
        if not isinstance(self.key, unicode):
            key = self.key.resolve(context)
        else:
            key = self.key

        cache_key = CACHE_PREFIX + key
        c = cache.get(cache_key)

        if c is None:
            c, created = Chunk.objects.\
                get_or_create(key=key, defaults={'content': key})
            cache.set(cache_key, c, int(self.cache_time))

        content = c.content
        return content
        
register.tag('chunk', do_get_chunk)
