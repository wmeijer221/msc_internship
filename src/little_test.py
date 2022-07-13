some_data = [1, 2, 3, 4, 5, 6, 7, 8]

data_iter = iter(some_data)


for element in data_iter:
    print(element)

other_iter = iter(some_data)

for element in other_iter:
    print(element)
    next(other_iter)
