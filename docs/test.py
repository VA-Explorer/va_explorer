import os

from pathlib import Path

# p = os.path.dirname(os.path.abspath(__file__))

p = Path(__file__).absolute().parent.parent

print(p)

