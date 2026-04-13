input_by_user=input('Enter a sentence with number representing their position:')
number_strings=['0','1','2','3','4','5','6','7','8','9']
sentence=input_by_user.split()
sorted_sentence={}
new_sentence=[]
print(sentence)
for word in sentence:
    for character in word:
        for string in number_strings:
            if string == character:
                sorted_sentence[int(string)]=word
for key,value in sorted_sentence.items():
    new_sentence.insert(key,value)
#Dictionary to store the key as index(number reprasenting their location) and words as values
print(sorted_sentence)
print(new_sentence)
#An empty string which concatenate the words
string_sentence=''
#print(new_sentence.po)
for sorted_words in new_sentence:
    for letter in sorted_words:
        if letter in number_strings:
            pass
        else:
            string_sentence+=letter
    string_sentence+=' '
print(f'The sorted sentence is: {string_sentence}')