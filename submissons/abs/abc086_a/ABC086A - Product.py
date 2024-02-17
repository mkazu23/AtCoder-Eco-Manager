a, b = map(int, input().split())
product = a * b
print("Odd" if product % 2 == 1 else "Even")