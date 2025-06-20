import json


print("   ".split())

string1 = "test , test , test     , test"

list1 = string1.split(",")
print(list1)
print(len(list1))

string2 = ",".join(list1)
print(string2)

list1 = [x.strip() for x in string1.split(",")]
print(list1)
print(len(list1))

string2 = ",".join(list1)
print(string2)
existing_dirs = None
existing_dirs = [x.strip() for x in existing_dirs.split(",")]