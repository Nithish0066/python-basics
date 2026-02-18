# Step 1: Ask user to enter a full sentence
sentence = input("Enter a full sentence: ")

# Step 2: Ask user for a specific word
search_word = input("Enter the word to count: ")

# Step 3: Convert sentence into words
words = sentence.split()

count = 0

# Step 4: Count the word
for word in words:
    if word.lower() == search_word.lower():
        count += 1

# Step 5: Print result
print("The word appears", count, "times in the sentence.")
