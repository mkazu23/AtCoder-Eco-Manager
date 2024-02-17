N = int(input())
A_N = [int(x) for x in input().split()]
cnt = 0
flg = 1

while True:
  for ele in A_N:
    if ele % 2 != 0:
      flg = 0
  if flg == 0:
    break
  A_N = [a // 2 for a in A_N]
  cnt += 1

print(cnt)