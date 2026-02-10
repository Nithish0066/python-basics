#  program to remove the voweles a,e,i,o and u

s = input ("Enter the string :")
voweles = ('a','e','i','o','u', 'A','E','I','O','U')
result = ""
for char in s:
    if char not in voweles:
        result += char
    else:
        continue
print ("String after removing the voweles : ", result)