A, B, C, X = map(int, open(0))
COIN_A = 500
COIN_B = 100
COIN_C = 50
cnt = 0

for a in range(A+1):
  for b in range(B+1):
    for c in range(C+1):
      total = COIN_A * a + COIN_B * b + COIN_C * c
      cnt += 1 if total == X else 0
print(cnt)