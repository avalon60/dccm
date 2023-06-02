import sys
k = 0
try:
   for line in sys.stdin:
      k = k + 1
      print(line)
except KeyboardInterrupt:
   sys.stdout.flush()
