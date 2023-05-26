# Define the size of the pattern
size = 5

# Generate the pattern
for i in range(size):
    for j in range(i + 1):
        print("*", end="")
    print()
