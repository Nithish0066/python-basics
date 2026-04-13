
def person_lister(func):
    def inner(people):
        people.sort(key=lambda x: int(x[2]))
        return [func(person) for person in people]
    return inner


@person_lister
def name_format(person):
    title = "Mr." if person[3] == "M" else "Ms."
    return f"{title} {person[0]} {person[1]}"

people = []

n = int(input("Enter number of people: "))

for _ in range(n):
    data = input("Enter FirstName LastName Age Gender: ")
    people.append(data.split())

result = name_format(people)

print("\nSorted Directory:")
for name in result:
    print(name)
