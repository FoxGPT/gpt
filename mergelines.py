with open("keys.txt", "r") as f1:
    lines_f1 = f1.readlines()

with open("gpt4.txt", "r") as f2:
    lines_f2 = f2.readlines()

with open("keys.txt", "w") as f1:
    for line in lines_f1:
        if line not in lines_f2:
            f1.write(line)
