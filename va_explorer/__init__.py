import asgiref

from . import monkey_patches

__version__ = "1"
__version_info__ = tuple(
    [
        int(num) if num.isdigit() else num
        for num in __version__.replace("-", ".", 1).split(".")
    ]
)

# Monkey Patches
asgiref.sync.sync_to_async = monkey_patches.patch_sync_to_async
